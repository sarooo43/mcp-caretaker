"""mcp-caretaker: local MCP server runtime behaviour checks (pre-release library)."""

__version__ = "0.0.0.dev0"

from .model import (
    CheckResult as CheckResult,
)
from .model import (
    Evidence as Evidence,
)
from .model import (
    RunResult as RunResult,
)
from .model import (
    Verdict as Verdict,
)
from .runner import run_checks as run_checks
