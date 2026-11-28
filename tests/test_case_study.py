"""The case study page must agree with the saved report files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_case_study_page_matches_the_saved_reports() -> None:
    page = (ROOT / "docs/case-study.md").read_text(encoding="utf-8")
    lines = page.splitlines()
    for name in ("time", "git", "fetch"):
        report = json.loads(
            (ROOT / "docs/case-study" / f"{name}.json").read_text(encoding="utf-8")
        )
        counts = report["counts"]
        totals = (
            f"pass={counts['pass']} warn={counts['warn']} "
            f"fail={counts['fail']} not_tested={counts['not_tested']}"
        )
        package = f"mcp-server-{name}"
        assert any(package in line and totals in line for line in lines), name
