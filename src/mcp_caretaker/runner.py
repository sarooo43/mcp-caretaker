"""One library runner for the five check groups. No printing, no files."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import anyio

from . import __version__, canary, thresholds
from .checks import CANARY_IDS, CHECK_BY_ID, CHECKS, STABILITY_IDS
from .checks.description import DESCRIPTION_CHECK_FUNCTIONS
from .checks.robustness import ROBUSTNESS_IDS, run_robustness_checks
from .checks.stability import build_result, compare_lists
from .checks.startup import STARTUP_CHECK_FUNCTIONS, StartupContext
from .errors import ConfirmationRequired
from .launch import LaunchSpec
from .model import CheckResult, RunResult, Verdict, finalize_run_result
from .session import (
    ServerSession,
    _error_text,
    _exception_has_type,
    remove_temp_area,
)

CheckFunction = Callable[[Any], CheckResult]


def _not_tested(check_id: str, reason: str) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        title=CHECK_BY_ID[check_id].title,
        verdict=Verdict.NOT_TESTED,
        summary="Check was not tested.",
        evidence=(),
        reason=reason,
    )


def _is_cancelled(exc: BaseException) -> bool:
    return _exception_has_type(exc, anyio.get_cancelled_exc_class())


def _run_one(check_id: str, function: CheckFunction, argument: Any) -> CheckResult:
    try:
        return function(argument)
    except BaseException as exc:
        if _is_cancelled(exc):
            raise
        return _not_tested(
            check_id,
            f"internal error in check: {_error_text(exc)}",
        )


def _init_fields(session: ServerSession) -> tuple[str | None, str | None, str | None]:
    result = session.initialize_result
    protocol = getattr(result, "protocol_version", None)
    info = getattr(result, "server_info", None)
    name = getattr(info, "name", None)
    version = getattr(info, "version", None)
    return (
        str(protocol) if protocol is not None else None,
        str(name) if name is not None else None,
        str(version) if version is not None else None,
    )


def _flatten(pages: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    tools: list[dict[str, Any]] = []
    for page in pages:
        items = page.get("tools")
        if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items
        ):
            return None
        tools.extend(items)
    return tools


async def _scan_session_stderr(
    session: ServerSession, tracker: canary.CanaryTracker
) -> BaseException | None:
    cap_bytes = thresholds.STDERR_SCAN_MAX_BYTES
    before = session.read_stderr_prefix(cap_bytes)
    exit_error: BaseException | None = None
    try:
        await session.__aexit__(None, None, None)
    except BaseException as exc:
        if _is_cancelled(exc):
            raise
        exit_error = exc
    after = session.read_stderr_prefix(cap_bytes)
    canary.observe_session_stderr(
        tracker, before, after, session.stderr_text, cap_bytes
    )
    return exit_error


async def run_checks(spec: LaunchSpec, *, confirmed: bool) -> RunResult:
    """Run all 25 checks against one confirmed local server and return one result each."""
    if confirmed is not True:
        raise ConfirmationRequired("launching a server requires confirmed=True")
    canaries = canary.make_canary()
    run_spec = replace(spec, extra_env={**spec.extra_env, **canaries})
    redaction = canary.build_redaction_map(run_spec, canaries)
    tracker = canary.CanaryTracker(canaries, redaction)
    temp_area = Path(tempfile.mkdtemp(prefix="mcp-caretaker-"))
    session = ServerSession(
        run_spec,
        confirmed=True,
        temp_area=temp_area,
        stderr_name="stderr-1.log",
    )
    session.set_noise_observer(tracker.observe_stdout)
    results_by_id: dict[str, CheckResult] = {
        item.id: _not_tested(item.id, "check did not run") for item in CHECKS
    }
    protocol_version: str | None = None
    server_name: str | None = None
    server_version: str | None = None
    ctx = StartupContext()
    start_error: BaseException | None = None
    body_error: BaseException | None = None
    exit_error: BaseException | None = None
    first_tools: list[dict[str, Any]] | None = None
    first_tools_ok = False
    final_pages: tuple[dict[str, Any], ...] | None = None
    earlier_failure_reason: str | None = None

    try:
        try:
            await session.__aenter__()
        except BaseException as exc:
            if _is_cancelled(exc):
                raise
            start_error = exc

        if start_error is not None:
            ctx = replace(ctx, start_error=start_error)
            results_by_id["CT-START-001"] = _run_one(
                "CT-START-001",
                STARTUP_CHECK_FUNCTIONS["CT-START-001"],
                ctx,
            )
            for item in CHECKS:
                if item.id != "CT-START-001":
                    results_by_id[item.id] = _not_tested(
                        item.id, "server did not start"
                    )
            exit_error = await _scan_session_stderr(session, tracker)
        else:
            try:
                protocol_version, server_name, server_version = _init_fields(session)
                ctx = StartupContext(
                    protocol_version=protocol_version,
                    server_name=server_name,
                    server_version=server_version,
                )
                results_by_id["CT-START-001"] = _run_one(
                    "CT-START-001",
                    STARTUP_CHECK_FUNCTIONS["CT-START-001"],
                    ctx,
                )
                results_by_id["CT-START-002"] = _run_one(
                    "CT-START-002",
                    STARTUP_CHECK_FUNCTIONS["CT-START-002"],
                    ctx,
                )
                try:
                    pages, cap_hit, tools_error = await session.collect_tools_pages()
                except BaseException as exc:
                    if _is_cancelled(exc):
                        raise
                    pages, cap_hit, tools_error = [], False, _error_text(exc)
                first_tools = _flatten(pages)
                first_tools_ok = tools_error is None and first_tools is not None
                tracker.observe_first_connection(
                    session.raw_initialize_result, pages, tools_error
                )
                raw_tools = first_tools or []
                ctx = replace(
                    ctx,
                    tools_error=tools_error,
                    tool_count=len(raw_tools),
                    page_count=len(pages),
                    zero_tools=not raw_tools and tools_error is None,
                    pages_cap_hit=cap_hit,
                    stdout_noise_count=session.stdout_noise_count,
                    stdout_noise=tuple(session.stdout_noise),
                )
                results_by_id["CT-START-003"] = _run_one(
                    "CT-START-003",
                    STARTUP_CHECK_FUNCTIONS["CT-START-003"],
                    ctx,
                )
                failed = results_by_id["CT-START-003"].verdict in (
                    Verdict.FAIL,
                    Verdict.NOT_TESTED,
                )
                for check_id, function in DESCRIPTION_CHECK_FUNCTIONS.items():
                    if failed or tools_error is not None:
                        results_by_id[check_id] = _not_tested(
                            check_id, "tools/list failed"
                        )
                    else:
                        results_by_id[check_id] = _run_one(
                            check_id, function, raw_tools
                        )
                if failed or tools_error is not None:
                    for check_id in ROBUSTNESS_IDS:
                        results_by_id[check_id] = _not_tested(
                            check_id, "tools/list failed"
                        )
                    earlier_failure_reason = "tools/list failed"
                else:
                    try:
                        robustness_results, final_pages = await run_robustness_checks(
                            session,
                            raw_tools,
                            redaction,
                            answer_hook=tracker.observe_answer,
                        )
                        results_by_id.update(robustness_results)
                    except BaseException as exc:
                        if _is_cancelled(exc):
                            raise
                        reason = (
                            f"internal error in robustness checks: {_error_text(exc)}"
                        )
                        for check_id in ROBUSTNESS_IDS:
                            results_by_id[check_id] = _not_tested(check_id, reason)
                        earlier_failure_reason = reason
                    if any(
                        results_by_id[check_id].verdict
                        in (Verdict.FAIL, Verdict.NOT_TESTED)
                        for check_id in ROBUSTNESS_IDS
                    ):
                        earlier_failure_reason = "robustness checks did not complete"
                ctx = replace(
                    ctx,
                    stdout_noise_count=session.stdout_noise_count,
                    stdout_noise=tuple(session.stdout_noise),
                )
                results_by_id["CT-START-004"] = _run_one(
                    "CT-START-004",
                    STARTUP_CHECK_FUNCTIONS["CT-START-004"],
                    ctx,
                )
            except BaseException as exc:
                if _is_cancelled(exc):
                    raise
                body_error = exc
            finally:
                exit_error = await _scan_session_stderr(session, tracker)

            ctx = replace(
                ctx,
                exited_by_itself=session.exited_by_itself,
                exited_before_shutdown=session.exited_before_shutdown,
            )
            results_by_id["CT-START-005"] = _run_one(
                "CT-START-005",
                STARTUP_CHECK_FUNCTIONS["CT-START-005"],
                ctx,
            )
            try:
                results_by_id[CANARY_IDS[0]] = canary.build_answer_result(
                    tracker, earlier_failure_reason
                )
                results_by_id[CANARY_IDS[1]] = canary.build_first_connection_result(
                    tracker
                )
            except BaseException as exc:
                if _is_cancelled(exc):
                    raise
                reason = f"internal error in canary checks: {_error_text(exc)}"
                for check_id in CANARY_IDS[:2]:
                    results_by_id[check_id] = _not_tested(check_id, reason)

            try:
                if not first_tools_ok:
                    for check_id in STABILITY_IDS:
                        results_by_id[check_id] = _not_tested(
                            check_id, "first tools/list unavailable"
                        )
                    results_by_id[CANARY_IDS[2]] = canary.build_output_result(tracker)
                else:
                    second = ServerSession(
                        run_spec,
                        confirmed=True,
                        temp_area=temp_area,
                        stderr_name="stderr-2.log",
                    )
                    second.set_noise_observer(tracker.observe_stdout)
                    second_start_error: BaseException | None = None
                    second_list_error: BaseException | str | None = None
                    second_exit_error: BaseException | None = None
                    second_pages: list[dict[str, Any]] = []
                    try:
                        try:
                            await second.__aenter__()
                        except BaseException as exc:
                            if _is_cancelled(exc):
                                raise
                            second_start_error = exc
                        else:
                            try:
                                (
                                    second_pages,
                                    second_cap_hit,
                                    second_tools_error,
                                ) = await second.collect_tools_pages()
                                if second_tools_error is not None:
                                    second_list_error = second_tools_error
                                elif second_cap_hit:
                                    second_list_error = "tools/list page cap hit"
                            except BaseException as exc:
                                if _is_cancelled(exc):
                                    raise
                                second_list_error = exc
                    finally:
                        second_exit_error = await _scan_session_stderr(second, tracker)
                    results_by_id[CANARY_IDS[2]] = canary.build_output_result(tracker)

                    if second_start_error is not None:
                        results_by_id[STABILITY_IDS[0]] = build_result(
                            STABILITY_IDS[0],
                            Verdict.NOT_TESTED,
                            "Check was not tested.",
                            (
                                canary.error_evidence(
                                    "second session start",
                                    second_start_error,
                                    redaction,
                                ),
                            ),
                            "second session did not start",
                        )
                    elif second_list_error is not None:
                        results_by_id[STABILITY_IDS[0]] = build_result(
                            STABILITY_IDS[0],
                            Verdict.NOT_TESTED,
                            "Check was not tested.",
                            (
                                canary.error_evidence(
                                    "second tools/list",
                                    second_list_error,
                                    redaction,
                                ),
                            ),
                            "second tools/list failed",
                        )
                    elif second_exit_error is not None:
                        results_by_id[STABILITY_IDS[0]] = build_result(
                            STABILITY_IDS[0],
                            Verdict.NOT_TESTED,
                            "Check was not tested.",
                            (
                                canary.error_evidence(
                                    "second session cleanup",
                                    second_exit_error,
                                    redaction,
                                ),
                            ),
                            "second session cleanup failed",
                        )
                    else:
                        second_tools = _flatten(second_pages)
                        if second_tools is None:
                            results_by_id[STABILITY_IDS[0]] = build_result(
                                STABILITY_IDS[0],
                                Verdict.NOT_TESTED,
                                "Check was not tested.",
                                reason="second tools/list had no raw tool objects",
                            )
                        else:
                            verdict, summary, evidence = compare_lists(
                                first_tools or [], second_tools, redaction
                            )
                            results_by_id[STABILITY_IDS[0]] = build_result(
                                STABILITY_IDS[0], verdict, summary, evidence
                            )

                    if (
                        final_pages is None
                        or results_by_id["CT-ROB-006"].verdict is not Verdict.PASS
                    ):
                        results_by_id[STABILITY_IDS[1]] = build_result(
                            STABILITY_IDS[1],
                            Verdict.NOT_TESTED,
                            "Check was not tested.",
                            reason="final liveness tools/list unavailable",
                        )
                    else:
                        liveness_tools = _flatten(list(final_pages))
                        if liveness_tools is None:
                            results_by_id[STABILITY_IDS[1]] = build_result(
                                STABILITY_IDS[1],
                                Verdict.NOT_TESTED,
                                "Check was not tested.",
                                reason="final liveness tools/list had no raw tool objects",
                            )
                        else:
                            verdict, summary, evidence = compare_lists(
                                first_tools or [], liveness_tools, redaction
                            )
                            results_by_id[STABILITY_IDS[1]] = build_result(
                                STABILITY_IDS[1], verdict, summary, evidence
                            )
            except BaseException as exc:
                if _is_cancelled(exc):
                    raise
                reason = f"internal error in stability checks: {_error_text(exc)}"
                for check_id in STABILITY_IDS:
                    results_by_id[check_id] = _not_tested(check_id, reason)
                if results_by_id[CANARY_IDS[2]].reason == "check did not run":
                    results_by_id[CANARY_IDS[2]] = _not_tested(CANARY_IDS[2], reason)

            error = body_error or exit_error
            if error is not None:
                reason = f"internal error in runner: {_error_text(error)}"
                for item in CHECKS:
                    if results_by_id[item.id].reason == "check did not run":
                        results_by_id[item.id] = _not_tested(item.id, reason)
    finally:
        await remove_temp_area(temp_area)

    run = RunResult(
        caretaker_version=__version__,
        protocol_version=protocol_version,
        server_name=server_name,
        server_version=server_version,
        results=tuple(results_by_id[item.id] for item in CHECKS),
    )
    return finalize_run_result(run, redaction)
