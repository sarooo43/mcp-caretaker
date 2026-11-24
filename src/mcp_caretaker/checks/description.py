"""Pure description/schema checks over raw ``tools/list`` tool dicts."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterator
from typing import Any

from ..model import CheckResult, Evidence, Verdict
from ..thresholds import (
    DESC_MAX_LENGTH,
    DESC_MIN_LENGTH,
    WHITESPACE_RUN_LIMIT,
)
from . import CHECK_BY_ID

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
TYPED_KEYS = ("type", "$ref", "anyOf", "oneOf", "allOf", "enum", "const")
HIDDEN_CATEGORIES = {"Cf", "Co", "Cs"}


def _make(
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


def _tool_name(tool: dict[str, Any]) -> str:
    name = tool.get("name")
    return name if isinstance(name, str) else str(name)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else str(value)


def _properties(tool: dict[str, Any]) -> dict[str, Any]:
    schema = tool.get("inputSchema")
    if not isinstance(schema, dict):
        return {}
    properties = schema.get("properties")
    return properties if isinstance(properties, dict) else {}


def _scanned_fields(tool: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Tool name/title/description plus TOP-LEVEL property name/title/description."""
    yield "name", _text(tool.get("name", ""))
    if "title" in tool:
        yield "title", _text(tool["title"])
    if "description" in tool:
        yield "description", _text(tool["description"])
    for prop_name, prop in _properties(tool).items():
        yield f"properties[{prop_name}].name", _text(prop_name)
        if isinstance(prop, dict):
            if "title" in prop:
                yield f"properties[{prop_name}].title", _text(prop["title"])
            if "description" in prop:
                yield f"properties[{prop_name}].description", _text(prop["description"])


def _is_hidden(char: str) -> bool:
    category = unicodedata.category(char)
    if category in HIDDEN_CATEGORIES:
        return True
    return category == "Cc" and char not in "\n\r\t"


def _is_horizontal(char: str) -> bool:
    return char in " \t" or unicodedata.category(char) == "Zs"


def _subject(index: int, tool: dict[str, Any], field: str) -> str:
    return f"tool[{index}] {_tool_name(tool)} {field}"


def check_desc_001(tools: list[dict[str, Any]]) -> CheckResult:
    offending = []
    for index, tool in enumerate(tools):
        description = tool.get("description")
        if not isinstance(description, str) or not description.strip():
            offending.append(
                Evidence(_subject(index, tool, "description"), "empty or non-string")
            )
    if offending:
        return _make(
            "CT-DESC-001",
            Verdict.WARN,
            f"{len(offending)} of {len(tools)} tools have no description.",
            tuple(offending),
        )
    return _make(
        "CT-DESC-001",
        Verdict.PASS,
        f"0 of {len(tools)} tools have no description.",
    )


def check_desc_002(tools: list[dict[str, Any]]) -> CheckResult:
    offending = []
    for index, tool in enumerate(tools):
        description = tool.get("description")
        if not isinstance(description, str) or not description.strip():
            continue
        length = len(description.strip())
        if length < DESC_MIN_LENGTH or length > DESC_MAX_LENGTH:
            offending.append(
                Evidence(_subject(index, tool, "description"), f"length {length}")
            )
    if offending:
        return _make(
            "CT-DESC-002",
            Verdict.WARN,
            f"{len(offending)} of {len(tools)} descriptions are outside the length limits.",
            tuple(offending),
        )
    return _make(
        "CT-DESC-002",
        Verdict.PASS,
        f"0 of {len(tools)} descriptions are outside the length limits.",
    )


def check_desc_003(tools: list[dict[str, Any]]) -> CheckResult:
    counts = Counter(_tool_name(tool) for tool in tools)
    duplicates = [name for name, count in counts.items() if count > 1]
    if duplicates:
        evidence = tuple(
            Evidence("duplicate name", f"{name}: {counts[name]} tools")
            for name in duplicates
        )
        return _make(
            "CT-DESC-003",
            Verdict.FAIL,
            f"{len(duplicates)} duplicate tool names were found.",
            evidence,
        )
    return _make(
        "CT-DESC-003",
        Verdict.PASS,
        f"0 duplicate tool names were found in {len(tools)} tools.",
    )


def check_desc_004(tools: list[dict[str, Any]]) -> CheckResult:
    offending = []
    for index, tool in enumerate(tools):
        schema = tool.get("inputSchema")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            offending.append(
                Evidence(_subject(index, tool, "inputSchema"), "not an object schema")
            )
    if offending:
        return _make(
            "CT-DESC-004",
            Verdict.FAIL,
            f"{len(offending)} of {len(tools)} tools have no object inputSchema.",
            tuple(offending),
        )
    return _make(
        "CT-DESC-004",
        Verdict.PASS,
        f"0 of {len(tools)} tools have no object inputSchema.",
    )


