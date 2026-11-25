"""One real-CLI test per gallery row, plus table shape checks."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "docs/gallery.md"
TIMEOUT = 60
COLUMNS = [
    "Fixture",
    "Arguments",
    "Options",
    "Expected warn/fail results",
    "Note",
]
EXPECTED_RE = re.compile(r"^CT-[A-Z]+-\d{3}:(?:warn|fail)$")


def _rows_and_problems() -> tuple[list[dict[str, str]], list[str]]:
    """Parse the bad-servers table; return its rows and any shape problems."""
    rows: list[dict[str, str]] = []
    problems: list[str] = []
    in_table = False
    found_table = False
    header: list[str] | None = None
    for line in GALLERY.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_table = line.strip() == "## Bad servers"
            header = None
            continue
        if not in_table or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            found_table = True
            if cells != COLUMNS:
                problems.append(f"unexpected header: {line}")
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if len(cells) != len(COLUMNS):
            problems.append(f"wrong cell count: {line}")
            continue
        rows.append(dict(zip(COLUMNS, cells)))
    if not found_table:
        problems.append("bad-servers table not found")
    return rows, problems


def _expected(row: dict[str, str]) -> set[tuple[str, str]]:
    text = row["Expected warn/fail results"]
    if text == "none":
        return set()
    return {
        tuple(item.strip().split(":", 1)) for item in text.split(",") if item.strip()
    }


def _split(value: str) -> list[str]:
    return [] if value == "-" else value.split()


ROWS, PROBLEMS = _rows_and_problems()
IDS = [
    "-".join(
        part
        for part in (row["Fixture"], row["Arguments"], row["Options"])
        if part != "-"
    )
    for row in ROWS
]


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_gallery_row(row: dict[str, str], tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mcp_caretaker",
            "check",
            "--trust",
            "--json",
            str(json_path),
            *_split(row["Options"]),
            "--",
            sys.executable,
            str(ROOT / "examples/servers" / row["Fixture"]),
            *_split(row["Arguments"]),
        ],
        capture_output=True,
        timeout=TIMEOUT,
        cwd=tmp_path,
        check=False,
    )
    assert json_path.exists(), completed.stderr.decode("utf-8", errors="replace")
    report = json.loads(json_path.read_text(encoding="utf-8"))
    actual = {
        (item["check_id"], item["verdict"])
        for item in report["results"]
        if item["verdict"] in ("warn", "fail")
    }
    assert actual == _expected(row)


def test_every_bad_fixture_is_in_the_gallery() -> None:
    listed = {row["Fixture"] for row in ROWS}
    present = {path.name for path in (ROOT / "examples/servers").glob("bad_*.py")}
    assert present <= listed


def test_gallery_rows_are_well_formed() -> None:
    assert PROBLEMS == []
    assert ROWS
    for row in ROWS:
        fixture = row["Fixture"]
        assert fixture.endswith(".py") and "/" not in fixture
        assert (ROOT / "examples/servers" / fixture).is_file()
        text = row["Expected warn/fail results"]
        if text != "none":
            assert all(EXPECTED_RE.match(item.strip()) for item in text.split(","))
