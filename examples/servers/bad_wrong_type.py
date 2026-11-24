"""Raw fixture for wrong-type acceptance, delay or exit. Test fixture, not a template."""

from __future__ import annotations

import os
import time
from typing import Any

from _raw_tools import clean_tool, serve, tool_result

MODE = os.environ.get("CARETAKER_TEST_MODE", "accept")
TOOL = clean_tool(
    "string_tool",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)


def on_call(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if name == "string_tool" and isinstance(arguments.get("text"), dict):
        if MODE == "crash":
            os._exit(7)
        if MODE == "hang":
            time.sleep(5)
        if MODE == "accept":
            return tool_result("accepted"), False
    return tool_result("invalid input", is_error=True), False


if __name__ == "__main__":
    serve(
        pages=[{"tools": [TOOL]}],
        on_call=on_call,
        pidfile=os.environ.get("CARETAKER_TEST_PIDFILE"),
    )
