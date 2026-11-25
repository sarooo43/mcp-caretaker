"""CLI behaviour tests: every case starts a REAL subprocess via ``python -m``.

Pure tests cover only fence, escape, argument splitting and counts to exit
code. All behaviour assertions use real subprocess runs with absolute
example-server paths, a timeout, and UTF-8 decoding with replacement.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path, PureWindowsPath

import pytest
from helpers import server_path

from mcp_caretaker import __version__
from mcp_caretaker.checks import CHECK_IDS
from mcp_caretaker.cli import main, split_server_command
from mcp_caretaker.model import CheckResult, RunResult, Verdict
from mcp_caretaker.report import (
    SAFETY_SENTENCE,
    build_report_dict,
    escape_ascii,
    exit_code_for_counts,
    fence,
    program_name,
    render_terminal,
)

TIMEOUT = 30
FAKE_ARG_SECRET = "ct-fake-argument-value-1234"
FAKE_ENV_SECRET = "ct-fake-env-value-9876"


def _run_cli(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        [sys.executable, "-m", "mcp_caretaker", "check", *args],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    return completed.returncode, stdout, stderr


def _server(name: str, *extra: str) -> list[str]:
    return [sys.executable, str(server_path(name)), *extra]


def _check_lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line.startswith("[")]


def _console_command() -> Path:
    """Locate the installed console command in this interpreter's scripts."""
    scripts = sysconfig.get_path("scripts")
    found = shutil.which("mcp-caretaker", path=scripts) if scripts else None
    assert found is not None, "mcp-caretaker console command was not found"
    return Path(found)


