"""Behaviour tests for run_checks: every one starts a REAL subprocess."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import psutil
import pytest
from helpers import server_argv, server_path, wait_until

import mcp_caretaker.runner as runner_module
from mcp_caretaker import Verdict, run_checks
from mcp_caretaker.checks import CHECK_BY_ID, CHECK_IDS
from mcp_caretaker.errors import ConfirmationRequired
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.model import RunResult
from mcp_caretaker.thresholds import EVIDENCE_MAX_CHARS


def _spec(name: str, **kwargs: object) -> LaunchSpec:
    values: dict[str, object] = {
        "argv": server_argv(name),
        "startup_timeout": 10.0,
        "call_timeout": 5.0,
        "shutdown_grace": 0.5,
    }
    values.update(kwargs)
    return LaunchSpec(**values)


def _by_id(run: RunResult) -> dict[str, object]:
    return {result.check_id: result for result in run.results}


@pytest.mark.anyio
async def test_clean_server_passes_all_14_checks() -> None:
    run = await run_checks(_spec("clean_server.py", shutdown_grace=5.0), confirmed=True)
    assert len(run.results) == 14
    assert [result.verdict for result in run.results] == [Verdict.PASS] * 14


@pytest.mark.anyio
async def test_runner_results_are_ordered_and_have_one_result_per_id() -> None:
    run = await run_checks(_spec("bad_duplicate_names.py"), confirmed=True)
    assert [result.check_id for result in run.results] == list(CHECK_IDS)
    assert len({result.check_id for result in run.results}) == 14
    assert all(
        result.title == CHECK_BY_ID[result.check_id].title for result in run.results
    )
    assert not hasattr(run, "score")


@pytest.mark.anyio
async def test_negotiated_protocol_version_is_in_run_result_and_start_002_evidence() -> (
    None
):
    run = await run_checks(_spec("bad_empty_handshake.py"), confirmed=True)
    assert run.protocol_version
    start_002 = _by_id(run)["CT-START-002"]
    assert start_002.verdict is Verdict.WARN
    assert any(
        item.subject == "protocolVersion" and item.detail == run.protocol_version
        for item in start_002.evidence
    )


@pytest.mark.anyio
async def test_empty_handshake_warns_start_002_and_keeps_protocol_version() -> None:
    run = await run_checks(_spec("bad_empty_handshake.py"), confirmed=True)
    assert run.protocol_version
    assert _by_id(run)["CT-START-002"].verdict is Verdict.WARN
    assert run.server_name == ""
    assert run.server_version == ""


@pytest.mark.anyio
async def test_confirmation_required_propagates_before_spawn(tmp_path) -> None:
    marker = tmp_path / "marker.txt"
    code = "import pathlib, sys; pathlib.Path(sys.argv[1]).write_text('ran')"
    spec = LaunchSpec(argv=(sys.executable, "-c", code, str(marker)))
    with pytest.raises(ConfirmationRequired):
        await run_checks(spec, confirmed=False)
    assert not marker.exists()


@pytest.mark.anyio
async def test_run_checks_does_not_print_or_write_files(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    await run_checks(_spec("bad_duplicate_names.py"), confirmed=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.anyio
async def test_no_argv_in_run_result() -> None:
    run = await run_checks(_spec("clean_server.py", shutdown_grace=5.0), confirmed=True)
    text = json.dumps(run.to_dict())
    assert str(server_path("clean_server.py")) not in text
    assert sys.executable not in text


@pytest.mark.anyio
async def test_crashing_check_is_not_tested_with_reason_and_others_still_run(
    monkeypatch,
) -> None:
    fake = "FAKE-CRASH-VALUE-1234"

    def boom(_: object) -> None:
        raise ValueError("boom " + fake)

    monkeypatch.setitem(runner_module.DESCRIPTION_CHECK_FUNCTIONS, "CT-DESC-001", boom)
    run = await run_checks(
        _spec(
            "clean_server.py",
            shutdown_grace=5.0,
            extra_env={"CARETAKER_FAKE_TEXT": fake},
        ),
        confirmed=True,
    )
    by_id = _by_id(run)
    crash = by_id["CT-DESC-001"]
    assert crash.verdict is Verdict.NOT_TESTED
    assert crash.reason is not None
    assert crash.reason.startswith("internal error in check: ValueError: ")
    assert "[REDACTED:CARETAKER_FAKE_TEXT]" in crash.reason
    assert fake not in crash.reason
    assert by_id["CT-DESC-002"].verdict is Verdict.PASS
    assert by_id["CT-START-005"].verdict is Verdict.PASS


@pytest.mark.anyio
async def test_startup_exit_fails_start_001_and_everything_else_is_not_tested() -> None:
    run = await run_checks(
        _spec("bad_exits_immediately.py", startup_timeout=5.0, shutdown_grace=0.2),
        confirmed=True,
    )
    by_id = _by_id(run)
    assert by_id["CT-START-001"].verdict is Verdict.FAIL
    assert any(
        item.subject == "exit_code" and item.detail == "3"
        for item in by_id["CT-START-001"].evidence
    )
    others = [result for result in run.results if result.check_id != "CT-START-001"]
    assert len(others) == 13
    assert all(
        result.verdict is Verdict.NOT_TESTED and result.reason for result in others
    )
    assert not any(result.verdict is Verdict.PASS for result in others)


@pytest.mark.anyio
async def test_startup_hang_fails_start_001_and_everything_else_is_not_tested() -> None:
    run = await run_checks(
        _spec("bad_hangs_on_startup.py", startup_timeout=1.0, shutdown_grace=0.2),
        confirmed=True,
    )
    by_id = _by_id(run)
    assert by_id["CT-START-001"].verdict is Verdict.FAIL
    others = [result for result in run.results if result.check_id != "CT-START-001"]
    assert len(others) == 13
    assert all(
        result.verdict is Verdict.NOT_TESTED and result.reason for result in others
    )


@pytest.mark.anyio
async def test_bad_duplicate_names_fails_desc_003() -> None:
    run = await run_checks(_spec("bad_duplicate_names.py"), confirmed=True)
    result = _by_id(run)["CT-DESC-003"]
    assert result.verdict is Verdict.FAIL
    assert any(
        item.subject == "duplicate name" and "2 tools" in item.detail
        for item in result.evidence
    )


@pytest.mark.anyio
async def test_bad_hidden_characters_warns_desc_007() -> None:
    run = await run_checks(_spec("bad_hidden_characters.py"), confirmed=True)
    result = _by_id(run)["CT-DESC-007"]
    assert result.verdict is Verdict.WARN
    assert any(
        "U+200B" in item.detail or "U+202E" in item.detail for item in result.evidence
    )


@pytest.mark.anyio
async def test_paginated_tools_are_collected_and_flag_page_two_tool() -> None:
    run = await run_checks(_spec("paginated_server.py"), confirmed=True)
    by_id = _by_id(run)
    assert by_id["CT-START-003"].verdict is Verdict.PASS
    assert "2 tools across 2 pages" in by_id["CT-START-003"].summary
    result = by_id["CT-DESC-001"]
    assert result.verdict is Verdict.WARN
    assert any("page_two_tool" in item.subject for item in result.evidence)


@pytest.mark.anyio
async def test_bad_descriptions_warn_or_fail_expected_description_checks() -> None:
    run = await run_checks(_spec("bad_descriptions.py"), confirmed=True)
    by_id = _by_id(run)
    expected = {
        "CT-DESC-001": Verdict.WARN,
        "CT-DESC-002": Verdict.WARN,
        "CT-DESC-003": Verdict.FAIL,
        "CT-DESC-004": Verdict.FAIL,
        "CT-DESC-005": Verdict.WARN,
        "CT-DESC-006": Verdict.WARN,
        "CT-DESC-007": Verdict.WARN,
        "CT-DESC-008": Verdict.WARN,
        "CT-DESC-009": Verdict.WARN,
    }
    assert {check_id: by_id[check_id].verdict for check_id in expected} == expected


@pytest.mark.anyio
async def test_tools_list_error_fails_start_003_and_desc_checks_are_not_tested() -> (
    None
):
    run = await run_checks(_spec("bad_tools_list_error.py"), confirmed=True)
    by_id = _by_id(run)
    assert by_id["CT-START-003"].verdict is Verdict.FAIL
    for check_id in CHECK_IDS:
        if check_id.startswith("CT-DESC-"):
            assert by_id[check_id].verdict is Verdict.NOT_TESTED
            assert by_id[check_id].reason == "tools/list failed"
    assert by_id["CT-START-001"].verdict is Verdict.PASS
    assert by_id["CT-START-005"].verdict is Verdict.PASS


@pytest.mark.anyio
async def test_tools_list_page_cap_warns_start_003() -> None:
    run = await run_checks(_spec("bad_page_cap.py"), confirmed=True)
    result = _by_id(run)["CT-START-003"]
    assert result.verdict is Verdict.WARN
    assert "page cap" in result.summary
    assert any(item.subject == "page_cap" for item in result.evidence)


@pytest.mark.anyio
async def test_leaky_stdout_warns_start_004_and_cap_is_bounded() -> None:
    fake = "FAKE-LEAK-VALUE-123456"
    run = await run_checks(
        _spec("leaky_stdout.py", extra_env={"CARETAKER_FAKE_TEXT": fake}),
        confirmed=True,
    )
    result = _by_id(run)["CT-START-004"]
    assert result.verdict is Verdict.WARN
    assert any(
        item.subject == "count" and item.detail == "2" for item in result.evidence
    )
    cap = EVIDENCE_MAX_CHARS + len("...[truncated]")
    assert all(len(item.detail) <= cap for item in result.evidence)
    assert any("\\u0001" in item.detail for item in result.evidence)
    assert any(
        "[REDACTED:CARETAKER_FAKE_TEXT]" in item.detail for item in result.evidence
    )


@pytest.mark.anyio
async def test_evidence_redacts_extra_env_value() -> None:
    fake = "FAKE-LEAK-VALUE-123456"
    run = await run_checks(
        _spec("leaky_stdout.py", extra_env={"CARETAKER_FAKE_TEXT": fake}),
        confirmed=True,
    )
    text = json.dumps(run.to_dict())
    assert fake not in text
    assert "[REDACTED:CARETAKER_FAKE_TEXT]" in text
    details = [item.detail for item in _by_id(run)["CT-START-004"].evidence]
    assert any("\\u0001" in detail for detail in details)


@pytest.mark.anyio
async def test_server_that_ignores_stdin_close_warns_start_005_and_is_killed(
    tmp_path: Path,
) -> None:
    pidfile = tmp_path / "server.pid"
    run = await run_checks(
        _spec(
            "bad_ignores_stdin_close.py",
            shutdown_grace=0.2,
            extra_env={"CARETAKER_TEST_PIDFILE": str(pidfile)},
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-START-005"].verdict is Verdict.WARN
    assert pidfile.exists()
    pid = int(pidfile.read_text(encoding="utf-8"))

    def gone() -> bool:
        if not psutil.pid_exists(pid):
            return True
        try:
            return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
        except psutil.Error:
            return True

    assert await wait_until(gone, timeout=5.0)
