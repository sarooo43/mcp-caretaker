"""Behaviour tests: every canary and stability case starts a REAL subprocess."""

from __future__ import annotations

import base64
import json
from typing import Any

import pytest
from helpers import server_argv

import mcp_caretaker.canary as canary_module
from mcp_caretaker import Verdict, run_checks, thresholds
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.model import RunResult

FIXED = {
    "CARETAKER_CANARY_API_KEY": "ct_canary_FAKE_API_KEY_0123456789abcdef",
    "CARETAKER_CANARY_TOKEN": "ct_canary_FAKE_TOKEN_0123456789abcdef",
    "CARETAKER_CANARY_SECRET": "ct_canary_FAKE_SECRET_0123456789abcdef",
}
BASE64_VALUES = tuple(
    base64.b64encode(value.encode("ascii")).decode("ascii") for value in FIXED.values()
)


@pytest.fixture(autouse=True)
def fixed_canary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(canary_module, "make_canary", lambda: dict(FIXED))


def _spec(name: str, *args: str, **kwargs: object) -> LaunchSpec:
    values: dict[str, object] = {
        "argv": server_argv(name, *args),
        "startup_timeout": 5,
        "call_timeout": 5,
        "shutdown_grace": 1,
    }
    values.update(kwargs)
    return LaunchSpec(**values)


def _by_id(run: RunResult) -> dict[str, Any]:
    return {result.check_id: result for result in run.results}


def _assert_no_canary_text(run: RunResult) -> None:
    text = json.dumps(run.to_dict())
    assert all(value not in text for value in FIXED.values())
    assert all(value not in text for value in BASE64_VALUES)


@pytest.mark.parametrize(
    ("mode", "check_id", "verdict", "subject"),
    [
        pytest.param(
            "result_text",
            "CT-CANARY-001",
            Verdict.FAIL,
            "tools/call answer",
            id="result-text-fails-canary-001",
        ),
        pytest.param(
            "error_result",
            "CT-CANARY-001",
            Verdict.FAIL,
            "tools/call answer",
            id="error-result-fails-canary-001",
        ),
        pytest.param(
            "rpc_error",
            "CT-CANARY-001",
            Verdict.FAIL,
            "tools/call answer",
            id="rpc-error-fails-canary-001",
        ),
        pytest.param(
            "tool_description",
            "CT-CANARY-002",
            Verdict.FAIL,
            "tools/list page 1",
            id="tool-description-fails-canary-002",
        ),
        pytest.param(
            "server_name",
            "CT-CANARY-002",
            Verdict.FAIL,
            "initialize serverInfo",
            id="server-name-fails-canary-002",
        ),
        pytest.param(
            "stderr",
            "CT-CANARY-003",
            Verdict.WARN,
            "stderr",
            id="stderr-warns-canary-003",
        ),
        pytest.param(
            "stdout",
            "CT-CANARY-003",
            Verdict.WARN,
            "stdout",
            id="stdout-warns-canary-003",
        ),
        pytest.param(
            "base64_result",
            "CT-CANARY-001",
            Verdict.FAIL,
            "tools/call answer",
            id="base64-result-fails-canary-001",
        ),
    ],
)
@pytest.mark.anyio
async def test_bad_canary_leaks_modes(
    mode: str, check_id: str, verdict: Verdict, subject: str
) -> None:
    run = await run_checks(_spec("bad_canary_leaks.py", mode), confirmed=True)
    result = _by_id(run)[check_id]
    assert result.verdict is verdict
    assert any(item.subject == subject for item in result.evidence)
    if mode == "base64_result":
        assert any("base64" in item.detail for item in result.evidence)
    _assert_no_canary_text(run)


@pytest.mark.anyio
async def test_clean_server_passes_canary_checks_with_answers_scanned() -> None:
    run = await run_checks(_spec("clean_server.py", shutdown_grace=5), confirmed=True)
    by_id = _by_id(run)
    assert len(run.results) == 25
    assert all(result.verdict is Verdict.PASS for result in run.results)
    for check_id in ("CT-CANARY-001", "CT-CANARY-002", "CT-CANARY-003"):
        assert by_id[check_id].verdict is Verdict.PASS
    assert "tools/call answers scanned" in by_id["CT-CANARY-001"].summary
    _assert_no_canary_text(run)


@pytest.mark.anyio
async def test_zero_tools_makes_canary_001_not_tested() -> None:
    run = await run_checks(
        _spec(
            "bad_tools_list_error.py",
            extra_env={"CARETAKER_TEST_ZERO_TOOLS": "1"},
        ),
        confirmed=True,
    )
    result = _by_id(run)["CT-CANARY-001"]
    assert result.verdict is Verdict.NOT_TESTED
    assert result.reason is not None
    _assert_no_canary_text(run)


