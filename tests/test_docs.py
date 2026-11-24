"""Pure documentation tests for the check pages and honest status."""

from __future__ import annotations

import re
from pathlib import Path

from mcp_caretaker.checks import CHECKS

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEADINGS = [
    "What it checks",
    "Why it matters",
    "Verdict",
    "How to fix",
    "Limits",
]


def test_every_check_has_docs_page_with_exact_headings() -> None:
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
