"""Fresh fake values, bounded scan hooks, and redaction for PR 4 checks."""

from __future__ import annotations

import base64
import json
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from mcp.shared.exceptions import MCPError

from . import thresholds
from .checks import CANARY_IDS, CHECK_BY_ID
from .launch import LaunchSpec, redact_values
from .model import CheckResult, Evidence, Verdict, visible_text

CANARY_NAMES = (
    "CARETAKER_CANARY_API_KEY",
    "CARETAKER_CANARY_TOKEN",
    "CARETAKER_CANARY_SECRET",
)
_TRUNCATED = "...[truncated]"


def make_canary() -> dict[str, str]:
    """Return three fresh fake values, one for each planted variable name."""
    return {name: "ct_canary_" + secrets.token_hex(16) for name in CANARY_NAMES}


def base64_form(value: str) -> str:
    """Return the one standard base64 encoding of the ASCII value alone."""
    return base64.b64encode(value.encode("ascii")).decode("ascii")


def _argv_env_values(argv: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for item in argv:
        if item.startswith("--env="):
            values.append(item.split("=", 1)[1])
    for index, item in enumerate(argv[:-1]):
        if item == "--env":
            values.append(argv[index + 1])
    for value in tuple(values):
        if "=" in value:
            values.append(value.split("=", 1)[1])
    return values


def build_redaction_map(
    spec: LaunchSpec, canary_values: Mapping[str, str]
) -> dict[str, str]:
    """Include caller values, canary values, base64 forms, and --env values."""
    redaction = dict(spec.extra_env)
    for name, value in canary_values.items():
        redaction[name] = value
        redaction[f"{name}_BASE64"] = base64_form(value)
    for index, value in enumerate(_argv_env_values(spec.argv), 1):
        if value:
            redaction[f"ARGV_ENV_{index}"] = value
    return redaction


def excerpt(text: str, redaction: Mapping[str, str], cap: int | None = None) -> str:
    """Redact the full text first, then escape and cap the visible excerpt."""
    limit = thresholds.EVIDENCE_MAX_CHARS if cap is None else cap
    cleaned = visible_text(redact_values(text, redaction))
    if len(cleaned) > limit:
        cleaned = cleaned[: max(0, limit - len(_TRUNCATED))] + _TRUNCATED
    return cleaned


def tools_list_replay(redaction: Mapping[str, str]) -> str:
    """Construct one capped tools/list line; it needs an initialize handshake."""
    line = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return excerpt(line, redaction, thresholds.REPLAY_MAX_CHARS)


def error_evidence(
    subject: str, error: BaseException | str, redaction: Mapping[str, str]
) -> Evidence:
    """Keep an exact, redacted, capped first-line error with any stderr tail."""
    if isinstance(error, BaseException):
        lines = str(error).splitlines()
        text = f"{type(error).__name__}: {lines[0] if lines else ''}"
        tail = getattr(error, "stderr_tail", "")
        if isinstance(tail, str) and tail:
            text += " | " + tail
    else:
        text = error
    return Evidence(subject, excerpt(text, redaction))


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def answer_text(answer: Any) -> str:
    """Serialize a whole tool result or MCPError fields before scanning."""
    if isinstance(answer, MCPError):
        payload: Any = {
            "code": answer.code,
            "message": answer.message,
            "data": answer.data,
        }
    else:
        dump = getattr(answer, "model_dump", None)
        if callable(dump):
            payload = dump(by_alias=True, exclude_unset=True)
        else:
            payload = {
                "content": getattr(answer, "content", None),
                "structuredContent": getattr(answer, "structured_content", None),
                "isError": getattr(answer, "is_error", None),
            }
    return _json_text(payload)


@dataclass(repr=False)
class CanaryTracker:
    """Keep only counts, findings, and scan sizes; never keep all answers."""

    values: Mapping[str, str]
    redaction: Mapping[str, str]
    answer_count: int = 0
    answer_findings: list[Evidence] = field(default_factory=list)
    handshake_findings: list[Evidence] = field(default_factory=list)
    output_findings: list[Evidence] = field(default_factory=list)
    handshake_available: bool = False
    tools_list_available: bool = False
    page_count: int = 0
    stdout_lines_scanned: int = 0
    stderr_bytes_scanned: int = 0
    stderr_cap_hit: bool = False
    stderr_after_close: bool = True

    def _forms(self) -> list[tuple[str, str, str]]:
        forms: list[tuple[str, str, str]] = []
        for name in CANARY_NAMES:
            value = self.values[name]
            forms.append((name, "exact", value))
            forms.append((name, "base64", base64_form(value)))
        return forms

    def _record(
        self,
        text: str,
        subject: str,
        replay: str | None,
        findings: list[Evidence],
    ) -> None:
        for name, encoding, needle in self._forms():
            if needle and needle in text:
                detail = f"{name} {encoding} | {excerpt(text, self.redaction)}"
                findings.append(Evidence(subject, detail, replay))

    def observe_answer(self, outcome: str, answer: Any, replay: str) -> None:
        if outcome not in ("success", "error_result", "jsonrpc_error"):
            return
        self.answer_count += 1
        self._record(
            answer_text(answer), "tools/call answer", replay, self.answer_findings
        )

    def observe_first_connection(
        self,
        raw_initialize: dict[str, Any] | None,
        pages: list[dict[str, Any]],
        tools_error: str | None,
    ) -> None:
        self.handshake_available = isinstance(raw_initialize, dict)
        self.tools_list_available = tools_error is None
        self.page_count = len(pages)
        if not self.handshake_available or not self.tools_list_available:
            return
        info = raw_initialize.get("serverInfo") if raw_initialize else {}
        selected = {
            key: info[key]
            for key in ("name", "version", "instructions")
            if isinstance(info, dict) and key in info
        }
        handshake = {
            "serverInfo": selected,
            "instructions": raw_initialize.get("instructions"),
        }
        replay = tools_list_replay(self.redaction)
        self._record(
            _json_text(handshake),
            "initialize serverInfo",
            replay,
            self.handshake_findings,
        )
        for index, page in enumerate(pages, 1):
            self._record(
                _json_text(page),
                f"tools/list page {index}",
                replay,
                self.handshake_findings,
            )

    def observe_stdout(self, line: str) -> None:
        self.stdout_lines_scanned += 1
        self._record(line, "stdout", None, self.output_findings)

    def observe_stderr(
        self, text: str, bytes_scanned: int, cap_hit: bool, after_close: bool
    ) -> None:
        self.stderr_bytes_scanned += bytes_scanned
        self.stderr_cap_hit = self.stderr_cap_hit or cap_hit
        self.stderr_after_close = self.stderr_after_close and after_close
        self._record(text, "stderr", None, self.output_findings)


def observe_session_stderr(
    tracker: CanaryTracker,
    before: tuple[str, int, bool] | None,
    after: tuple[str, int, bool] | None,
    cached_text: str,
) -> None:
    """Prefer the after-close prefix; document the before-shutdown fallback."""
    prefix = after if after is not None else before
    if prefix is not None:
        tracker.observe_stderr(*prefix, after_close=after is not None)
        return
    data = cached_text.encode("utf-8")
    tracker.observe_stderr(cached_text, len(data), False, False)


def _result(
    check_id: str,
    verdict: Verdict,
    summary: str,
    evidence: tuple[Evidence, ...] = (),
    reason: str | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        title=CHECK_BY_ID[check_id].title,
        verdict=verdict,
        summary=summary,
        evidence=evidence,
        reason=reason,
    )


def build_answer_result(
    tracker: CanaryTracker, earlier_failure_reason: str | None
) -> CheckResult:
    findings = tuple(tracker.answer_findings)
    if findings:
        return _result(
            CANARY_IDS[0],
            Verdict.FAIL,
            f"{len(findings)} findings in {tracker.answer_count} tools/call answers scanned.",
            findings,
        )
    if earlier_failure_reason is not None or tracker.answer_count == 0:
        return _result(
            CANARY_IDS[0],
            Verdict.NOT_TESTED,
            "Check was not tested.",
            reason=earlier_failure_reason or "no tools/call answers were scanned",
        )
    return _result(
        CANARY_IDS[0],
        Verdict.PASS,
        f"{tracker.answer_count} tools/call answers scanned; no findings.",
    )


def build_first_connection_result(tracker: CanaryTracker) -> CheckResult:
    if not tracker.handshake_available or not tracker.tools_list_available:
        return _result(
            CANARY_IDS[1],
            Verdict.NOT_TESTED,
            "Check was not tested.",
            reason="handshake or tools/list failed",
        )
    findings = tuple(tracker.handshake_findings)
    if findings:
        return _result(
            CANARY_IDS[1],
            Verdict.FAIL,
            f"{len(findings)} findings in handshake or first tools/list pages.",
            findings,
        )
    return _result(
        CANARY_IDS[1],
        Verdict.PASS,
        f"handshake and {tracker.page_count} tools/list pages scanned; no findings.",
    )


def build_output_result(tracker: CanaryTracker) -> CheckResult:
    findings = tuple(tracker.output_findings)
    if findings:
        verdict = Verdict.WARN
        summary = f"{len(findings)} findings in stderr or stdout output."
    else:
        verdict = Verdict.PASS
        summary = (
            f"{tracker.stderr_bytes_scanned} stderr bytes scanned and "
            f"{tracker.stdout_lines_scanned} stdout lines scanned; no findings."
        )
    if tracker.stderr_cap_hit:
        summary += " stderr cap reached."
    if not tracker.stderr_after_close:
        summary += " used before-shutdown stderr prefix."
    return _result(CANARY_IDS[2], verdict, summary, findings)
