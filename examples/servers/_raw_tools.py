"""Raw standard-library MCP fixture helper. Test fixture, not a template.

It writes line-delimited JSON-RPC on stdout. Fixture scripts choose the raw
``tools/list`` pages, so checks can inspect wire text that SDK objects drop.
No paths or text from a server response are executed.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def send(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def result(mid: Any, value: dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": mid, "result": value})


def error(mid: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}})


def clean_tool(
    name: str = "ok",
    description: str = "A clear description for this tool.",
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if properties is None:
        properties = {
            "value": {
                "type": "string",
                "description": "A string value for this tool.",
            }
        }
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": properties},
    }


def serve(
    *,
    pages: list[dict[str, Any]] | None = None,
    server_name: str = "raw-fixture",
    server_version: str = "1.0",
    stdout_noise: list[str] | None = None,
    tools_error: dict[str, Any] | None = None,
    ignore_stdin_close: bool = False,
    pidfile: str | None = None,
) -> None:
    """Serve one raw stdio session using only fixed fixture choices."""
    if pidfile is not None:
        Path(pidfile).write_text(str(os.getpid()), encoding="utf-8")
    for line in stdout_noise or []:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
    chosen_pages = pages or [{"tools": [clean_tool()]}]

    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if not isinstance(msg, dict) or "id" not in msg:
            continue
        mid = msg["id"]
        method = msg.get("method")
        params = msg.get("params") or {}
        if method == "initialize":
            result(
                mid,
                {
                    "protocolVersion": params.get("protocolVersion", "2025-11-25"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": server_name,
                        "version": server_version,
                    },
                },
            )
        elif method == "tools/list":
            if tools_error is not None:
                error(
                    mid,
                    int(tools_error.get("code", -32000)),
                    str(tools_error.get("message", "tools/list unavailable")),
                )
            else:
                index = int(params.get("cursor") or 0)
                result(mid, chosen_pages[min(index, len(chosen_pages) - 1)])
        elif method == "ping":
            result(mid, {})
        else:
            error(mid, -32601, "method not found")

    if ignore_stdin_close:
        while True:
            time.sleep(1)
