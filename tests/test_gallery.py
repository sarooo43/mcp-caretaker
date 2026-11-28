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


def _pairs(values: set[tuple[str, str]]) -> str:
    """Render expected or actual results as `CT-ID verdict` items."""
    return (
        ", ".join(f"{check} {verdict}" for check, verdict in sorted(values)) or "none"
    )


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
def test_gallery_row(row: dict[str, str], tmp_path: Path, capsys) -> None:
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
    expected = _expected(row)
    state = "OK" if actual == expected else "MISMATCH"
    with capsys.disabled():
        print(
            f"gallery: {row['Fixture']} | expected {_pairs(expected)}"
            f" | got {_pairs(actual)} | {state}"
        )
    assert actual == expected


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


FENCE_RE = re.compile(r"```sh\n(.+?)\n```", re.DOTALL)


def _page_row_target(page: Path) -> tuple[str, list[str], list[str]] | None:
    """Return the page's reproduce target as fixture, arguments, options."""
    match = FENCE_RE.search(page.read_text(encoding="utf-8"))
    if match is None:
        return None
    tokens = match.group(1).split()
    if not tokens:
        return None
    if tokens[0] != "<python>":
        return tokens[1].rsplit("/", 1)[-1], tokens[2:], []
    split = tokens.index("--")
    return tokens[split + 2].rsplit("/", 1)[-1], tokens[split + 3 :], tokens[5:split]


def test_every_page_reproduce_command_matches_a_gallery_row() -> None:
    problems: list[str] = []
    for page in sorted((ROOT / "docs/checks").glob("CT-*.md")):
        target = _page_row_target(page)
        if target is None:
            problems.append(f"{page.name}: no reproduce command")
            continue
        fixture, arguments, options = target
        matches = [
            row
            for row in ROWS
            if row["Fixture"] == fixture
            and _split(row["Arguments"]) == arguments
            and _split(row["Options"]) == options
        ]
        if len(matches) != 1:
            problems.append(f"{page.name}: {len(matches)} gallery rows match {target}")
            continue
        listed = {
            check_id
            for check_id, verdict in _expected(matches[0])
            if verdict in ("warn", "fail")
        }
        if page.stem not in listed:
            problems.append(f"{page.name}: row does not list {page.stem}")
    assert problems == []
