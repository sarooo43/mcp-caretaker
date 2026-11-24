"""Command line entry point.

Only ``--version`` and ``--help`` exist in this PR. A bare invocation prints help.
There are deliberately no other commands yet.
"""

from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the deliberately tiny command line parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-caretaker",
        description="Runtime behaviour tester for local MCP servers (pre-release, nothing usable yet).",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Print help for a bare invocation; argparse handles --help and --version."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
