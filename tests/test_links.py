"""Markdown links must point at files that exist in this repository."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:")
BLOB_PREFIX = "https://github.com/sarooo43/mcp-caretaker/blob/main/"


def _markdown_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "examples/servers/README.md"]
    files.extend(sorted((ROOT / "docs").rglob("*.md")))
    return files


def test_relative_markdown_links_point_to_existing_files() -> None:
    problems: list[str] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            if target.startswith(BLOB_PREFIX):
                local = target[len(BLOB_PREFIX) :].split("#", 1)[0]
                if not (ROOT / local).exists():
                    problems.append(f"{path.relative_to(ROOT).as_posix()} -> {target}")
                continue
            if target.startswith(SKIP_PREFIXES) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                problems.append(f"{path.relative_to(ROOT).as_posix()} -> {target}")
    assert problems == []
