"""CLI test: --version in a real subprocess."""

from __future__ import annotations

import subprocess
import sys

from mcp_caretaker import __version__


def test_cli_version_runs() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "mcp_caretaker", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert __version__ in completed.stdout
