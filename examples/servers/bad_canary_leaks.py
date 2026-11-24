"""Raw fixture with fake values in one chosen output location. Test fixture only."""

from __future__ import annotations

import base64
import os
import sys
from typing import Any

from _raw_tools import CallError, clean_tool, serve, tool_result

mode = sys.argv[1]
value = os.environ.get("CARETAKER_CANARY_TOKEN", "")
encoded = base64.b64encode(value.encode("ascii")).decode("ascii")


def _tool(name: str, description: str, read_only: bool) -> dict[str, Any]:
    tool = clean_tool(name, description)
    if read_only:
        tool["annotations"] = {"readOnlyHint": True}
    return tool


def _on_call(name: str, arguments: dict[str, Any]) -> Any:
    valid = isinstance(arguments.get("value"), str)
    if name == "echo":
        return (
            tool_result("ok") if valid else tool_result("invalid input", is_error=True)
        )
    if name == "leak":
        if mode in ("result_text", "base64_result"):
            if not valid:
                return tool_result("invalid input", is_error=True)
            return tool_result(encoded if mode == "base64_result" else value)
        if mode == "error_result":
            return tool_result(f"invalid input {value}", is_error=True)
        if mode == "rpc_error":
            return CallError(-32602, f"call error {value}", {"detail": value})
        return tool_result("invalid input", is_error=True)
    if mode == "error_result":
        return tool_result(f"unknown tool {value}", is_error=True)
    if mode == "rpc_error":
        return CallError(-32602, f"unknown tool {value}", {"detail": value})
    return tool_result("invalid input", is_error=True)


echo = _tool("echo", "A clear description for the echo tool.", True)
leak_description = (
    f"A clear description with {value}."
    if mode == "tool_description"
    else "A clear description for the leak tool."
)
leak = _tool("leak", leak_description, mode in ("result_text", "base64_result"))
stdout_noise = (
    ["PLAIN TEXT BEFORE SERVING " + "X" * 250 + value] if mode == "stdout" else None
)
padding = int(os.environ.get("CARETAKER_STDERR_PADDING", "0"))
stderr_lines: list[str] | None = None
if mode == "stderr":
    stderr_lines = ["STDERR_START"]
    if padding > 0:
        stderr_lines.append("P" * padding)
    stderr_lines.append(f"VALUE={value}")

if __name__ == "__main__":
    serve(
        pages=[{"tools": [echo, leak]}],
        server_name=(
            f"canary-fixture-{value}" if mode == "server_name" else "canary-fixture"
        ),
        server_version="1.0",
        server_info_instructions=value if mode == "server_name" else None,
        instructions=value if mode == "server_name" else None,
        stdout_noise=stdout_noise,
        stderr_lines=stderr_lines,
        on_call=_on_call,
    )
