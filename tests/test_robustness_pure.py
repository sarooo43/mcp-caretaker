"""Pure unit tests for robustness generators, replay and aggregation."""

from __future__ import annotations

import json
from typing import Any

import pytest

from mcp_caretaker import Verdict, thresholds
from mcp_caretaker.checks import CHECK_BY_ID
from mcp_caretaker.checks.robustness import (
    BANNED_SCHEMA_KEYS,
    ROBUSTNESS_IDS,
    TYPE_DEFAULTS,
    ProbeRecord,
    aggregate_results,
    is_read_only,
    make_valid_arguments,
    replay_line,
    wrong_value,
)
from mcp_caretaker.model import Evidence


def _schema(prop: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": {"text": prop}, "required": ["text"]}


def test_make_valid_arguments_supported_types() -> None:
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "count": {"type": "integer"},
            "ratio": {"type": "number"},
            "flag": {"type": "boolean"},
            "nothing": {"type": "null"},
            "fixed": {"type": "string", "const": "fixed"},
            "fallback": {"type": "integer", "default": 7},
            "choice": {"type": "string", "enum": ["first", "second"]},
        },
        "required": [
            "text",
            "count",
            "ratio",
            "flag",
            "nothing",
            "fixed",
            "fallback",
            "choice",
        ],
    }
    arguments = make_valid_arguments(schema)
    assert arguments == {
        "text": "A",
        "count": 1,
        "ratio": 1.0,
        "flag": True,
        "nothing": None,
        "fixed": "fixed",
        "fallback": 7,
        "choice": "first",
    }
    assert json.loads(json.dumps(arguments)) == arguments


def test_make_valid_arguments_refuses_complex_schemas() -> None:
    for key in BANNED_SCHEMA_KEYS:
        prop = {"type": "string", key: "x"}
        assert make_valid_arguments(_schema(prop)) is None
    for prop in (
        {"description": "no type"},
        {"type": "array", "items": {"type": "string"}},
        {"type": "object", "properties": {}},
        {"type": ["string", "null"]},
    ):
        assert make_valid_arguments(_schema(prop)) is None
    assert make_valid_arguments({"$ref": "#/elsewhere", "type": "object"}) is None
    assert make_valid_arguments({"type": "object"}) is None


def test_wrong_value_for_each_declared_type() -> None:
    kinds: dict[str, type[Any]] = {
        "string": dict,
        "integer": str,
        "number": str,
        "boolean": str,
        "array": str,
        "object": str,
        "null": str,
    }
    for declared, kind in kinds.items():
        value = wrong_value(declared)
        assert isinstance(value, kind)
        assert json.loads(json.dumps(value)) == value
        assert value != TYPE_DEFAULTS.get(declared)


def test_read_only_detection_requires_exactly_true() -> None:
    assert is_read_only({"annotations": {"readOnlyHint": True}})
    for value in (False, "true", 1, None):
        assert not is_read_only({"annotations": {"readOnlyHint": value}})
    assert not is_read_only({"readOnlyHint": True})
    assert not is_read_only({})


def test_replay_line_is_valid_jsonrpc_and_huge_uses_placeholder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    huge = "A" * thresholds.HUGE_STRING_LENGTH
    line = replay_line("echo", {"text": huge}, {}, "text")
    parsed = json.loads(line)
    assert parsed["jsonrpc"] == "2.0"
    assert parsed["id"] == 1
    assert parsed["method"] == "tools/call"
    assert parsed["params"]["name"] == "echo"
    assert parsed["params"]["arguments"] == {
        "text": f"<{thresholds.HUGE_STRING_LENGTH} x 'A'>"
    }
    assert huge not in line
    assert "\n" not in line
    monkeypatch.setattr(thresholds, "REPLAY_MAX_CHARS", 20)
    capped = replay_line("echo", {"text": "x" * 100}, {})
    assert capped.endswith("...[truncated]")


def test_aggregation_worst_verdict_and_partial_coverage_summary() -> None:
    def record(outcome: str, reason: str | None = None) -> ProbeRecord:
        return ProbeRecord(
            "CT-ROB-001",
            outcome,
            (Evidence("probe", "detail"),),
            skip_reason=reason,
        )

    worst = aggregate_results(
        [
            record("success"),
            record("no_answer"),
            record("skipped", "tool cap reached"),
        ]
    )["CT-ROB-001"]
    assert worst.verdict is Verdict.FAIL
    assert "2 tested, 1 skipped" in worst.summary

    partial = aggregate_results(
        [record("error_result"), record("skipped", "probe budget exhausted")]
    )["CT-ROB-001"]
    assert partial.verdict is Verdict.NOT_TESTED
    assert partial.reason == "probe budget exhausted"
    assert "1 tested, 1 skipped" in partial.summary

    complete = aggregate_results([record("error_result")])["CT-ROB-001"]
    assert complete.verdict is Verdict.PASS
    assert "1 tested, 0 skipped" in complete.summary


def test_rob_titles_and_summaries_avoid_banned_words() -> None:
    banned = ("malicious", "vulnerable", "unsafe", "attack", "exploit")
    records = [
        ProbeRecord(
            check_id,
            "pass" if check_id == "CT-ROB-006" else "error_result",
            (Evidence("probe", "detail"),),
        )
        for check_id in ROBUSTNESS_IDS
    ]
    results = aggregate_results(records)
    texts = [CHECK_BY_ID[check_id].title for check_id in ROBUSTNESS_IDS]
    texts.extend(result.summary for result in results.values())
    texts.extend(result.reason or "" for result in results.values())
    for word in banned:
        assert all(word not in text.lower() for text in texts)
