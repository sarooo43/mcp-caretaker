"""MCP fixture that spawns a long-sleeping grandchild, then serves normally.

Not intentionally bad: it exists so cleanup can be tested against a surviving
descendant process. test fixture, not a template.
"""

from __future__ import annotations

import os
import subprocess
import sys

from mcp.server.mcpserver import MCPServer

server = MCPServer("spawns-grandchild")


def start_grandchild() -> None:
    """Spawn a process that outlives the server unless the tree is killed."""
    creationflags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    )
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    pidfile = os.environ.get("CARETAKER_TEST_PIDFILE")
    if pidfile:
        with open(pidfile, "w", encoding="utf-8") as handle:
            handle.write(str(child.pid))


@server.tool(description="Return a fixed string so the server can be queried.")
def ping() -> str:
    return "pong"


if __name__ == "__main__":
    start_grandchild()
    server.run(transport="stdio")