@pytest.mark.anyio
async def test_reason_counts_not_tested_robustness_checks_and_answers() -> None:
    run = await run_checks(_spec("bad_valid_call_mixed.py"), confirmed=True)
    result = _by_id(run)["CT-CANARY-001"]
    assert result.verdict is Verdict.NOT_TESTED
    assert result.reason == (
        "robustness checks: 0 failed, 2 not tested; 6 tools/call answers were scanned"
    )
    _assert_no_canary_text(run)


@pytest.mark.anyio
async def test_reason_counts_failed_robustness_checks_and_answers() -> None:
    run = await run_checks(_spec("bad_dies_after_probes.py"), confirmed=True)
    result = _by_id(run)["CT-CANARY-001"]
    assert result.verdict is Verdict.NOT_TESTED
    assert result.reason == (
        "robustness checks: 1 failed, 0 not tested; 5 tools/call answers were scanned"
    )
    _assert_no_canary_text(run)


@pytest.mark.anyio
async def test_stderr_cap_hides_later_value_and_reports_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cap = 64
    monkeypatch.setattr(thresholds, "STDERR_SCAN_MAX_BYTES", cap)
    run = await run_checks(
        _spec(
            "bad_canary_leaks.py",
            "stderr",
            extra_env={"CARETAKER_STDERR_PADDING": "100"},
        ),
        confirmed=True,
    )
    result = _by_id(run)["CT-CANARY-003"]
    assert result.verdict is Verdict.PASS
    assert f"{2 * cap} stderr bytes scanned" in result.summary
    assert not result.evidence
    _assert_no_canary_text(run)


@pytest.mark.anyio
async def test_second_start_failure_makes_stab_001_not_tested() -> None:
    run = await run_checks(
        _spec(
            "bad_rug_pull.py",
            "reconnect_description",
            extra_env={"CARETAKER_TEST_SECOND_START_FAIL": "1"},
        ),
        confirmed=True,
    )
    result = _by_id(run)["CT-STAB-001"]
    assert result.verdict is Verdict.NOT_TESTED
    assert result.reason is not None
    assert any(
        item.subject == "second session start" and "exit code 7" in item.detail
        for item in result.evidence
    )
    _assert_no_canary_text(run)


@pytest.mark.parametrize(
    ("mode", "check_id", "verdict", "subject"),
    [
        pytest.param(
            "reconnect_description",
            "CT-STAB-001",
            Verdict.FAIL,
            "echo",
            id="reconnect-description-fails-stab-001",
        ),
        pytest.param(
            "after_calls_description",
            "CT-STAB-002",
            Verdict.FAIL,
            "echo",
            id="after-calls-description-fails-stab-002",
        ),
        pytest.param(
            "after_calls_input_schema",
            "CT-STAB-002",
            Verdict.FAIL,
            "echo",
            id="after-calls-input-schema-fails-stab-002",
        ),
        pytest.param(
            "after_calls_annotation",
            "CT-STAB-002",
            Verdict.FAIL,
            "echo",
            id="after-calls-annotation-fails-stab-002",
        ),
        pytest.param(
            "after_calls_title",
            "CT-STAB-002",
            Verdict.FAIL,
            "echo",
            id="after-calls-title-fails-stab-002",
        ),
        pytest.param(
            "after_calls_output_schema",
            "CT-STAB-002",
            Verdict.FAIL,
            "echo",
            id="after-calls-output-schema-fails-stab-002",
        ),
        pytest.param(
            "added_tool",
            "CT-STAB-002",
            Verdict.WARN,
            "extra",
            id="added-tool-warns-stab-002",
        ),
        pytest.param(
            "removed_tool",
            "CT-STAB-002",
            Verdict.WARN,
            "writer",
            id="removed-tool-warns-stab-002",
        ),
        pytest.param(
            "reordered",
            "CT-STAB-002",
            Verdict.PASS,
            None,
            id="reordered-passes-stab-002",
        ),
    ],
)
@pytest.mark.anyio
async def test_bad_rug_pull_modes(
    mode: str, check_id: str, verdict: Verdict, subject: str | None
) -> None:
    run = await run_checks(_spec("bad_rug_pull.py", mode), confirmed=True)
    result = _by_id(run)[check_id]
    assert result.verdict is verdict
    if subject is None:
        assert not result.evidence
    else:
        assert any(item.subject == subject for item in result.evidence)
    _assert_no_canary_text(run)
