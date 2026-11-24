"""Errors raised by mcp-caretaker.

Callers must pass already-redacted text when constructing these errors. Messages
never contain values from ``extra_env``; that is enforced in ``session.py``.
"""

from __future__ import annotations


class CaretakerError(Exception):
    """Base class for all mcp-caretaker errors."""


class ConfirmationRequired(CaretakerError):
    """Raised when a launch was attempted without ``confirmed=True``."""


class ServerExited(CaretakerError):
    """The child exited before the MCP handshake completed."""

    def __init__(self, exit_code: int | None, stderr_tail: str = "") -> None:
        self.exit_code = exit_code
        self.stderr_tail = stderr_tail
        super().__init__(
            f"server exited before the MCP handshake (exit code {exit_code}); "
            f"stderr tail: {stderr_tail}"
        )


class StartupTimeout(CaretakerError):
    """The MCP handshake did not complete within ``startup_timeout``."""


class CallTimeout(CaretakerError):
    """A tools/call did not complete within its timeout."""
