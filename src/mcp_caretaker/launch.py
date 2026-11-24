"""Launch configuration and helpers for a local MCP server.

``extra_env`` values are treated as secrets: they appear in the child environment,
but never in a ``LaunchSpec`` repr/str, in error messages, or in captured stderr.
Only their names are ever shown.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .thresholds import SHUTDOWN_GRACE_SECONDS

# Shorter values would redact harmless common substrings ("1", "a", "/tmp"), so
# the redactor deliberately ignores them. Documented in docs/decisions/0002.
REDACTION_MIN_LENGTH = 4


@dataclass(frozen=True)
class LaunchSpec:
    """How to launch one server. ``argv`` is a tuple, never a command string."""

    argv: tuple[str, ...]
    extra_env: Mapping[str, str] = field(default_factory=dict)
    startup_timeout: float = 30.0
    call_timeout: float = 10.0
    shutdown_grace: float = SHUTDOWN_GRACE_SECONDS

    def __post_init__(self) -> None:
        if isinstance(self.argv, str) or not isinstance(self.argv, tuple):
            raise TypeError("argv must be a tuple of strings, never a command string")
        if not self.argv:
            raise ValueError("argv must not be empty")
        if not all(isinstance(item, str) for item in self.argv):
            raise TypeError("every argv item must be a string")
        for name, value in self.extra_env.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise TypeError("extra_env names and values must be strings")
        if self.startup_timeout <= 0:
            raise ValueError("startup_timeout must be positive")
        if self.call_timeout <= 0:
            raise ValueError("call_timeout must be positive")
        if self.shutdown_grace <= 0:
            raise ValueError("shutdown_grace must be positive")

    def __repr__(self) -> str:
        text = (
            f"LaunchSpec(argv={self.argv!r}, "
            f"extra_env_names={sorted(self.extra_env)!r}, "
            f"startup_timeout={self.startup_timeout!r}, "
            f"call_timeout={self.call_timeout!r}, "
            f"shutdown_grace={self.shutdown_grace!r})"
        )
        return redact_values(text, self.extra_env)

    __str__ = __repr__


def build_child_env(spec: LaunchSpec, temp_dir: str | Path) -> dict[str, str]:
    """Build the child environment from EMPTY plus a small allow-list.

    Nothing from the parent is inherited except the names below. ``TEMP``, ``TMP``
    and (on POSIX) ``TMPDIR`` point at our temp folder. ``extra_env`` is added last
    and may override any of these names.
    """
    root = str(Path(temp_dir))
    env: dict[str, str] = {}

    if "PATH" in os.environ:
        env["PATH"] = os.environ["PATH"]

    if sys.platform == "win32":
        for name in ("SYSTEMROOT", "COMSPEC", "PATHEXT"):
            if name in os.environ:
                env[name] = os.environ[name]

    env["TEMP"] = root
    env["TMP"] = root
    if sys.platform != "win32":
        env["TMPDIR"] = root
        # Locale names only; CPython may add LC_CTYPE itself at startup.
        for name in ("LANG", "LC_ALL"):
            if name in os.environ:
                env[name] = os.environ[name]

    for name, value in spec.extra_env.items():
        env[name] = value
    return env


def redact_values(text: str, extra_env: Mapping[str, str]) -> str:
    """Replace each secret value with ``[REDACTED:NAME]``.

    Values shorter than ``REDACTION_MIN_LENGTH`` (4) are not replaced: a one- or
    two-character value would otherwise redact ordinary text everywhere. Names are
    kept, values are not. Longer values are replaced first so that one secret which
    contains another cannot leave a partial value behind.
    """
    items = sorted(extra_env.items(), key=lambda item: (-len(item[1]), item[0]))
    for name, value in items:
        if len(value) < REDACTION_MIN_LENGTH:
            continue
        text = text.replace(value, f"[REDACTED:{name}]")
    return text
