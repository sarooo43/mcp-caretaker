"""One library runner for the first two check groups. No printing, no files."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import anyio

from . import __version__
from .checks import CHECK_BY_ID, CHECKS
from .checks.description import DESCRIPTION_CHECK_FUNCTIONS
from .checks.startup import STARTUP_CHECK_FUNCTIONS, StartupContext
from .launch import LaunchSpec
from .model import (
    CheckResult,
    RunResult,
    Verdict,
    finalize_run_result,
)
from .session import ServerSession, _error_text, _exception_has_type

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


async def run_checks(spec: LaunchSpec, *, confirmed: bool) -> RunResult:
    """Run all 14 checks against one confirmed local server and return one result each."""
    session = ServerSession(spec, confirmed=confirmed)
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
                results_by_id[item.id] = _not_tested(item.id, "server did not start")
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
            raw_tools: list[dict[str, Any]] = []
            for page in pages:
                for tool in page.get("tools", []):
                    if isinstance(tool, dict):
                        raw_tools.append(tool)
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
                    results_by_id[check_id] = _not_tested(check_id, "tools/list failed")
                else:
                    results_by_id[check_id] = _run_one(check_id, function, raw_tools)
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
            try:
                await session.__aexit__(None, None, None)
            except BaseException as exc:
                if _is_cancelled(exc):
                    raise
                exit_error = exc

        ctx = replace(ctx, exited_by_itself=session.exited_by_itself)
        results_by_id["CT-START-005"] = _run_one(
            "CT-START-005",
            STARTUP_CHECK_FUNCTIONS["CT-START-005"],
            ctx,
        )
        error = body_error or exit_error
        if error is not None:
            reason = f"internal error in runner: {_error_text(error)}"
            for item in CHECKS:
                if results_by_id[item.id].reason == "check did not run":
                    results_by_id[item.id] = _not_tested(item.id, reason)

    run = RunResult(
        caretaker_version=__version__,
        protocol_version=protocol_version,
        server_name=server_name,
        server_version=server_version,
        results=tuple(results_by_id[item.id] for item in CHECKS),
    )
    return finalize_run_result(run, spec.extra_env)
