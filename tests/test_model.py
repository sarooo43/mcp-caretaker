"""Pure unit tests for the frozen result model, registry and thresholds."""

from __future__ import annotations

import inspect
import json
import tomllib
from pathlib import Path

import pytest

from mcp_caretaker import CheckResult, Evidence, RunResult, Verdict, run_checks
from mcp_caretaker.checks import CHECK_IDS, CHECKS
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.model import finalize_result, visible_text
from mcp_caretaker.thresholds import (
    DESC_MAX_LENGTH,
    DESC_MIN_LENGTH,
    EVIDENCE_MAX_CHARS,
    EVIDENCE_MAX_ITEMS,
    MAX_TOOLS_PAGES,
    SHUTDOWN_GRACE_SECONDS,
    WHITESPACE_RUN_LIMIT,
)

ROOT = Path(__file__).resolve().parents[1]


def test_verdict_values_are_exactly_four_strings() -> None:
    assert [item.value for item in Verdict] == ["pass", "warn", "fail", "not_tested"]


def test_check_registry_has_14_unique_ids_in_order() -> None:
    assert CHECK_IDS == (
        "CT-START-001",
        "CT-START-002",
        "CT-START-003",
        "CT-START-004",
        "CT-START-005",
        "CT-DESC-001",
        "CT-DESC-002",
        "CT-DESC-003",
        "CT-DESC-004",
        "CT-DESC-005",
        "CT-DESC-006",
        "CT-DESC-007",
        "CT-DESC-008",
        "CT-DESC-009",
    )
    assert len(set(CHECK_IDS)) == len(CHECKS) == 14
    assert all(info.docs_path.startswith("docs/checks/") for info in CHECKS)


def test_run_checks_signature_is_spec_and_keyword_only_confirmed() -> None:
    parameters = inspect.signature(run_checks).parameters
    assert list(parameters) == ["spec", "confirmed"]
    assert parameters["confirmed"].kind is inspect.Parameter.KEYWORD_ONLY


def test_run_result_to_dict_is_json_serialisable_and_has_no_score() -> None:
    result = CheckResult(
        check_id="CT-DESC-001",
        title="Every tool has a description",
        verdict=Verdict.PASS,
        summary="0 of 1 tools have no description.",
        evidence=(Evidence("subject", "detail"),),
    )
    run = RunResult(
        caretaker_version="0.0.0.dev0",
        protocol_version="test-protocol",
        server_name="test-server",
        server_version="1.0",
        results=(result,),
    )
    data = run.to_dict()
    assert json.loads(json.dumps(data))["results"][0]["verdict"] == "pass"
    assert "score" not in data
    assert "grade" not in data


def test_visible_text_escapes_non_printables() -> None:
    assert visible_text("a\u200b\n\t") == "a\\u200B\\u000A\\u0009"


def test_evidence_is_redacted_escaped_capped_and_omits_extra_items() -> None:
    secret = "FAKE-EVIDENCE-VALUE-1234"
    long_detail = ("before " + secret + " \u200b " + "X" * 400).strip()
    original = CheckResult(
        check_id="CT-DESC-001",
        title="Every tool has a description",
        verdict=Verdict.WARN,
        summary="summary contains " + secret,
        evidence=tuple(
            Evidence(f"tool {index}", long_detail)
            for index in range(EVIDENCE_MAX_ITEMS + 5)
        ),
    )
    result = finalize_result(original, {"CARETAKER_FAKE_TEXT": secret})
    assert len(result.evidence) == EVIDENCE_MAX_ITEMS + 1
    assert result.evidence[-1].detail == "5 more not shown"
    assert secret not in result.summary
    assert "[REDACTED:CARETAKER_FAKE_TEXT]" in result.summary
    assert secret not in result.evidence[0].detail
    assert "\\u200B" in result.evidence[0].detail
    assert result.evidence[0].detail.endswith("...[truncated]")
    assert len(result.evidence[0].detail) == EVIDENCE_MAX_CHARS + len("...[truncated]")


def test_not_tested_result_keeps_reason_and_is_not_pass() -> None:
    result = finalize_result(
        CheckResult(
            check_id="CT-START-005",
            title="Server exits after input is closed",
            verdict=Verdict.NOT_TESTED,
            summary="Check was not tested.",
            reason="session did not start or outcome is unknown",
        ),
        {},
    )
    assert result.verdict is Verdict.NOT_TESTED
    assert result.verdict.value != "pass"
    assert result.reason is not None


def test_threshold_constants_have_expected_values_and_comments() -> None:
    assert (DESC_MIN_LENGTH, DESC_MAX_LENGTH) == (10, 1000)
    assert WHITESPACE_RUN_LIMIT == 40
    assert MAX_TOOLS_PAGES == 10
    assert (EVIDENCE_MAX_ITEMS, EVIDENCE_MAX_CHARS) == (20, 300)
    assert SHUTDOWN_GRACE_SECONDS == 5
    source = (ROOT / "src/mcp_caretaker/thresholds.py").read_text(encoding="utf-8")
    assert source.count("Guessed") >= 7


def test_pyproject_runtime_dependencies_are_unchanged() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    assert data["project"]["dependencies"] == ["mcp==2.3.0", "mcp-types==2.3.0"]


def test_shutdown_grace_default_and_validation() -> None:
    spec = LaunchSpec(argv=("python", "-V"))
    assert spec.shutdown_grace == SHUTDOWN_GRACE_SECONDS
    with pytest.raises(ValueError):
        LaunchSpec(argv=("python", "-V"), shutdown_grace=0)