def check_desc_005(tools: list[dict[str, Any]]) -> CheckResult:
    offending = []
    for index, tool in enumerate(tools):
        for prop_name, prop in _properties(tool).items():
            typed = isinstance(prop, dict) and any(key in prop for key in TYPED_KEYS)
            if not typed:
                offending.append(
                    Evidence(
                        _subject(index, tool, f"properties[{prop_name}]"),
                        "no typed key",
                    )
                )
    if offending:
        return _make(
            "CT-DESC-005",
            Verdict.WARN,
            f"{len(offending)} top-level properties are not typed.",
            tuple(offending),
        )
    return _make(
        "CT-DESC-005",
        Verdict.PASS,
        "0 top-level properties are not typed.",
    )


def check_desc_006(tools: list[dict[str, Any]]) -> CheckResult:
    offending = []
    for index, tool in enumerate(tools):
        for prop_name, prop in _properties(tool).items():
            description = prop.get("description") if isinstance(prop, dict) else None
            if not isinstance(description, str) or not description.strip():
                offending.append(
                    Evidence(
                        _subject(index, tool, f"properties[{prop_name}]"),
                        "no description",
                    )
                )
    if offending:
        return _make(
            "CT-DESC-006",
            Verdict.WARN,
            f"{len(offending)} top-level properties have no description.",
            tuple(offending),
        )
    return _make(
        "CT-DESC-006",
        Verdict.PASS,
        "0 top-level properties have no description.",
    )


def check_desc_007(tools: list[dict[str, Any]]) -> CheckResult:
    hits = []
    for index, tool in enumerate(tools):
        for field, text in _scanned_fields(tool):
            for position, char in enumerate(text):
                if not _is_hidden(char):
                    continue
                code_point = f"U+{ord(char):04X}"
                unicode_name = unicodedata.name(char, "UNNAMED")
                hits.append(
                    Evidence(
                        _subject(index, tool, field),
                        f"position {position}: {code_point} {unicode_name}",
                    )
                )
    if hits:
        return _make(
            "CT-DESC-007",
            Verdict.WARN,
            f"{len(hits)} hidden characters were found in scanned text.",
            tuple(hits),
        )
    return _make(
        "CT-DESC-007",
        Verdict.PASS,
        "0 hidden characters were found in scanned text.",
    )


def check_desc_008(tools: list[dict[str, Any]]) -> CheckResult:
    hits = []
    for index, tool in enumerate(tools):
        for field, text in _scanned_fields(tool):
            position = 0
            while position < len(text):
                if not _is_horizontal(text[position]):
                    position += 1
                    continue
                start = position
                while position < len(text) and _is_horizontal(text[position]):
                    position += 1
                run = position - start
                if run >= WHITESPACE_RUN_LIMIT:
                    after = text[position : position + 60]
                    hits.append(
                        Evidence(
                            _subject(index, tool, field),
                            f"run length {run}, position {start}, after run: {after}",
                        )
                    )
    if hits:
        return _make(
            "CT-DESC-008",
            Verdict.WARN,
            f"{len(hits)} horizontal whitespace runs were found.",
            tuple(hits),
        )
    return _make(
        "CT-DESC-008",
        Verdict.PASS,
        "0 horizontal whitespace runs were found.",
    )


def check_desc_009(tools: list[dict[str, Any]]) -> CheckResult:
    offending = []
    for index, tool in enumerate(tools):
        name = tool.get("name")
        if not isinstance(name, str) or NAME_RE.fullmatch(name) is None:
            offending.append(
                Evidence(_subject(index, tool, "name"), "name rule mismatch")
            )
    if offending:
        return _make(
            "CT-DESC-009",
            Verdict.WARN,
            f"{len(offending)} of {len(tools)} tool names do not match the spec name rule.",
            tuple(offending),
        )
    return _make(
        "CT-DESC-009",
        Verdict.PASS,
        f"0 of {len(tools)} tool names do not match the spec name rule.",
    )


DESCRIPTION_CHECK_FUNCTIONS: dict[
    str, Callable[[list[dict[str, Any]]], CheckResult]
] = {
    "CT-DESC-001": check_desc_001,
    "CT-DESC-002": check_desc_002,
    "CT-DESC-003": check_desc_003,
    "CT-DESC-004": check_desc_004,
    "CT-DESC-005": check_desc_005,
    "CT-DESC-006": check_desc_006,
    "CT-DESC-007": check_desc_007,
    "CT-DESC-008": check_desc_008,
    "CT-DESC-009": check_desc_009,
}
