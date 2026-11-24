"""Raw fixture for a slow or exiting large-string call. Test fixture, not a template."""

from __future__ import annotations

import os
import time
from typing import Any

from _raw_tools import clean_tool, serve, tool_result

MODE = os.environ.get("CARETAKER_TEST_MODE", "slow")
TOOL = clean_tool(
    "string_tool",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)
TOOL["annotations"] = {"readOnlyHint": True}


def on_call(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    value = arguments.get("text")
    if name == "string_tool" and isinstance(value, str) and len(value) > 1000:
        if MODE == "crash":
            os._exit(7)
        if MODE == "slow":
            time.sleep(3)
    return tool_result("ok"), False


if __name__ == "__main__":
    serve(
        pages=[{"tools": [TOOL]}],
        on_call=on_call,
        pidfile=os.environ.get("CARETAKER_TEST_PIDFILE"),
    )