def test_clean_server_exit_zero_with_json_and_markdown(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    code, stdout, stderr = _run_cli(
        [
            "--trust",
            "--json",
            str(json_path),
            "--markdown",
            str(markdown_path),
            "--",
            *_server("clean_server.py"),
        ]
    )
    assert code == 0
    assert "running 25 checks; this launches the server" in stderr
    lines = _check_lines(stdout)
    assert len(lines) == 25
    for line, check_id in zip(lines, CHECK_IDS, strict=True):
        assert line.startswith(f"[PASS] {check_id} ")
    assert "Totals: pass=25 warn=0 fail=0 not_tested=0" in stdout
    assert SAFETY_SENTENCE in stdout
    assert str(json_path) in stdout
    assert str(markdown_path) in stdout
    assert "replay" not in stdout
    raw = json_path.read_bytes()
    assert raw.endswith(b"\n")
    assert all(byte < 128 for byte in raw)
    report = json.loads(raw.decode("utf-8"))
    assert list(report) == [
        "schema_version",
        "tool",
        "server",
        "protocol_version",
        "counts",
        "results",
    ]
    assert report["schema_version"] == 1
    assert report["tool"] == {"name": "mcp-caretaker", "version": __version__}
    assert report["server"]["program"] == PureWindowsPath(sys.executable).name
    assert report["server"]["argument_count"] == 1
    assert isinstance(report["protocol_version"], str)
    assert report["counts"] == {"pass": 25, "warn": 0, "fail": 0, "not_tested": 0}
    assert [item["check_id"] for item in report["results"]] == list(CHECK_IDS)
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# mcp-caretaker report" in markdown
    assert SAFETY_SENTENCE in markdown
    assert "### CT-" not in markdown


def test_missing_trust_exits_2_and_launches_nothing(tmp_path: Path) -> None:
    pidfile = tmp_path / "server.pid"
    json_path = tmp_path / "report.json"
    code, stdout, stderr = _run_cli(
        [
            "--env",
            f"CARETAKER_TEST_PIDFILE={pidfile}",
            "--json",
            str(json_path),
            "--",
            *_server("bad_huge_input.py"),
        ]
    )
    assert code == 2
    assert "--trust" in stderr
    assert "not a sandbox" in stderr
    assert stdout == ""
    assert not pidfile.exists()
    assert not json_path.exists()


def test_missing_separator_and_empty_command_exit_2() -> None:
    code, _, _ = _run_cli(["--trust", *_server("clean_server.py")])
    assert code == 2
    code, _, _ = _run_cli(["--trust", "--"])
    assert code == 2


def test_failing_server_exits_1() -> None:
    code, stdout, _ = _run_cli(["--trust", "--", *_server("bad_exits_immediately.py")])
    assert code == 1
    assert "[FAIL] CT-START-001 " in stdout
    assert "Totals: pass=0 warn=0 fail=1 not_tested=24" in stdout


def test_warn_server_exit_codes() -> None:
    code, stdout, _ = _run_cli(
        ["--trust", "--", *_server("bad_canary_leaks.py", "stderr")]
    )
    assert code == 0
    assert "warn=1" in stdout
    code, stdout, _ = _run_cli(
        [
            "--trust",
            "--fail-on",
            "warn",
            "--",
            *_server("bad_canary_leaks.py", "stderr"),
        ]
    )
    assert code == 1
    assert "warn=1" in stdout


def test_only_writers_not_tested_keeps_exit_zero() -> None:
    code, stdout, _ = _run_cli(["--trust", "--", *_server("only_writers_server.py")])
    assert code == 0
    assert "[NOT_TESTED]" in stdout
    assert "not_tested=" in stdout
    assert "fail=0" in stdout


def test_server_arguments_never_written(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    code, stdout, stderr = _run_cli(
        [
            "--trust",
            "--json",
            str(json_path),
            "--markdown",
            str(markdown_path),
            "--",
            *_server("clean_server.py", "--token", FAKE_ARG_SECRET),
        ]
    )
    assert code == 0
    for text in (
        stdout,
        stderr,
        json_path.read_text(encoding="utf-8"),
        markdown_path.read_text(encoding="utf-8"),
    ):
        assert FAKE_ARG_SECRET not in text


def test_env_value_redacted_in_json(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    code, stdout, stderr = _run_cli(
        [
            "--trust",
            "--env",
            f"CARETAKER_FAKE_TEXT={FAKE_ENV_SECRET}",
            "--json",
            str(json_path),
            "--",
            *_server("leaky_stdout.py"),
        ]
    )
    assert code == 0
    for text in (stdout, stderr, json_path.read_text(encoding="utf-8")):
        assert FAKE_ENV_SECRET not in text
    assert "[REDACTED:CARETAKER_FAKE_TEXT]" in json_path.read_text(encoding="utf-8")


def test_hostile_text_escaped_and_fenced(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    code, stdout, _ = _run_cli(
        [
            "--trust",
            "--json",
            str(json_path),
            "--markdown",
            str(markdown_path),
            "--",
            *_server("bad_hostile_text.py"),
        ]
    )
    assert code == 0
    assert all(ord(char) < 128 for char in stdout)
    assert "\x1b" not in stdout
    assert "caf\\u00E9" in stdout
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "``````" in markdown
    assert "Hostile" in markdown
    raw_json = json_path.read_bytes()
    assert all(byte < 128 for byte in raw_json)


def test_output_paths_validated_before_launch(tmp_path: Path) -> None:
    pidfile = tmp_path / "server.pid"
    missing = tmp_path / "nope" / "report.json"
    code, stdout, _ = _run_cli(
        [
            "--trust",
            "--env",
            f"CARETAKER_TEST_PIDFILE={pidfile}",
            "--json",
            str(missing),
            "--",
            *_server("bad_huge_input.py"),
        ]
    )
    assert code == 2
    assert stdout == ""
    assert not pidfile.exists()
    same = tmp_path / "same.json"
    code, _, _ = _run_cli(
        [
            "--trust",
            "--json",
            str(same),
            "--markdown",
            str(same),
            "--",
            *_server("clean_server.py"),
        ]
    )
    assert code == 2


def test_output_overwrite_and_write_failure(tmp_path: Path) -> None:
    target = tmp_path / "report.json"
    target.write_text("old contents", encoding="utf-8")
    code, _, _ = _run_cli(
        ["--trust", "--json", str(target), "--", *_server("clean_server.py")]
    )
    assert code == 0
    assert target.read_text(encoding="utf-8") != "old contents"
    code, stdout, _ = _run_cli(
        ["--trust", "--json", str(tmp_path), "--", *_server("clean_server.py")]
    )
    assert code == 2
    assert "Totals:" in stdout


@pytest.mark.parametrize(
    "options",
    [
        ["--env", "FOO"],
        ["--env", "=value"],
        ["--env", "CARETAKER_CANARY_TOKEN=x"],
        ["--startup-timeout", "0"],
        ["--startup-timeout", "-1"],
        ["--call-timeout", "abc"],
        ["--fail-on", "bogus"],
        ["--unknown-option"],
    ],
)
def test_bad_options_exit_2(options: list[str]) -> None:
    code, _, _ = _run_cli(["--trust", *options, "--", *_server("clean_server.py")])
    assert code == 2


def test_startup_and_call_timeouts() -> None:
    code, stdout, _ = _run_cli(
        [
            "--trust",
            "--startup-timeout",
            "1",
            "--",
            *_server("bad_hangs_on_startup.py"),
        ]
    )
    assert code == 1
    assert "[FAIL] CT-START-001 " in stdout
    code, stdout, _ = _run_cli(
        ["--trust", "--call-timeout", "1", "--", *_server("bad_huge_input.py")]
    )
    assert code == 1
    assert "fail=1" in stdout or "fail=2" in stdout or "fail=3" in stdout


def test_json_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    code, _, _ = _run_cli(
        ["--trust", "--json", str(first), "--", *_server("clean_server.py")]
    )
    assert code == 0
    code, _, _ = _run_cli(
        ["--trust", "--json", str(second), "--", *_server("clean_server.py")]
    )
    assert code == 0
    assert first.read_bytes() == second.read_bytes()


def test_nonexistent_program_exits_1(tmp_path: Path) -> None:
    missing = str(tmp_path / "no-such-program")
    code, stdout, _ = _run_cli(["--trust", "--", missing])
    assert code == 1
    assert "[FAIL] CT-START-001 " in stdout


def test_entry_point_metadata_and_direct_main(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'mcp-caretaker = "mcp_caretaker.cli:main"' in pyproject
    assert main([]) == 2
    assert main(["bogus"]) == 2
    assert main(["check", "--", "prog"]) == 2
    missing = str(tmp_path / "no-such-program")
    assert main(["check", "--trust", "--", missing]) == 1


def test_stderr_cap_counts_two_capped_scans() -> None:
    server = str(server_path("bad_canary_leaks.py"))
    script = (
        "import asyncio, sys\n"
        "from mcp_caretaker import run_checks, thresholds\n"
        "from mcp_caretaker.launch import LaunchSpec\n"
        "thresholds.STDERR_SCAN_MAX_BYTES = 64\n"
        "async def main():\n"
        f"    spec = LaunchSpec(argv=(sys.executable, {server!r}, 'stderr'), "
        "extra_env={'CARETAKER_STDERR_PADDING': '100'}, "
        "startup_timeout=5, call_timeout=5, shutdown_grace=1)\n"
        "    run = await run_checks(spec, confirmed=True)\n"
        "    print([r.summary for r in run.results "
        "if r.check_id == 'CT-CANARY-003'][0])\n"
        "asyncio.run(main())\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    output = completed.stdout.decode("utf-8", errors="replace")
    assert completed.returncode == 0
    assert "128 stderr bytes scanned across 2 session(s)" in output
    assert "Stderr cap of 64 bytes per session reached." in output


def test_fence_uses_longest_run_plus_one() -> None:
    assert fence("plain") == "```\nplain\n```"
    assert fence("a ``` b") == "````\na ``` b\n````"
    assert fence("a ````` b") == "``````\na ````` b\n``````"


def test_escape_ascii_covers_non_printable_and_non_ascii() -> None:
    assert escape_ascii("abc XYZ 123") == "abc XYZ 123"
    assert escape_ascii("a\x1bb") == "a\\u001Bb"
    assert escape_ascii("caf\u00e9") == "caf\\u00E9"
    assert escape_ascii("a\\b") == "a\\\\b"
    assert escape_ascii("a\nb") == "a\\u000Ab"
    assert all(ord(char) < 128 for char in escape_ascii("x\x1b\u00e9\U0001f600"))


def test_split_server_command_keeps_later_dashes() -> None:
    assert split_server_command(["--trust", "--", "prog", "--", "x"]) == (
        ["--trust"],
        ["prog", "--", "x"],
    )
    assert split_server_command(["--trust", "prog"]) is None
    assert split_server_command(["--"]) == ([], [])


def test_counts_to_exit_code_ignores_not_tested() -> None:
    assert (
        exit_code_for_counts(
            {"pass": 25, "warn": 0, "fail": 0, "not_tested": 0}, "fail"
        )
        == 0
    )
    assert (
        exit_code_for_counts(
            {"pass": 24, "warn": 1, "fail": 0, "not_tested": 0}, "fail"
        )
        == 0
    )
    assert (
        exit_code_for_counts(
            {"pass": 24, "warn": 1, "fail": 0, "not_tested": 0}, "warn"
        )
        == 1
    )
    assert (
        exit_code_for_counts(
            {"pass": 0, "warn": 0, "fail": 1, "not_tested": 24}, "fail"
        )
        == 1
    )
    assert (
        exit_code_for_counts(
            {"pass": 22, "warn": 0, "fail": 0, "not_tested": 3}, "warn"
        )
        == 0
    )


def test_program_name_handles_both_slash_styles() -> None:
    assert program_name("/usr/bin/python") == "python"
    assert program_name("C:\\tools\\python.exe") == "python.exe"
    assert program_name("python") == "python"


def test_report_dict_key_order_and_counts() -> None:
    run = RunResult(
        caretaker_version="0.0.0.dev0",
        protocol_version=None,
        server_name=None,
        server_version=None,
        results=(
            CheckResult("CT-START-001", "Title", Verdict.PASS, "ok"),
            CheckResult("CT-START-002", "Title", Verdict.WARN, "hmm"),
        ),
    )
    report = build_report_dict(run, "/a/b/prog", 2)
    assert list(report) == [
        "schema_version",
        "tool",
        "server",
        "protocol_version",
        "counts",
        "results",
    ]
    assert report["server"] == {"program": "prog", "argument_count": 2}
    assert report["counts"] == {"pass": 1, "warn": 1, "fail": 0, "not_tested": 0}


def test_terminal_prints_local_paths_without_doubling_backslashes() -> None:
    report = build_report_dict(
        RunResult(
            caretaker_version="0.0.0.dev0",
            protocol_version=None,
            server_name=None,
            server_version=None,
            results=(CheckResult("CT-START-001", "Title", Verdict.PASS, "ok"),),
        ),
        "C:\\tools\\python.exe",
        0,
    )
    text = render_terminal(report, "C:\\out\\report.json", "C:\\out\\report.md")
    assert "JSON: C:\\out\\report.json" in text
    assert "Markdown: C:\\out\\report.md" in text
    assert all(ord(char) < 128 for char in escape_ascii("caf\u00e9 \\ \x1b"))


def test_stderr_summary_names_two_sessions(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    code, _, _ = _run_cli(
        ["--trust", "--json", str(json_path), "--", *_server("clean_server.py")]
    )
    assert code == 0
    report = json.loads(json_path.read_text(encoding="utf-8"))
    summary = next(
        item["summary"]
        for item in report["results"]
        if item["check_id"] == "CT-CANARY-003"
    )
    assert "across 2 session(s)" in summary
    assert summary.endswith("no findings.")
    assert "Stderr cap of" not in summary


def test_stderr_summary_names_one_session_when_second_did_not_run(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "report.json"
    code, _, _ = _run_cli(
        [
            "--trust",
            "--json",
            str(json_path),
            "--",
            *_server("bad_tools_list_error.py"),
        ]
    )
    assert code == 1
    report = json.loads(json_path.read_text(encoding="utf-8"))
    summary = next(
        item["summary"]
        for item in report["results"]
        if item["check_id"] == "CT-CANARY-003"
    )
    assert "across 1 session(s)" in summary
    assert "no findings." in summary


def test_console_command_runs_clean_server(tmp_path: Path) -> None:
    command = _console_command()
    json_path = tmp_path / "report.json"
    completed = subprocess.run(
        [
            str(command),
            "check",
            "--trust",
            "--json",
            str(json_path),
            "--",
            *_server("clean_server.py"),
        ],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    assert completed.returncode == 0
    assert len(_check_lines(stdout)) == 25
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert sum(report["counts"].values()) == 25


def test_bare_and_unknown_invocations_print_usage_on_stderr_and_exit_2() -> None:
    for args in ([], ["check"], ["unknown-command"]):
        completed = subprocess.run(
            [sys.executable, "-m", "mcp_caretaker", *args],
            capture_output=True,
            timeout=TIMEOUT,
            check=False,
        )
        assert completed.returncode == 2
        assert completed.stdout == b""
        assert b"usage: mcp-caretaker check" in completed.stderr


def _assert_version_output(completed: subprocess.CompletedProcess[bytes]) -> str:
    """The version line is one stdout line and nothing else."""
    stdout = completed.stdout.decode("utf-8", errors="replace")
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert stdout.endswith("\n") and stdout.count("\n") == 1
    name, version = stdout.rstrip("\n").split(" ", 1)
    assert name == "mcp-caretaker"
    assert version == __version__
    return version


def test_version_flag_on_module_invocation() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "mcp_caretaker", "--version"],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    _assert_version_output(completed)


def test_version_flag_on_console_command() -> None:
    completed = subprocess.run(
        [str(_console_command()), "--version"],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    _assert_version_output(completed)


def test_version_matches_json_report(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    code, _, _ = _run_cli(
        ["--trust", "--json", str(json_path), "--", *_server("clean_server.py")]
    )
    assert code == 0
    report = json.loads(json_path.read_text(encoding="utf-8"))
    completed = subprocess.run(
        [sys.executable, "-m", "mcp_caretaker", "--version"],
        capture_output=True,
        timeout=TIMEOUT,
        check=False,
    )
    assert _assert_version_output(completed) == report["tool"]["version"]
