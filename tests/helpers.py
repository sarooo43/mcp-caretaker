"""Shared helpers for the tests. Nothing here ships in the wheel."""

from __future__ import annotations

import pathlib
import sys
from collections.abc import Callable

import anyio

SERVERS = pathlib.Path(__file__).resolve().parents[1] / "examples" / "servers"


def server_path(name: str) -> pathlib.Path:
    """Absolute path to a fixture server."""
    return (SERVERS / name).resolve()


def server_argv(name: str, *args: str) -> tuple[str, ...]:
    """Argv tuple that starts a fixture server directly (never a shell)."""
    return (sys.executable, str(server_path(name)), *args)


def result_text(result: object) -> str:
    """Join the text blocks of an SDK CallToolResult."""
    return "".join(
        getattr(block, "text", "") for block in getattr(result, "content", [])
    )


async def wait_until(predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    """Bounded poll; returns whether the predicate became true in time."""
    with anyio.move_on_after(timeout):
        while not predicate():
            await anyio.sleep(0.02)
        return True
    return predicate()
