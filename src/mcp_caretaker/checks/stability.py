"""Canonical tool-list comparison for the two stability checks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .. import canary
from ..model import CheckResult, Evidence, Verdict
from . import CHECK_BY_ID

COMPARE_FIELDS = (
    "title",
    "description",
    "inputSchema",
    "outputSchema",
    "annotations",
)
_ABSENT = "<absent>"


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def _canonical_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {field: tool[field] for field in COMPARE_FIELDS if field in tool}


def _by_name(tools: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(tool.get("name")): _canonical_tool(tool)
        for tool in tools
        if isinstance(tool, dict)
    }


def compare_lists(
    first: list[dict[str, Any]],
    second: list[dict[str, Any]],
    redaction: Mapping[str, str],
) -> tuple[Verdict, str, tuple[Evidence, ...]]:
    """Match by name, ignore order and top-level _meta or icons; changed wins."""
    left = _by_name(first)
    right = _by_name(second)
    replay = canary.tools_list_replay(redaction)
    evidence: list[Evidence] = []
    changed = False
    added_or_removed = False
    for name in sorted(set(left) | set(right)):
        before = left.get(name)
        after = right.get(name)
        if before is None:
            added_or_removed = True
            detail = f"tool: before {_ABSENT} after {canary.excerpt(_canonical(after), redaction)}"
            evidence.append(Evidence(name, detail, replay))
            continue
        if after is None:
            added_or_removed = True
            detail = f"tool: before {canary.excerpt(_canonical(before), redaction)} after {_ABSENT}"
            evidence.append(Evidence(name, detail, replay))
            continue
        for field in COMPARE_FIELDS:
            former = before.get(field, _ABSENT)
            latter = after.get(field, _ABSENT)
            if _canonical(former) == _canonical(latter):
                continue
            changed = True
            detail = (
                f"{field}: before {canary.excerpt(_canonical(former), redaction)} "
                f"after {canary.excerpt(_canonical(latter), redaction)}"
            )
            evidence.append(Evidence(name, detail, replay))
    if changed:
        verdict = Verdict.FAIL
        summary = f"{len(evidence)} changes in common tool fields."
    elif added_or_removed:
        verdict = Verdict.WARN
        summary = f"{len(evidence)} tools added or removed."
    else:
        verdict = Verdict.PASS
        summary = f"{len(left)} common tools unchanged."
    return verdict, summary, tuple(evidence)


def build_result(
    check_id: str,
    verdict: Verdict,
    summary: str,
    evidence: tuple[Evidence, ...] = (),
    reason: str | None = None,
) -> CheckResult:
    """Build one registered stability result."""
    return CheckResult(
        check_id=check_id,
        title=CHECK_BY_ID[check_id].title,
        verdict=verdict,
        summary=summary,
        evidence=evidence,
        reason=reason,
    )
