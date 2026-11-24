"""Small frozen result model for checks. No score, grade, report file or CLI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from .launch import redact_values
from .thresholds import EVIDENCE_MAX_CHARS, EVIDENCE_MAX_ITEMS


class Verdict(str, Enum):
    """JSON verdict strings, exactly as specified."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_TESTED = "not_tested"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Evidence:
    subject: str
    detail: str


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    title: str
    verdict: Verdict
    summary: str
    evidence: tuple[Evidence, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class RunResult:
    caretaker_version: str
    protocol_version: str | None
    server_name: str | None
    server_version: str | None
    results: tuple[CheckResult, ...]

    def to_dict(self) -> dict[str, Any]:
        """Stable lowercase snake_case keys; ``json.dumps`` works directly."""
        return {
            "caretaker_version": self.caretaker_version,
            "protocol_version": self.protocol_version,
            "server_name": self.server_name,
            "server_version": self.server_version,
            "results": [
                {
                    "check_id": result.check_id,
                    "title": result.title,
                    "verdict": result.verdict.value,
                    "summary": result.summary,
                    "evidence": [
                        {"subject": item.subject, "detail": item.detail}
                        for item in result.evidence
                    ],
                    "reason": result.reason,
                }
                for result in self.results
            ],
        }


def visible_text(text: str) -> str:
    """Show non-printable characters as ``\\uXXXX`` (or ``\\UXXXXXXXX``) escapes."""
    out: list[str] = []
    for char in text:
        if char.isprintable():
            out.append(char)
        elif ord(char) <= 0xFFFF:
            out.append(f"\\u{ord(char):04X}")
        else:
            out.append(f"\\U{ord(char):08X}")
    return "".join(out)


def _clean_text(text: str, extra_env: Mapping[str, str]) -> str:
    text = redact_values(text, extra_env)
    text = visible_text(text)
    if len(text) > EVIDENCE_MAX_CHARS:
        text = text[:EVIDENCE_MAX_CHARS] + "...[truncated]"
    return text


def finalize_result(result: CheckResult, extra_env: Mapping[str, str]) -> CheckResult:
    """Redact, escape and cap all text in a result. Never changes the verdict."""
    evidence = list(result.evidence[:EVIDENCE_MAX_ITEMS])
    omitted = len(result.evidence) - len(evidence)
    if omitted > 0:
        evidence.append(Evidence("evidence", f"{omitted} more not shown"))
    cleaned = tuple(
        Evidence(
            subject=_clean_text(item.subject, extra_env),
            detail=_clean_text(item.detail, extra_env),
        )
        for item in evidence
    )
    return replace(
        result,
        summary=_clean_text(result.summary, extra_env),
        evidence=cleaned,
        reason=(
            _clean_text(result.reason, extra_env) if result.reason is not None else None
        ),
    )


def finalize_run_result(run: RunResult, extra_env: Mapping[str, str]) -> RunResult:
    """Apply the same text safety rules to server metadata and every result."""
    return replace(
        run,
        protocol_version=(
            _clean_text(run.protocol_version, extra_env)
            if run.protocol_version is not None
            else None
        ),
        server_name=(
            _clean_text(run.server_name, extra_env)
            if run.server_name is not None
            else None
        ),
        server_version=(
            _clean_text(run.server_version, extra_env)
            if run.server_version is not None
            else None
        ),
        results=tuple(finalize_result(item, extra_env) for item in run.results),
    )
