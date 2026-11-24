"""Fixed-order robustness probes over raw tools/list dicts.

Only ``tools/call`` and ``tools/list`` are sent. Generated valid input and the
large string are sent only to tools whose raw ``readOnlyHint`` is exactly JSON
true. All other tools receive invalid input only.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import anyio
from mcp.shared.exceptions import MCPError
from mcp_types import CONNECTION_CLOSED

from .. import thresholds
from ..errors import CallTimeout, ServerExited
from ..launch import redact_values
from ..model import CheckResult, Evidence, Verdict, visible_text
from ..session import ServerSession, _error_text, _exception_has_type
from . import CHECK_BY_ID, CHECKS

ROBUSTNESS_IDS = tuple(item.id for item in CHECKS if item.group == "robustness")
UNKNOWN_TOOL_NAME = "caretaker_no_such_tool"
BANNED_SCHEMA_KEYS = frozenset(
    {
        "pattern",
        "format",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minItems",
        "maxItems",
        "anyOf",
        "oneOf",
        "allOf",
        "$ref",
        "not",
        "if",
    }
)
TYPE_DEFAULTS: dict[str, Any] = {
    "string": "A",
    "integer": 1,
    "number": 1.0,
    "boolean": True,
    "null": None,
}
WRONG_VALUES: dict[str, Any] = {
    "string": {"caretaker_wrong_type": True},
    "integer": "not-a-number",
    "number": "not-a-number",
    "boolean": "not-a-bool",
    "array": "not-an-array",
    "object": "not-an-object",
    "null": "not-a-null",
}
FAILING_OUTCOMES = {
    "CT-ROB-001": frozenset({"success", "no_answer", "exited"}),
    "CT-ROB-002": frozenset({"success", "no_answer", "exited"}),
    "CT-ROB-003": frozenset({"success", "no_answer", "exited"}),
    "CT-ROB-004": frozenset({"no_answer", "exited"}),
    "CT-ROB-005": frozenset({"error_result", "jsonrpc_error", "no_answer", "exited"}),
    "CT-ROB-006": frozenset(),
}


@dataclass(frozen=True)
class ProbePlan:
    check_id: str
    kind: str
    tool_name: str
    tool_index: int
    arguments: dict[str, Any] | None = None
    huge_property: str | None = None
    skipped_reason: str | None = None


@dataclass(frozen=True)
class ProbeRecord:
    check_id: str
    outcome: str
    evidence: tuple[Evidence, ...]
    skip_reason: str | None = None


def is_read_only(tool: Mapping[str, Any]) -> bool:
    """Require the raw wire key ``annotations.readOnlyHint`` to be exactly true."""
    annotations = tool.get("annotations")
    return isinstance(annotations, Mapping) and annotations.get("readOnlyHint") is True


def wrong_value(declared_type: Any) -> Any:
    """Return a JSON value that does not match one declared type."""
    if declared_type == "string":
        return {"caretaker_wrong_type": True}
    return WRONG_VALUES.get(str(declared_type), "not-a-type")


def _has_banned_keys(schema: Mapping[str, Any]) -> bool:
    return any(key in schema for key in BANNED_SCHEMA_KEYS)


def _required(schema: Mapping[str, Any]) -> list[str] | None:
    required = schema.get("required", [])
    if not isinstance(required, list) or not required:
        return None
    if any(not isinstance(name, str) for name in required):
        return None
    return required


def make_valid_arguments(schema: Any) -> dict[str, Any] | None:
    """Generate only required top-level properties, or refuse the schema."""
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        return None
    if _has_banned_keys(schema):
        return None
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return None
    required = schema.get("required", [])
    if not isinstance(required, list) or any(
        not isinstance(name, str) for name in required
    ):
        return None
    for prop in properties.values():
        if not isinstance(prop, Mapping) or _has_banned_keys(prop):
            return None
        declared = prop.get("type")
        if not isinstance(declared, str) or declared not in TYPE_DEFAULTS:
            return None
    arguments: dict[str, Any] = {}
    for name in required:
        prop = properties.get(name)
        if not isinstance(prop, Mapping):
            return None
        declared = prop.get("type")
        if not isinstance(declared, str) or declared not in TYPE_DEFAULTS:
            return None
        if "const" in prop:
            value = prop["const"]
        elif "default" in prop:
            value = prop["default"]
        elif "enum" in prop:
            enum = prop["enum"]
            if not isinstance(enum, list) or not enum:
                return None
            value = enum[0]
        else:
            value = TYPE_DEFAULTS[declared]
        arguments[name] = value
    return arguments


def _wrong_arguments(schema: Any) -> dict[str, Any] | None:
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        return None
    properties = schema.get("properties")
    required = _required(schema)
    if not isinstance(properties, Mapping) or required is None:
        return None
    arguments: dict[str, Any] = {}
    for name in required:
        prop = properties.get(name)
        if not isinstance(prop, Mapping):
            return None
        arguments[name] = wrong_value(prop.get("type"))
    return arguments


def _huge_arguments(schema: Any) -> tuple[dict[str, Any], str] | None:
    valid = make_valid_arguments(schema)
    if valid is None:
        return None
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return None
    for name in valid:
        prop = properties.get(name)
        if isinstance(prop, Mapping) and prop.get("type") == "string":
            huge = dict(valid)
            huge[name] = "A" * thresholds.HUGE_STRING_LENGTH
            return huge, name
    return None


def _arg_summary(
    arguments: Mapping[str, Any], huge_property: str | None
) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in arguments.items():
        length = len(value) if isinstance(value, (str, list, dict)) else None
        summary[key] = {"type": type(value).__name__, "length": length}
    if huge_property is not None:
        summary[huge_property] = (
            f"<{huge_property}: string of {thresholds.HUGE_STRING_LENGTH} characters>"
        )
    return summary


def replay_line(
    name: str,
    arguments: Mapping[str, Any],
    extra_env: Mapping[str, str],
    huge_property: str | None = None,
) -> str:
    """Construct one capped JSON-RPC tools/call line; never use captured wire bytes."""
    display = dict(arguments)
    if huge_property is not None:
        display[huge_property] = f"<{thresholds.HUGE_STRING_LENGTH} x 'A'>"
    line = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": display},
        },
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    line = visible_text(redact_values(line, extra_env))
    if len(line) > thresholds.REPLAY_MAX_CHARS:
        line = line[: thresholds.REPLAY_MAX_CHARS] + "...[truncated]"
    return line


def _answer_detail(answer: Any) -> dict[str, Any]:
    if answer is None:
        return {}
    if isinstance(answer, BaseException):
        return {"error": _error_text(answer)}
    text = "".join(
        str(getattr(block, "text", "")) for block in getattr(answer, "content", [])
    )[:120]
    return {"is_error": bool(getattr(answer, "is_error", False)), "text": text}


def _compact(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False, default=str)


def _probe_record(
    plan: ProbePlan,
    outcome: str,
    answer: Any,
    extra_env: Mapping[str, str],
) -> ProbeRecord:
    subject = (
        f"probe {plan.check_id} tool[{plan.tool_index}] {plan.tool_name} {plan.kind}"
    )
    detail = _compact(
        {
            "tool": plan.tool_name,
            "phase": plan.kind,
            "args": _arg_summary(plan.arguments or {}, plan.huge_property),
            "outcome": outcome,
            "answer": _answer_detail(answer),
        }
    )
    evidence = [Evidence(subject, detail)]
    if outcome in FAILING_OUTCOMES.get(plan.check_id, frozenset()):
        replay = replay_line(
            plan.tool_name, plan.arguments or {}, extra_env, plan.huge_property
        )
        evidence.append(
            Evidence(
                f"replay {plan.check_id} tool[{plan.tool_index}] {plan.tool_name}",
                "constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first",
                replay=replay,
            )
        )
    return ProbeRecord(plan.check_id, outcome, tuple(evidence))


def _skip_record(plan: ProbePlan, reason: str) -> ProbeRecord:
    detail = _compact(
        {
            "tool": plan.tool_name,
            "phase": plan.kind,
            "outcome": "skipped",
            "reason": reason,
        }
    )
    subject = (
        f"probe {plan.check_id} tool[{plan.tool_index}] {plan.tool_name} {plan.kind}"
    )
    return ProbeRecord(
        plan.check_id,
        "skipped",
        (Evidence(subject, detail),),
        skip_reason=reason,
    )


def plan_probes(tools: list[dict[str, Any]]) -> list[ProbePlan]:
    """Build fixed-order plans; skipped plans are still counted in coverage."""
    plans: list[ProbePlan] = []
    valid: list[tuple[int, str, dict[str, Any], Any]] = []
    skipped: list[tuple[int, str, dict[str, Any] | None, str]] = []
    seen: set[str] = set()
    for index, tool in enumerate(tools):
        name = tool.get("name")
        schema = tool.get("inputSchema")
        if not isinstance(name, str) or not isinstance(schema, Mapping):
            skipped.append(
                (index, str(name), tool, "tool has no valid name or object inputSchema")
            )
            continue
        if name in seen:
            skipped.append((index, name, tool, "duplicate tool name"))
            continue
        seen.add(name)
        if len(valid) >= thresholds.MAX_TOOLS_PROBED:
            skipped.append((index, name, tool, "tool cap reached"))
            continue
        valid.append((index, name, tool, schema))

    for index, name, _, schema in valid:
        arguments = _wrong_arguments(schema)
        if arguments is None:
            plans.append(
                ProbePlan(
                    "CT-ROB-001",
                    "wrong_type",
                    name,
                    index,
                    skipped_reason="no required property was available for wrong-type input",
                )
            )
        else:
            plans.append(ProbePlan("CT-ROB-001", "wrong_type", name, index, arguments))
    for index, name, _, schema in valid:
        if _required(schema) is None:
            plans.append(
                ProbePlan(
                    "CT-ROB-002",
                    "missing_required",
                    name,
                    index,
                    skipped_reason="no required property was available for missing-required input",
                )
            )
        else:
            plans.append(ProbePlan("CT-ROB-002", "missing_required", name, index, {}))
    for index, name, tool, reason in skipped:
        plans.append(
            ProbePlan("CT-ROB-001", "wrong_type", name, index, skipped_reason=reason)
        )
        plans.append(
            ProbePlan(
                "CT-ROB-002", "missing_required", name, index, skipped_reason=reason
            )
        )
        if isinstance(tool, Mapping) and is_read_only(tool):
            plans.append(
                ProbePlan(
                    "CT-ROB-004", "huge_string", name, index, skipped_reason=reason
                )
            )
            plans.append(
                ProbePlan(
                    "CT-ROB-005", "valid_call", name, index, skipped_reason=reason
                )
            )
    if not valid and not skipped:
        plans.append(
            ProbePlan(
                "CT-ROB-001",
                "wrong_type",
                "tools/list",
                -1,
                skipped_reason="no tools to probe",
            )
        )
        plans.append(
            ProbePlan(
                "CT-ROB-002",
                "missing_required",
                "tools/list",
                -1,
                skipped_reason="no tools to probe",
            )
        )
    plans.append(ProbePlan("CT-ROB-003", "unknown_tool", UNKNOWN_TOOL_NAME, -1, {}))

    read_only = [item for item in valid if is_read_only(item[2])]
    if not read_only:
        plans.append(
            ProbePlan(
                "CT-ROB-004",
                "huge_string",
                "tools/list",
                -1,
                skipped_reason="no read-only tools were available for huge input",
            )
        )
    else:
        huge_plan = None
        for index, name, _, schema in read_only:
            huge = _huge_arguments(schema)
            if huge is not None:
                arguments, huge_property = huge
                huge_plan = ProbePlan(
                    "CT-ROB-004",
                    "huge_string",
                    name,
                    index,
                    arguments,
                    huge_property=huge_property,
                )
                break
        if huge_plan is None:
            plans.append(
                ProbePlan(
                    "CT-ROB-004",
                    "huge_string",
                    "tools/list",
                    -1,
                    skipped_reason="valid input could not be generated for a huge string",
                )
            )
        else:
            plans.append(huge_plan)
    if not read_only:
        plans.append(
            ProbePlan(
                "CT-ROB-005",
                "valid_call",
                "tools/list",
                -1,
                skipped_reason="no read-only tools were available for valid input",
            )
        )
    else:
        for index, name, _, schema in read_only:
            arguments = make_valid_arguments(schema)
            if arguments is None:
                plans.append(
                    ProbePlan(
                        "CT-ROB-005",
                        "valid_call",
                        name,
                        index,
                        skipped_reason="valid input could not be generated for this tool",
                    )
                )
            else:
                plans.append(
                    ProbePlan("CT-ROB-005", "valid_call", name, index, arguments)
                )
    plans.append(ProbePlan("CT-ROB-006", "liveness", "tools/list", -1))
    return plans


def aggregate_results(records: list[ProbeRecord]) -> dict[str, CheckResult]:
    """Use the worst recorded outcome; skipped coverage never becomes pass."""
    results: dict[str, CheckResult] = {}
    for check_id in ROBUSTNESS_IDS:
        items = [record for record in records if record.check_id == check_id]
        tested = [record for record in items if record.outcome != "skipped"]
        skipped = [record for record in items if record.outcome == "skipped"]
        outcomes = [record.outcome for record in tested]
        if check_id in ("CT-ROB-001", "CT-ROB-002", "CT-ROB-003"):
            if any(item in ("exited", "no_answer") for item in outcomes):
                verdict = Verdict.FAIL
            elif "success" in outcomes:
                verdict = Verdict.WARN
            elif skipped:
                verdict = Verdict.NOT_TESTED
            else:
                verdict = Verdict.PASS
        elif check_id == "CT-ROB-004":
            if "exited" in outcomes:
                verdict = Verdict.FAIL
            elif "no_answer" in outcomes:
                verdict = Verdict.WARN
            elif skipped:
                verdict = Verdict.NOT_TESTED
            else:
                verdict = Verdict.PASS
        elif check_id == "CT-ROB-005":
            if "exited" in outcomes:
                verdict = Verdict.FAIL
            elif any(
                item in ("no_answer", "error_result", "jsonrpc_error")
                for item in outcomes
            ):
                verdict = Verdict.WARN
            elif skipped:
                verdict = Verdict.NOT_TESTED
            else:
                verdict = Verdict.PASS
        else:
            if "fail" in outcomes:
                verdict = Verdict.FAIL
            elif skipped:
                verdict = Verdict.NOT_TESTED
            elif tested:
                verdict = Verdict.PASS
            else:
                verdict = Verdict.NOT_TESTED
        fail_count = sum(item in ("exited", "no_answer", "fail") for item in outcomes)
        warn_count = sum(
            item in ("success", "error_result", "jsonrpc_error", "no_answer")
            for item in outcomes
        )
        prefix = f"{len(tested)} tested, {len(skipped)} skipped; "
        if verdict is Verdict.FAIL:
            text = (
                f"{fail_count} probes had no answer, child exit, or liveness failure."
            )
        elif verdict is Verdict.WARN:
            text = f"{warn_count} answers differed from the expected answer."
        elif verdict is Verdict.NOT_TESTED:
            text = "at least one planned probe was skipped."
        else:
            text = "all recorded answers met the rule."
        evidence = [item for record in items for item in record.evidence]
        evidence.append(
            Evidence("coverage", f"{len(tested)} tested, {len(skipped)} skipped")
        )
        reason = (
            skipped[0].skip_reason or "no probe could run"
            if verdict is Verdict.NOT_TESTED and skipped
            else "no probe could run"
            if verdict is Verdict.NOT_TESTED
            else None
        )
        results[check_id] = CheckResult(
            check_id=check_id,
            title=CHECK_BY_ID[check_id].title,
            verdict=verdict,
            summary=prefix + text,
            evidence=tuple(evidence),
            reason=reason,
        )
    return results


def _is_cancelled(exc: BaseException) -> bool:
    return _exception_has_type(exc, anyio.get_cancelled_exc_class())


async def _call_once(session: ServerSession, plan: ProbePlan) -> tuple[str, Any]:
    try:
        answer = await session.call_tool(plan.tool_name, plan.arguments or {})
    except BaseException as exc:
        if _is_cancelled(exc):
            raise
        if isinstance(exc, ServerExited):
            return "exited", exc
        if isinstance(exc, CallTimeout):
            return "no_answer", exc
        if isinstance(exc, MCPError):
            code = exc.error.code
            return ("exited" if code == CONNECTION_CLOSED else "jsonrpc_error"), exc
        return "no_answer", exc
    if getattr(answer, "is_error", False) is True:
        return "error_result", answer
    return "success", answer


async def _liveness(session: ServerSession) -> tuple[str, Any]:
    try:
        with anyio.fail_after(session.spec.call_timeout):
            await session.list_tools()
        return "pass", None
    except BaseException as exc:
        if _is_cancelled(exc):
            raise
        return "fail", exc


def _budget_hit(started: float) -> bool:
    return time.monotonic() - started >= thresholds.PROBE_BUDGET_SECONDS


def _internal_error_results(exc: BaseException) -> dict[str, CheckResult]:
    reason = f"internal error in robustness checks: {_error_text(exc)}"
    records = [
        _skip_record(
            ProbePlan(check_id, "internal", check_id, -1, skipped_reason=reason),
            reason,
        )
        for check_id in ROBUSTNESS_IDS
    ]
    return aggregate_results(records)


async def run_robustness_checks(
    session: ServerSession,
    tools: list[dict[str, Any]],
    extra_env: Mapping[str, str],
) -> dict[str, CheckResult]:
    """Run fixed-order probes and return one result per robustness ID."""
    started = time.monotonic()
    try:
        plans = plan_probes(tools)
        records: list[ProbeRecord] = []
        for index, plan in enumerate(plans):
            if _budget_hit(started):
                records.extend(
                    _skip_record(item, "probe budget exhausted")
                    for item in plans[index:]
                )
                break
            if plan.skipped_reason is not None:
                records.append(_skip_record(plan, plan.skipped_reason))
                continue
            if plan.kind == "liveness":
                outcome, answer = await _liveness(session)
                records.append(
                    _probe_record(
                        plan, outcome, answer if outcome == "fail" else None, extra_env
                    )
                )
                continue
            outcome, answer = await _call_once(session, plan)
            records.append(_probe_record(plan, outcome, answer, extra_env))
            if outcome in ("no_answer", "exited"):
                live_outcome, live_answer = await _liveness(session)
                if live_outcome == "fail":
                    live_plan = ProbePlan("CT-ROB-006", "liveness", "tools/list", -1)
                    records.append(
                        _probe_record(live_plan, "fail", live_answer, extra_env)
                    )
                    records.extend(
                        _skip_record(item, "liveness failed")
                        for item in plans[index + 1 :]
                        if item.kind != "liveness"
                    )
                    break
        return aggregate_results(records)
    except BaseException as exc:
        if _is_cancelled(exc):
            raise
        return _internal_error_results(exc)
