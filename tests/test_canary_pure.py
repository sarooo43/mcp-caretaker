"""Pure tests for fake values, redaction, and canonical list comparison."""

from __future__ import annotations

import base64

from mcp_caretaker import canary, thresholds
from mcp_caretaker.checks.stability import compare_lists
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.model import Verdict


def test_make_canary_is_fresh_and_has_three_names() -> None:
    first = canary.make_canary()
    second = canary.make_canary()
    assert tuple(first) == canary.CANARY_NAMES
    assert all(value.startswith("ct_canary_") for value in first.values())
    assert all(len(value) == 42 for value in first.values())
    assert first != second


def test_base64_form_is_one_standard_ascii_encoding() -> None:
    value = "FAKE-PURE-VALUE-123456"
    encoded = canary.base64_form(value)
    assert encoded == base64.b64encode(value.encode("ascii")).decode("ascii")
    assert "-" not in encoded and "_" not in encoded


def test_redaction_map_includes_canary_base64_and_argv_env_values() -> None:
    value = "ct_canary_FAKE_TOKEN_0123456789abcdef"
    spec = LaunchSpec(
        argv=("python", "server.py", "--env", "NAME=FAKE-ARGV-VALUE-1234"),
        extra_env={"CALLER": "FAKE-CALLER-VALUE-1234"},
    )
    values = {"CARETAKER_CANARY_TOKEN": value}
    redaction = canary.build_redaction_map(spec, values)
    assert redaction["CARETAKER_CANARY_TOKEN"] == value
    assert redaction["CARETAKER_CANARY_TOKEN_BASE64"] == canary.base64_form(value)
    assert "FAKE-CALLER-VALUE-1234" in redaction.values()
    assert "NAME=FAKE-ARGV-VALUE-1234" in redaction.values()
    assert "FAKE-ARGV-VALUE-1234" in redaction.values()


def test_excerpt_redacts_full_text_before_cap() -> None:
    value = "ct_canary_FAKE_TOKEN_0123456789abcdef"
    encoded = canary.base64_form(value)
    redaction = canary.build_redaction_map(
        LaunchSpec(argv=("python", "server.py")),
        {"CARETAKER_CANARY_TOKEN": value},
    )
    text = f"before {value} {encoded} " + "X" * 400
    detail = canary.excerpt(text, redaction)
    assert value not in detail
    assert encoded not in detail
    assert "[REDACTED:CARETAKER_CANARY_TOKEN]" in detail
    assert "[REDACTED:CARETAKER_CANARY_TOKEN_BASE64]" in detail
    assert len(detail) <= thresholds.EVIDENCE_MAX_CHARS


def _tool(name: str, description: str) -> dict[str, object]:
    return {
        "name": name,
        "title": f"{name} title",
        "description": description,
        "inputSchema": {"type": "object", "properties": {}},
        "outputSchema": {"type": "object", "properties": {}},
        "annotations": {"readOnlyHint": True},
        "_meta": {"sample": name},
        "icons": [{"src": name}],
    }


def test_compare_changed_field_wins_and_ignores_order_meta_and_icons() -> None:
    first = [
        _tool("a", "A clear first description."),
        _tool("b", "B clear description."),
    ]
    second = [
        {**_tool("b", "B clear description."), "_meta": {"changed": True}},
        {**_tool("a", "A different description."), "icons": []},
        _tool("c", "C clear description."),
    ]
    verdict, summary, evidence = compare_lists(first, second, {})
    assert verdict is Verdict.FAIL
    assert "changes in common tool fields" in summary
    assert any(
        item.subject == "a" and "description" in item.detail for item in evidence
    )
    assert all(
        "_meta" not in item.detail and "icons" not in item.detail for item in evidence
    )


def test_compare_added_removed_and_reordered_lists() -> None:
    first = [
        _tool("a", "A clear first description."),
        _tool("b", "B clear description."),
    ]
    verdict, summary, evidence = compare_lists(first, [first[1]], {})
    assert verdict is Verdict.WARN
    assert "tools added or removed" in summary
    assert any(item.subject == "a" for item in evidence)
    verdict, summary, evidence = compare_lists(first, [first[1], first[0]], {})
    assert verdict is Verdict.PASS
    assert not evidence


def test_compare_detects_annotation_changes() -> None:
    first = [_tool("a", "A clear first description.")]
    second = [
        {
            **_tool("a", "A clear first description."),
            "annotations": {"readOnlyHint": True, "title": "Changed"},
        }
    ]
    verdict, _, evidence = compare_lists(first, second, {})
    assert verdict is Verdict.FAIL
    assert any(
        item.subject == "a" and "annotations" in item.detail for item in evidence
    )
