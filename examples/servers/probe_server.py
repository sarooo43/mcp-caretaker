"""Probe MCP fixture: reports the child's environment, cwd, timing and stderr.

Intentionally exposes its own environment to the test process. Not intentionally
bad in any other way. test fixture, not a template.
"""

from __future__ import annotations

import json
import os
import sys
import time

from mcp.server.mcpserver import MCPServer

server = MCPServer("probe-server")

# A test can ask for a large non-secret padding block to exercise the 64 KiB
# stderr cap. The padding is ordinary text, never a secret value.
_PADDING_ENV = "CARETAKER_STDERR_PADDING"


@server.tool(
    description="Return the sorted environment variable NAMES seen by the child."
)
def env_names() -> str:
    return json.dumps(sorted(os.environ.keys()))


@server.tool(description="Return the child's current working directory.")
def cwd() -> str:
    return os.getcwd()


@server.tool(description="Sleep for the given number of seconds, then return.")
def sleep(seconds: float) -> str:
    time.sleep(seconds)
    return "done"


@server.tool(description="Write the named environment variable's value to stderr.")
def shout_env(name: str) -> str:
    padding = int(os.environ.get(_PADDING_ENV, "0"))
    if padding > 0:
        sys.stderr.write("STDERR_START\n" + "P" * padding + "\n")
    sys.stderr.write(f"VALUE={os.environ.get(name, '<missing>')}\n")
    sys.stderr.write("SHOUT_ENV_DONE\n")
    sys.stderr.flush()
    return "ok"


if __name__ == "__main__":
    server.run(transport="stdio")
