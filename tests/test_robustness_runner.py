"""Behaviour tests for robustness checks; every one starts a REAL subprocess."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import psutil
import pytest
from helpers import server_argv, wait_until

from mcp_caretaker import Verdict, run_checks, thresholds
from mcp_caretaker.checks.robustness import ROBUSTNESS_IDS, UNKNOWN_TOOL_NAME
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.model import CheckResult, RunResult


def _spec(name: str, **kwargs: object) -> LaunchSpec:
    values: dict[str, object] = {
        "argv": server_argv(name),
        "startup_timeout": 2,
        "call_timeout": 2,
        "shutdown_grace": 2,
    }
    values.update(kwargs)
    return LaunchSpec(**values)


def _by_id(run: RunResult) -> dict[str, CheckResult]:
    return {result.check_id: result for result in run.results}


def _read_calls(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _gone(pid: int) -> bool:
    if not psutil.pid_exists(pid):
        return True
    try:
        return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
    except psutil.Error:
        return True


@pytest.mark.anyio
async def test_writer_tool_gets_only_invalid_input(tmp_path: Path) -> None:
    log = tmp_path / "calls.jsonl"
    await run_checks(
        _spec(
            "recording_server.py",
            extra_env={"CARETAKER_TEST_CALLLOG": str(log)},
        ),
        confirmed=True,
    )
    writer_calls = [call for call in _read_calls(log) if call["tool"] == "writer"]
    assert writer_calls
    for call in writer_calls:
        assert all(arg["type"] != "str" for arg in call["args"].values())
        assert not any(
            arg["length"] is not None and arg["length"] > 1000
            for arg in call["args"].values()
        )


@pytest.mark.anyio
async def test_read_only_tool_gets_huge_and_valid_calls(tmp_path: Path) -> None:
    log = tmp_path / "calls.jsonl"
    await run_checks(
        _spec(
            "recording_server.py",
            extra_env={"CARETAKER_TEST_CALLLOG": str(log)},
        ),
        confirmed=True,
    )
    reader_lengths = [
        arg["length"]
        for call in _read_calls(log)
        if call["tool"] == "reader"
        for arg in call["args"].values()
        if arg["type"] == "str"
    ]
    assert thresholds.HUGE_STRING_LENGTH in reader_lengths
    assert 1 in reader_lengths


@pytest.mark.anyio
async def test_unknown_tool_probe_is_sent_exactly_once(tmp_path: Path) -> None:
    log = tmp_path / "calls.jsonl"
    await run_checks(
        _spec(
            "recording_server.py",
            extra_env={"CARETAKER_TEST_CALLLOG": str(log)},
        ),
        confirmed=True,
    )
    assert sum(call["tool"] == UNKNOWN_TOOL_NAME for call in _read_calls(log)) == 1


@pytest.mark.anyio
async def test_only_writers_server_has_huge_and_valid_not_tested() -> None:
    run = await run_checks(_spec("only_writers_server.py"), confirmed=True)
    by_id = _by_id(run)
    assert by_id["CT-ROB-004"].verdict is Verdict.NOT_TESTED
    assert by_id["CT-ROB-005"].verdict is Verdict.NOT_TESTED


@pytest.mark.anyio
async def test_complex_schema_is_not_tested_for_valid_call() -> None:
    run = await run_checks(_spec("complex_schema_server.py"), confirmed=True)
    assert _by_id(run)["CT-ROB-005"].verdict is Verdict.NOT_TESTED


@pytest.mark.anyio
async def test_wrong_type_accepted_warns_rob_001() -> None:
    run = await run_checks(_spec("bad_wrong_type.py"), confirmed=True)
    assert _by_id(run)["CT-ROB-001"].verdict is Verdict.WARN


@pytest.mark.anyio
async def test_wrong_type_crash_fails_rob_001() -> None:
    run = await run_checks(
        _spec(
            "bad_wrong_type.py",
            extra_env={"CARETAKER_TEST_MODE": "crash"},
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-ROB-001"].verdict is Verdict.FAIL


@pytest.mark.anyio
async def test_wrong_type_hang_fails_rob_001_and_stops_probing(
    tmp_path: Path,
) -> None:
    log = tmp_path / "calls.jsonl"
    pidfile = tmp_path / "server.pid"
    run = await run_checks(
        _spec(
            "bad_wrong_type.py",
            extra_env={
                "CARETAKER_TEST_MODE": "hang",
                "CARETAKER_TEST_CALLLOG": str(log),
                "CARETAKER_TEST_PIDFILE": str(pidfile),
            },
        ),
        confirmed=True,
    )
    by_id = _by_id(run)
    assert by_id["CT-ROB-001"].verdict is Verdict.FAIL
    assert by_id["CT-ROB-006"].verdict is Verdict.FAIL
    calls = _read_calls(log)
    assert len(calls) == 1
    assert calls[0]["tool"] == "string_tool"
    pid = int(pidfile.read_text(encoding="utf-8"))
    assert await wait_until(lambda: _gone(pid), timeout=5.0)


@pytest.mark.anyio
async def test_missing_required_accepted_warns_rob_002() -> None:
    run = await run_checks(_spec("bad_missing_required.py"), confirmed=True)
    assert _by_id(run)["CT-ROB-002"].verdict is Verdict.WARN


@pytest.mark.anyio
async def test_missing_required_crash_fails_rob_002() -> None:
    run = await run_checks(
        _spec(
            "bad_missing_required.py",
            extra_env={"CARETAKER_TEST_MODE": "crash"},
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-ROB-002"].verdict is Verdict.FAIL


@pytest.mark.anyio
async def test_unknown_tool_accepted_warns_rob_003() -> None:
    run = await run_checks(_spec("bad_unknown_tool.py"), confirmed=True)
    assert _by_id(run)["CT-ROB-003"].verdict is Verdict.WARN


@pytest.mark.anyio
async def test_unknown_tool_crash_fails_rob_003() -> None:
    run = await run_checks(
        _spec(
            "bad_unknown_tool.py",
            extra_env={"CARETAKER_TEST_MODE": "crash"},
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-ROB-003"].verdict is Verdict.FAIL


@pytest.mark.anyio
async def test_huge_input_slow_warns_rob_004(tmp_path: Path) -> None:
    pidfile = tmp_path / "server.pid"
    run = await run_checks(
        _spec(
            "bad_huge_input.py",
            extra_env={
                "CARETAKER_TEST_MODE": "slow",
                "CARETAKER_TEST_PIDFILE": str(pidfile),
            },
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-ROB-004"].verdict is Verdict.WARN
    pid = int(pidfile.read_text(encoding="utf-8"))
    assert await wait_until(lambda: _gone(pid), timeout=5.0)


@pytest.mark.anyio
async def test_huge_input_crash_fails_rob_004() -> None:
    run = await run_checks(
        _spec(
            "bad_huge_input.py",
            extra_env={"CARETAKER_TEST_MODE": "crash"},
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-ROB-004"].verdict is Verdict.FAIL


@pytest.mark.anyio
async def test_valid_call_error_result_warns_rob_005() -> None:
    run = await run_checks(_spec("bad_valid_call.py"), confirmed=True)
    assert _by_id(run)["CT-ROB-005"].verdict is Verdict.WARN


@pytest.mark.anyio
async def test_valid_call_crash_fails_rob_005() -> None:
    run = await run_checks(
        _spec(
            "bad_valid_call.py",
            extra_env={"CARETAKER_TEST_MODE": "crash"},
        ),
        confirmed=True,
    )
    assert _by_id(run)["CT-ROB-005"].verdict is Verdict.FAIL


@pytest.mark.anyio
async def test_server_dies_after_probes_fails_rob_006() -> None:
    run = await run_checks(_spec("bad_dies_after_probes.py"), confirmed=True)
    by_id = _by_id(run)
    assert by_id["CT-ROB-006"].verdict is Verdict.FAIL
    assert by_id["CT-START-005"].verdict is Verdict.NOT_TESTED


@pytest.mark.anyio
async def test_zero_tools_runs_only_rob_003_and_rob_006() -> None:
    run = await run_checks(
        _spec(
            "bad_tools_list_error.py",
            extra_env={"CARETAKER_TEST_ZERO_TOOLS": "1"},
        ),
        confirmed=True,
    )
    by_id = _by_id(run)
    assert by_id["CT-ROB-003"].verdict is Verdict.PASS
    assert by_id["CT-ROB-006"].verdict is Verdict.PASS
    for check_id in ROBUSTNESS_IDS:
        if check_id not in ("CT-ROB-003", "CT-ROB-006"):
            assert by_id[check_id].verdict is Verdict.NOT_TESTED


@pytest.mark.anyio
async def test_tool_cap_marks_remaining_tools_not_tested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(thresholds, "MAX_TOOLS_PROBED", 1)
    run = await run_checks(_spec("recording_server.py"), confirmed=True)
    by_id = _by_id(run)
    for check_id in ("CT-ROB-001", "CT-ROB-002", "CT-ROB-004", "CT-ROB-005"):
        assert by_id[check_id].verdict is Verdict.NOT_TESTED
        assert by_id[check_id].reason == "tool cap reached"
    assert by_id["CT-ROB-003"].verdict is Verdict.PASS
    assert by_id["CT-ROB-006"].verdict is Verdict.PASS


@pytest.mark.anyio
async def test_probe_budget_exhausted_marks_rest_not_tested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(thresholds, "PROBE_BUDGET_SECONDS", 0)
    run = await run_checks(_spec("recording_server.py"), confirmed=True)
    by_id = _by_id(run)
    for check_id in ROBUSTNESS_IDS:
        assert by_id[check_id].verdict is Verdict.NOT_TESTED
        assert by_id[check_id].reason == "probe budget exhausted"


@pytest.mark.anyio
async def test_failing_probe_has_replay_line() -> None:
    run = await run_checks(_spec("bad_wrong_type.py"), confirmed=True)
    result = _by_id(run)["CT-ROB-001"]
    assert result.verdict is Verdict.WARN
    replays = [item.replay for item in result.evidence if item.replay]
    assert replays
    line = json.loads(replays[0])
    assert line["id"] == 1
    assert line["method"] == "tools/call"
    passed = [
        evidence
        for item in run.results
        if item.verdict is Verdict.PASS
        for evidence in item.evidence
    ]
    assert all(evidence.replay is None for evidence in passed)


@pytest.mark.anyio
async def test_probe_evidence_redacts_extra_env_value() -> None:
    fake = "FAKE-ROBUSTNESS-VALUE-1234"
    run = await run_checks(
        _spec(
            "recording_server.py",
            extra_env={"CARETAKER_FAKE_TEXT": fake},
        ),
        confirmed=True,
    )
    text = json.dumps(run.to_dict())
    assert fake not in text
    assert "[REDACTED:CARETAKER_FAKE_TEXT]" in text
    rob_evidence = [
        evidence
        for item in run.results
        if item.check_id.startswith("CT-ROB-")
        for evidence in item.evidence
    ]
    assert any(
        "[REDACTED:CARETAKER_FAKE_TEXT]" in evidence.detail for evidence in rob_evidence
    )
