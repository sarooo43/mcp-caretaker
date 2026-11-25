"""Command line entry point: ``mcp-caretaker check --trust -- PROGRAM``.

The server command is split at the first literal ``--`` before argparse sees
the arguments, so later ``--`` values reach the server unchanged. The server
is launched directly, never through a shell. Nothing is launched without
``--trust`` and output paths are validated before any launch.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import fields
from pathlib import Path

from . import __version__
from .checks import CHECKS
from .launch import LaunchSpec, redact_values
from .report import (
    build_report_dict,
    exit_code_for_counts,
    render_json,
    render_markdown,
    render_terminal,
)
from .runner import run_checks
from .thresholds import EVIDENCE_MAX_CHARS

TRUST_MESSAGE = (
    "error: --trust is required; --trust means this runs the server "
    "on your machine and is not a sandbox"
)
USAGE = "usage: mcp-caretaker check --trust [options] -- PROGRAM [ARGS...]"


def _launch_defaults() -> dict[str, float]:
    """Read timeout defaults from LaunchSpec so numbers are not duplicated."""
    defaults: dict[str, float] = {}
    for item in fields(LaunchSpec):
        if item.name in ("startup_timeout", "call_timeout"):
            defaults[item.name] = float(item.default)  # type: ignore[arg-type]
    return defaults


def build_parser() -> argparse.ArgumentParser:
    """Build the parser for the options before the first ``--``."""
    parser = argparse.ArgumentParser(
        prog="mcp-caretaker check",
        description=(
            "Run 25 behaviour checks against a local MCP server. "
            "This launches the server on your machine; it is not a sandbox."
        ),
    )
    parser.add_argument(
        "--trust",
        action="store_true",
        help="confirm that running the server on this machine is intended",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="extra environment variable for the server (repeatable)",
    )
    parser.add_argument("--startup-timeout", type=float, default=None)
    parser.add_argument("--call-timeout", type=float, default=None)
    parser.add_argument("--json", default=None, metavar="PATH")
    parser.add_argument("--markdown", default=None, metavar="PATH")
    parser.add_argument("--fail-on", choices=("fail", "warn"), default="fail")
    return parser


def _parse_env(items: list[str]) -> dict[str, str] | None:
    """Parse repeatable NAME=VALUE items; return None on a usage error."""
    env: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            return None
        name, value = item.split("=", 1)
        if not name or name.startswith("CARETAKER_CANARY_"):
            return None
        env[name] = value
    return env


def _output_error(path: str) -> bool:
    """Return True when the output parent folder is missing or not a folder."""
    parent = Path(path).parent
    return not parent.exists() or not parent.is_dir()


def split_server_command(rest: list[str]) -> tuple[list[str], list[str]] | None:
    """Split at the first literal ``--``; None when there is no separator."""
    if "--" not in rest:
        return None
    split = rest.index("--")
    return rest[:split], rest[split + 1 :]


def main(argv: list[str] | None = None) -> int:
    """Run the check command; return 0, 1, or 2 as documented."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--version"]:
        print(f"mcp-caretaker {__version__}")
        return 0
    if not args or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2
    rest = args[1:]
    if not rest:
        print(USAGE, file=sys.stderr)
        return 2
    split = split_server_command(rest)
    if split is None:
        print("error: missing -- before the server command", file=sys.stderr)
        return 2
    option_args, server_argv = split
    if not server_argv:
        print("error: missing server command after --", file=sys.stderr)
        return 2
    parser = build_parser()
    try:
        options = parser.parse_args(option_args)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    if not options.trust:
        print(TRUST_MESSAGE, file=sys.stderr)
        return 2
    env = _parse_env(options.env)
    if env is None:
        print(
            "error: --env needs NAME=VALUE with a non-empty name that does "
            "not start with CARETAKER_CANARY_",
            file=sys.stderr,
        )
        return 2
    defaults = _launch_defaults()
    startup_timeout = (
        defaults["startup_timeout"]
        if options.startup_timeout is None
        else options.startup_timeout
    )
    call_timeout = (
        defaults["call_timeout"]
        if options.call_timeout is None
        else options.call_timeout
    )
    if startup_timeout <= 0 or call_timeout <= 0:
        print("error: timeouts must be greater than 0", file=sys.stderr)
        return 2
    if options.json is not None and _output_error(options.json):
        print(f"error: output folder does not exist: {options.json}", file=sys.stderr)
        return 2
    if options.markdown is not None and _output_error(options.markdown):
        print(
            f"error: output folder does not exist: {options.markdown}",
            file=sys.stderr,
        )
        return 2
    if (
        options.json is not None
        and options.markdown is not None
        and Path(options.json) == Path(options.markdown)
    ):
        print("error: --json and --markdown must differ", file=sys.stderr)
        return 2
    spec = LaunchSpec(
        argv=tuple(server_argv),
        extra_env=env,
        startup_timeout=startup_timeout,
        call_timeout=call_timeout,
    )
    print(f"running {len(CHECKS)} checks; this launches the server", file=sys.stderr)
    try:
        run = asyncio.run(run_checks(spec, confirmed=True))
    except Exception as exc:  # noqa: BLE001 - any failure becomes exit 2
        message = redact_values(str(exc), env)
        if len(message) > EVIDENCE_MAX_CHARS:
            message = message[:EVIDENCE_MAX_CHARS] + "...[truncated]"
        print(f"{type(exc).__name__}: {message}", file=sys.stderr)
        return 2
    report = build_report_dict(run, server_argv[0], len(server_argv) - 1)
    sys.stdout.write(
        render_terminal(report, json_path=options.json, markdown_path=options.markdown)
    )
    json_text = render_json(report) if options.json is not None else None
    markdown_text = render_markdown(report) if options.markdown is not None else None
    try:
        if options.json is not None and json_text is not None:
            Path(options.json).write_text(json_text, encoding="utf-8")
        if options.markdown is not None and markdown_text is not None:
            Path(options.markdown).write_text(markdown_text, encoding="utf-8")
    except OSError as exc:
        print(f"error: could not write output: {exc}", file=sys.stderr)
        return 2
    return exit_code_for_counts(report["counts"], options.fail_on)
