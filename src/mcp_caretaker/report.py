"""Report rendering: one JSON dict is the source of truth.

Markdown and the terminal summary are rendered from the same dict that is
written as JSON. Server text is never executed, used as a path, or trusted;
terminal text is escaped to printable ASCII and Markdown fences server text.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import PureWindowsPath
from typing import Any

from .model import RunResult

SAFETY_SENTENCE = (
    "A pass is not a safety guarantee. "
    "Running a server executes its code; this tool is not a sandbox."
)


def escape_ascii(text: str, *, escape_backslash: bool = True) -> str:
    """Escape every character outside printable ASCII as a visible escape.

    Printable ASCII (space to tilde) is kept, except backslash which is
    doubled so a literal escape sequence in server text cannot be mistaken
    for one of ours. Everything else becomes ``\\uXXXX`` or ``\\UXXXXXXXX``.
    The result is pure ASCII and does not depend on the console code page.
    Local paths are printed with ``escape_backslash=False`` so a Windows path
    stays copyable; they are not server text.
    """
    out: list[str] = []
    for char in text:
        code = ord(char)
        if char == "\\" and escape_backslash:
            out.append("\\\\")
        elif 0x20 <= code <= 0x7E:
            out.append(char)
        elif code <= 0xFFFF:
            out.append(f"\\u{code:04X}")
        else:
            out.append(f"\\U{code:08X}")
    return "".join(out)


def _longest_backtick_run(text: str) -> int:
    longest = 0
    current = 0
    for char in text:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def fence(text: str) -> str:
    """Wrap text in a code fence longer than any backtick run inside it."""
    marker = "`" * max(3, _longest_backtick_run(text) + 1)
    return f"{marker}\n{text}\n{marker}"


def counts_for(run: RunResult) -> dict[str, int]:
    """Count verdicts in the fixed JSON key order."""
    counts = {"pass": 0, "warn": 0, "fail": 0, "not_tested": 0}
    for result in run.results:
        counts[result.verdict.value] += 1
    return counts


def exit_code_for_counts(counts: Mapping[str, int], fail_on: str) -> int:
    """Map counts to an exit code; ``not_tested`` never changes it."""
    if counts.get("fail", 0) > 0:
        return 1
    if fail_on == "warn" and counts.get("warn", 0) > 0:
        return 1
    return 0


def program_name(program: str) -> str:
    """Return the file name only, handling both slash styles."""
    return PureWindowsPath(program).name


def build_report_dict(
    run: RunResult, program: str, argument_count: int
) -> dict[str, Any]:
    """Build the JSON-ready dict with fixed key order and no per-run values."""
    return {
        "schema_version": 1,
        "tool": {"name": "mcp-caretaker", "version": run.caretaker_version},
        "server": {
            "program": program_name(program),
            "argument_count": argument_count,
        },
        "protocol_version": run.protocol_version,
        "counts": counts_for(run),
        "results": run.to_dict()["results"],
    }


def render_json(report: dict[str, Any]) -> str:
    """Render the JSON report text with a trailing newline."""
    return json.dumps(report, indent=2, ensure_ascii=True) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    """Render Markdown from the same dict; server text only inside fences."""
    tool = report["tool"]
    server = report["server"]
    counts = report["counts"]
    protocol = report["protocol_version"]
    lines = [
        "# mcp-caretaker report",
        "",
        f"Tool: {tool['name']} {tool['version']}",
        "Program:",
        fence(str(server["program"])),
        f"Arguments: {server['argument_count']}",
        "Protocol version:",
        fence(str(protocol) if protocol is not None else "unknown"),
        "",
        "## Results",
        "",
        "| ID | Title | Verdict |",
        "| --- | --- | --- |",
    ]
    for result in report["results"]:
        lines.append(
            f"| {result['check_id']} | {result['title']} | {result['verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- pass: {counts['pass']}",
            f"- warn: {counts['warn']}",
            f"- fail: {counts['fail']}",
            f"- not_tested: {counts['not_tested']}",
            "",
            SAFETY_SENTENCE,
            "",
            "## Details",
            "",
        ]
    )
    for result in report["results"]:
        if result["verdict"] == "pass":
            continue
        lines.append(
            f"### {result['check_id']} {result['title']} "
            f"[{str(result['verdict']).upper()}]"
        )
        lines.append("")
        content = [f"summary: {result['summary']}"]
        if result["reason"] is not None:
            content.append(f"reason: {result['reason']}")
        for index, item in enumerate(result["evidence"], 1):
            content.append(f"evidence {index} subject: {item['subject']}")
            content.append(f"evidence {index} detail: {item['detail']}")
            if item["replay"] is not None:
                content.append(f"evidence {index} replay: {item['replay']}")
        lines.append(fence("\n".join(content)))
        lines.append("")
    return "\n".join(lines)


def render_terminal(
    report: dict[str, Any],
    json_path: str | None = None,
    markdown_path: str | None = None,
) -> str:
    """Render the short ASCII terminal summary from the same dict."""
    tool = report["tool"]
    server = report["server"]
    counts = report["counts"]
    protocol = report["protocol_version"]
    lines = [
        f"mcp-caretaker {escape_ascii(str(tool['version']))}",
        f"Program: {escape_ascii(str(server['program']))}",
        f"Arguments: {server['argument_count']}",
        "Protocol version: "
        + (escape_ascii(str(protocol)) if protocol is not None else "unknown"),
    ]
    for result in report["results"]:
        word = str(result["verdict"]).upper()
        lines.append(
            f"[{word}] {result['check_id']} {escape_ascii(str(result['title']))}"
        )
    for result in report["results"]:
        if result["verdict"] == "pass":
            continue
        lines.append(f"{result['check_id']} summary: {escape_ascii(result['summary'])}")
        if result["reason"] is not None:
            lines.append(
                f"{result['check_id']} reason: {escape_ascii(result['reason'])}"
            )
        for item in result["evidence"]:
            lines.append(
                f"{result['check_id']} evidence subject: "
                f"{escape_ascii(item['subject'])}"
            )
            lines.append(
                f"{result['check_id']} evidence detail: {escape_ascii(item['detail'])}"
            )
    lines.append(
        f"Totals: pass={counts['pass']} warn={counts['warn']} "
        f"fail={counts['fail']} not_tested={counts['not_tested']}"
    )
    lines.append(SAFETY_SENTENCE)
    if json_path is not None:
        lines.append(f"JSON: {escape_ascii(json_path, escape_backslash=False)}")
    if markdown_path is not None:
        lines.append(f"Markdown: {escape_ascii(markdown_path, escape_backslash=False)}")
    return "\n".join(lines) + "\n"
