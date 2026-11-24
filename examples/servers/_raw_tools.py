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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CallError:
    """A call-level JSON-RPC error chosen by a fixture."""

    code: int
    message: str
    data: Any = None


def send(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def result(mid: Any, value: dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": mid, "result": value})


def error(mid: Any, code: int, message: str, data: Any = None) -> None:
    payload: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        payload["data"] = data
    send({"jsonrpc": "2.0", "id": mid, "error": payload})


def tool_result(text: str, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


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
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
        },
    }


def _log_call(name: str, arguments: dict[str, Any]) -> None:
    path = os.environ.get("CARETAKER_TEST_CALLLOG")
    if not path:
        return
    args: dict[str, dict[str, Any]] = {}
    for key, value in arguments.items():
        length = len(value) if isinstance(value, (str, list, dict)) else None
        args[str(key)] = {"type": type(value).__name__, "length": length}
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"tool": name, "args": args}) + "\n")


def serve(
    *,
    pages: list[dict[str, Any]] | None = None,
    server_name: str = "raw-fixture",
    server_version: str = "1.0",
    server_info_instructions: str | None = None,
    instructions: str | None = None,
    stdout_noise: list[str] | None = None,
    stderr_lines: list[str] | None = None,
    tools_error: dict[str, Any] | None = None,
    ignore_stdin_close: bool = False,
    pidfile: str | None = None,
    on_call: Callable[
        [str, dict[str, Any]],
        dict[str, Any] | tuple[dict[str, Any], bool] | CallError | None,
    ]
    | None = None,
    exit_after_list: bool = False,
) -> None:
    """Serve one raw stdio session using only fixed fixture choices."""
    if pidfile is not None:
        Path(pidfile).write_text(str(os.getpid()), encoding="utf-8")
    for line in stdout_noise or []:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
    for line in stderr_lines or []:
        sys.stderr.write(line + "\n")
        sys.stderr.flush()
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
            server_info: dict[str, Any] = {
                "name": server_name,
                "version": server_version,
            }
            if server_info_instructions is not None:
                server_info["instructions"] = server_info_instructions
            initialize_result: dict[str, Any] = {
                "protocolVersion": params.get("protocolVersion", "2025-11-25"),
                "capabilities": {"tools": {}},
                "serverInfo": server_info,
            }
            if instructions is not None:
                initialize_result["instructions"] = instructions
            result(mid, initialize_result)
        elif method == "tools/list":
            if exit_after_list:
                os._exit(7)
            if tools_error is not None:
                error(
                    mid,
                    int(tools_error.get("code", -32000)),
                    str(tools_error.get("message", "tools/list unavailable")),
                )
            else:
                index = int(params.get("cursor") or 0)
                result(mid, chosen_pages[min(index, len(chosen_pages) - 1)])
        elif method == "tools/call":
            name = str(params.get("name", ""))
            raw_args = params.get("arguments")
            arguments = raw_args if isinstance(raw_args, dict) else {}
            _log_call(name, arguments)
            answer = on_call(name, arguments) if on_call is not None else None
            if isinstance(answer, CallError):
                error(mid, answer.code, answer.message, answer.data)
            else:
                die_after_reply = False
                if isinstance(answer, tuple):
                    answer, die_after_reply = answer
                if answer is None:
                    answer = tool_result("invalid input", is_error=True)
                result(mid, answer)
                if die_after_reply:
                    time.sleep(0.2)
                    os._exit(7)
        elif method == "ping":
            result(mid, {})
        else:
            error(mid, -32601, "method not found")

    if ignore_stdin_close:
        while True:
            time.sleep(1)
