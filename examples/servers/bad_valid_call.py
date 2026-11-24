"""Raw fixture for a rejected or exiting valid call. Test fixture, not a template."""

from __future__ import annotations

import os
from typing import Any

from _raw_tools import clean_tool, serve, tool_result

MODE = os.environ.get("CARETAKER_TEST_MODE", "error")
TOOL = clean_tool(
    "string_tool",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)
TOOL["annotations"] = {"readOnlyHint": True}


def on_call(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    value = arguments.get("text")
    if name == "string_tool" and isinstance(value, str) and value == "A":
        if MODE == "crash":
            os._exit(7)
        if MODE == "error":
            return tool_result("valid input rejected", is_error=True), False
    if name == "string_tool" and isinstance(value, str) and len(value) > 1000:
        return tool_result("ok"), False
    return tool_result("invalid input", is_error=True), False


if __name__ == "__main__":
    serve(pages=[{"tools": [TOOL]}], on_call=on_call)
