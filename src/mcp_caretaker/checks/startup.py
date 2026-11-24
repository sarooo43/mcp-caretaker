"""Startup check functions. They are pure functions over a small context."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..errors import ServerExited, StartupTimeout
from ..model import CheckResult, Evidence, Verdict
from . import CHECK_BY_ID


@dataclass(frozen=True)
class StartupContext:
    start_error: BaseException | None = None
    protocol_version: str | None = None
    server_name: str | None = None
    server_version: str | None = None
    tools_error: str | None = None
    tool_count: int = 0
    page_count: int = 0
    zero_tools: bool = False
    pages_cap_hit: bool = False
    stdout_noise_count: int = 0
    stdout_noise: tuple[str, ...] = ()
    exited_by_itself: bool | None = None
    exited_before_shutdown: bool = False


def _make(
    check_id: str,
    verdict: Verdict,
    summary: str,
    evidence: tuple[Evidence, ...] = (),
    reason: str | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        title=CHECK_BY_ID[check_id].title,
        verdict=verdict,
        summary=summary,
        evidence=evidence,
        reason=reason,
    )


def check_start_001(ctx: StartupContext) -> CheckResult:
    error = ctx.start_error
    if isinstance(error, ServerExited):
        return _make(
            "CT-START-001",
            Verdict.FAIL,
            f"Server exited before handshake; exit code {error.exit_code}.",
            (
                Evidence("exit_code", str(error.exit_code)),
                Evidence("stderr_tail", error.stderr_tail),
            ),
        )
    if isinstance(error, StartupTimeout):
        return _make(
            "CT-START-001",
            Verdict.FAIL,
            "Handshake exceeded startup timeout.",
            (Evidence("timeout", str(error)),),
        )
    if error is not None:
        return _make(
            "CT-START-001",
            Verdict.FAIL,
            "Server did not start.",
            (Evidence("error", f"{type(error).__name__}: {error}"),),
        )
    return _make(
        "CT-START-001",
        Verdict.PASS,
        "Server started and completed the handshake.",
    )


def check_start_002(ctx: StartupContext) -> CheckResult:
    protocol = ctx.protocol_version or ""
    name = ctx.server_name or ""
    version = ctx.server_version or ""
    evidence = (
        Evidence("protocolVersion", protocol),
        Evidence("serverInfo.name", name),
        Evidence("serverInfo.version", version),
    )
    empty = sum(1 for value in (name, version) if not value)
    if empty:
        return _make(
            "CT-START-002",
            Verdict.WARN,
            f"{empty} of 2 handshake fields are empty.",
            evidence,
        )
    return _make(
        "CT-START-002",
        Verdict.PASS,
        "2 of 2 handshake fields are present.",
        evidence,
    )


def check_start_003(ctx: StartupContext) -> CheckResult:
    if ctx.tools_error is not None:
        return _make(
            "CT-START-003",
            Verdict.FAIL,
            "tools/list failed.",
            (Evidence("error", ctx.tools_error),),
        )
    warnings: list[str] = []
    evidence: list[Evidence] = []
    if ctx.zero_tools:
        warnings.append("0 tools were returned.")
        evidence.append(
            Evidence(
                "empty_tool_list",
                "An empty tool list is also valid for a server that offers only resources or prompts.",
            )
        )
    if ctx.pages_cap_hit:
        warnings.append("tools/list page cap was hit.")
        evidence.append(
            Evidence(
                "page_cap",
                f"{ctx.page_count} pages were read; the next cursor was still present.",
            )
        )
    if warnings:
        return _make(
            "CT-START-003",
            Verdict.WARN,
            " ".join(warnings),
            tuple(evidence),
        )
    return _make(
        "CT-START-003",
        Verdict.PASS,
        f"tools/list returned {ctx.tool_count} tools across {ctx.page_count} pages.",
    )


def check_start_004(ctx: StartupContext) -> CheckResult:
    if ctx.stdout_noise_count:
        evidence = [Evidence("count", str(ctx.stdout_noise_count))]
        for index, line in enumerate(ctx.stdout_noise[:5], start=1):
            evidence.append(Evidence(f"line {index}", line))
        return _make(
            "CT-START-004",
            Verdict.WARN,
            f"{ctx.stdout_noise_count} non-protocol stdout lines were seen.",
            tuple(evidence),
        )
    return _make(
        "CT-START-004",
        Verdict.PASS,
        "0 non-protocol stdout lines were seen.",
    )


def check_start_005(ctx: StartupContext) -> CheckResult:
    if ctx.exited_by_itself is None:
        reason = (
            "server had already exited before shutdown"
            if ctx.exited_before_shutdown
            else "session did not start or outcome is unknown"
        )
        return _make(
            "CT-START-005",
            Verdict.NOT_TESTED,
            "Server exit outcome was not recorded.",
            reason=reason,
        )
    if ctx.exited_by_itself:
        return _make(
            "CT-START-005",
            Verdict.PASS,
            "Server exited by itself after input was closed.",
        )
    return _make(
        "CT-START-005",
        Verdict.WARN,
        "Server had to be killed after input was closed.",
    )


STARTUP_CHECK_FUNCTIONS: dict[str, Callable[[StartupContext], CheckResult]] = {
    "CT-START-001": check_start_001,
    "CT-START-002": check_start_002,
    "CT-START-003": check_start_003,
    "CT-START-004": check_start_004,
    "CT-START-005": check_start_005,
}
