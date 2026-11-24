"""Isolated import of the SDK's internal Windows Job Object helpers."""

from __future__ import annotations

from typing import Any

from .errors import CaretakerError


def windows_helpers() -> tuple[Any, Any, Any]:
    """Return the three SDK helpers, or fail loudly if an SDK update removes them."""
    try:
        from mcp.os.win32.utilities import (
            close_process_job,
            create_windows_process,
            terminate_windows_process_tree,
        )
    except (ImportError, AttributeError) as exc:
        raise CaretakerError(
            "mcp==2.3.0 Windows Job Object helper is missing; the launcher "
            "cannot start or stop a Windows child"
        ) from exc
    return create_windows_process, terminate_windows_process_tree, close_process_job
