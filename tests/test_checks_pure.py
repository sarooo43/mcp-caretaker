"""Pure unit tests for the startup and description/schema check functions."""

from __future__ import annotations

from typing import Any

from mcp_caretaker.checks.description import (
    DESCRIPTION_CHECK_FUNCTIONS,
    TYPED_KEYS,
    check_desc_001,
    check_desc_002,
    check_desc_003,
    check_desc_004,
    check_desc_005,
    check_desc_006,
    check_desc_007,
    check_desc_008,
    check_desc_009,
)
from mcp_caretaker.checks.startup import (
    StartupContext,
    check_start_002,
    check_start_003,
    check_start_005,
)
from mcp_caretaker.model import Verdict
from mcp_caretaker.thresholds import DESC_MAX_LENGTH, DESC_MIN_LENGTH


def _tool(
    name: str = "ok",
    description: str = "A clear description for this tool.",
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if properties is None:
        properties = {"value": {"type": "string", "description": "A string value."}}
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": properties},
    }


def test_desc_008_run_length_boundary() -> None:
    def tool(run: int, char: str) -> dict[str, Any]:
        return _tool(description="x" + char * run, properties={})

    assert check_desc_008([tool(39, " ")]).verdict is Verdict.PASS
    assert check_desc_008([tool(40, " ")]).verdict is Verdict.WARN
    assert check_desc_008([tool(40, "\t")]).verdict is Verdict.WARN
    assert check_desc_008([tool(40, "\u2003")]).verdict is Verdict.WARN


def test_desc_002_length_boundaries() -> None:
    lengths = (
        DESC_MIN_LENGTH - 1,
        DESC_MIN_LENGTH,
        DESC_MAX_LENGTH,
        DESC_MAX_LENGTH + 1,
    )
    verdicts = [
        check_desc_002([_tool(description="x" * length)]).verdict for length in lengths
    ]
    assert verdicts == [Verdict.WARN, Verdict.PASS, Verdict.PASS, Verdict.WARN]


def test_desc_005_typed_equivalents_and_untyped_property() -> None:
    for key in TYPED_KEYS:
        tool = _tool(properties={"value": {key: "v"}})
        assert check_desc_005([tool]).verdict is Verdict.PASS
    untyped = _tool(properties={"value": {"description": "An untyped value."}})
    assert check_desc_005([untyped]).verdict is Verdict.WARN


def test_desc_007_hidden_categories_and_allowed_marks() -> None:
    for char in ("\u200b", "\u0001", "\ue000", "\ud800"):
        tool = _tool(description="A clear description " + char)
        assert check_desc_007([tool]).verdict is Verdict.WARN
    allowed = _tool(description="Cafe\u0301 \ufe0f")
    allowed["title"] = "Cafe\u0301"
    assert check_desc_007([allowed]).verdict is Verdict.PASS
    line_breaks = _tool(description="A clear description\nwith\tline\rbreaks")
    assert check_desc_007([line_breaks]).verdict is Verdict.PASS


def test_desc_007_scans_only_declared_fields() -> None:
    tool = _tool(
        properties={
            "nested": {
                "type": "object",
                "description": "A nested object.",
                "properties": {
                    "deep": {
                        "type": "string",
                        "description": "Hidden \u200b nested text.",
                    }
                },
            }
        }
    )
    tool["outputSchema"] = {"type": "object", "description": "Hidden \u200b output"}
    assert check_desc_007([tool]).verdict is Verdict.PASS
    tool["title"] = "Title\u200b"
    assert check_desc_007([tool]).verdict is Verdict.WARN
    property_tool = _tool(
        properties={"value\u200b": {"type": "string", "description": "A value."}}
    )
    assert check_desc_007([property_tool]).verdict is Verdict.WARN


def test_desc_009_name_rule_boundaries() -> None:
    names = ("", "a", "a" * 128, "a" * 129, "a b")
    verdicts = [check_desc_009([_tool(name=name)]).verdict for name in names]
    assert verdicts == [
        Verdict.WARN,
        Verdict.PASS,
        Verdict.PASS,
        Verdict.WARN,
        Verdict.WARN,
    ]
    assert check_desc_009([_tool(name="bad name")]).verdict is Verdict.WARN


def test_desc_001_003_004_006_aggregate_problems() -> None:
    missing = _tool("missing")
    del missing["description"]
    duplicate = _tool("duplicate")
    bad_schema = _tool("bad_schema")
    bad_schema["inputSchema"] = {"type": "string"}
    undocumented = _tool("undocumented", properties={"value": {"type": "string"}})
    tools = [missing, duplicate, duplicate, bad_schema, undocumented]
    assert check_desc_001(tools).verdict is Verdict.WARN
    assert len(check_desc_001(tools).evidence) == 1
    assert check_desc_003(tools).verdict is Verdict.FAIL
    assert check_desc_004(tools).verdict is Verdict.FAIL
    assert check_desc_006(tools).verdict is Verdict.WARN


def test_start_002_includes_negotiated_protocol_version() -> None:
    result = check_start_002(
        StartupContext(
            protocol_version="test-protocol",
            server_name="test-server",
            server_version="1.0",
        )
    )
    assert result.verdict is Verdict.PASS
    assert any(
        item.subject == "protocolVersion" and item.detail == "test-protocol"
        for item in result.evidence
    )


def test_start_003_zero_tools_and_page_cap_warn() -> None:
    zero = check_start_003(StartupContext(zero_tools=True))
    assert zero.verdict is Verdict.WARN
    assert any(item.subject == "empty_tool_list" for item in zero.evidence)
    cap = check_start_003(StartupContext(pages_cap_hit=True, page_count=10))
    assert cap.verdict is Verdict.WARN
    assert any(item.subject == "page_cap" for item in cap.evidence)


def test_start_005_unknown_outcome_is_not_tested_with_reason() -> None:
    result = check_start_005(StartupContext())
    assert result.verdict is Verdict.NOT_TESTED
    assert result.reason is not None


def test_check_summaries_are_one_factual_line_and_contain_facts() -> None:
    tools = [
        _tool("ok"),
        _tool("duplicate"),
        _tool("duplicate"),
    ]
    for check_id, function in DESCRIPTION_CHECK_FUNCTIONS.items():
        result = function(tools)
        assert "\n" not in result.summary
        assert result.check_id == check_id
        for word in ("malicious", "vulnerable", "attack"):
            assert word not in result.summary.lower()
        if result.verdict in (Verdict.WARN, Verdict.FAIL):
            assert any(char.isdigit() for char in result.summary)
