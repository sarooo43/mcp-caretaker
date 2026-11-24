"""Raw fixture that records call shapes only. Test fixture, not a template."""

from __future__ import annotations

import os
from typing import Any

from _raw_tools import clean_tool, serve, tool_result

FAKE = os.environ.get("CARETAKER_FAKE_TEXT", "no-value")
WRITER = clean_tool(
    "writer",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)
READER = clean_tool(
    "reader",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)
READER["annotations"] = {"readOnlyHint": True}


def on_call(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    value = arguments.get("text")
    if name == "reader" and isinstance(value, str) and value == "A":
        return tool_result("ok"), False
    if name == "reader" and isinstance(value, str) and len(value) > 1000:
        return tool_result("ok"), False
    return tool_result("invalid input " + FAKE, is_error=True), False


if __name__ == "__main__":
    serve(pages=[{"tools": [WRITER, READER]}], on_call=on_call)
