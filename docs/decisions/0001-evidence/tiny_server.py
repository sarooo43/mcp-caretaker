"""T0 evidence fixture: tiny SDK-based MCP server. Test fixture, not a template."""

import json
import os
import subprocess
import sys
import time

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

server = MCPServer("t0-tiny")


@server.tool(description="Return the text unchanged.", annotations=ToolAnnotations(read_only_hint=True))
def echo(text: str) -> str:
    return text


@server.tool(description="Add two integers.", annotations=ToolAnnotations(read_only_hint=True))
def add(a: int, b: int) -> int:
    return a + b


@server.tool(description="List environment variable NAMES.")
def env_names() -> str:
    return json.dumps(sorted(os.environ.keys()))


@server.tool(description="Return the working directory.")
def cwd() -> str:
    return os.getcwd()


@server.tool(description="Write a variable's value to stderr.")
def shout_env(name: str) -> str:
    sys.stderr.write(f"SHOUT={os.environ.get(name, '<missing>')}\n")
    sys.stderr.flush()
    return "ok"


@server.tool(description="Spawn a sleeping grandchild, return its pid.")
def spawn_grandchild() -> str:
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pidfile = os.environ.get("CARETAKER_PIDFILE")
    if pidfile:
        with open(pidfile, "w", encoding="utf-8") as handle:
            handle.write(str(child.pid))
    return str(child.pid)


@server.tool(description="Sleep for a while.")
def sleep(seconds: float) -> str:
    time.sleep(seconds)
    return "done"


if __name__ == "__main__":
    server.run(transport="stdio")
