"""Pure documentation tests for the check pages and honest status."""

from __future__ import annotations

import re
from pathlib import Path

from mcp_caretaker.checks import CHECKS
from mcp_caretaker.checks.description import DESCRIPTION_CHECK_FUNCTIONS
from mcp_caretaker.checks.startup import STARTUP_CHECK_FUNCTIONS, StartupContext

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEADINGS = [
    "What it checks",
    "Why it matters",
    "Verdict",
    "How to fix",
    "Limits",
]
BANNED_WORDS = ("malicious", "vulnerable", "unsafe", "attack", "exploit")


def test_every_check_has_docs_page_with_required_headings() -> None:
    for info in CHECKS:
        path = ROOT / info.docs_path
        text = path.read_text(encoding="utf-8")
        headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
        assert headings == EXPECTED_HEADINGS, path
        assert "not_tested` is never counted or displayed as pass" in text


def test_new_docs_have_no_dates_or_chained_shell_commands() -> None:
    paths = [
        ROOT / "README.md",
        ROOT / "examples/servers/README.md",
        ROOT / "docs/checks/README.md",
        *(ROOT / info.docs_path for info in CHECKS),
    ]
    joined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}\b", joined)
    assert "&&" not in joined
    for word in (
        "malicious",
        "vulnerable",
        "attack",
        "exploit",
        "unsafe",
        "robustness",
        "canary",
        "stability",
    ):
        assert word not in joined.lower()


def test_thresholds_are_documented_as_guesses() -> None:
    text = (ROOT / "docs/checks/README.md").read_text(encoding="utf-8")
    phrase = "this number is a guess; it lives in thresholds.py"
    assert text.count(phrase) == 7
    for number in ("10", "1000", "40", "20", "300", "5"):
        assert f"= {number}" in text


def test_every_docs_page_matches_a_registered_check() -> None:
    pages = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "docs/checks").glob("CT-*.md")
    }
    assert pages == {info.docs_path for info in CHECKS}


def test_titles_and_summaries_avoid_banned_words() -> None:
    tool = {
        "name": "ok",
        "description": "A clear description for this tool.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "A string value."}
            },
        },
    }
    results = [function([tool]) for function in DESCRIPTION_CHECK_FUNCTIONS.values()]
    results.extend(
        function(StartupContext()) for function in STARTUP_CHECK_FUNCTIONS.values()
    )
    texts = [info.title for info in CHECKS]
    texts.extend(result.summary for result in results)
    texts.extend(result.reason or "" for result in results)
    for word in BANNED_WORDS:
        assert all(word not in text.lower() for text in texts)
