"""Raw fixture that exits after a chosen probe. Test fixture, not a template."""

from __future__ import annotations

import os
from typing import Any

from _raw_tools import clean_tool, serve, tool_result

MODE = os.environ.get("CARETAKER_TEST_MODE", "after_probes")
TOOL = clean_tool(
    "echo",
    "Return the supplied text unchanged.",
    properties={
        "text": {
            "type": "string",
            "description": "The text to return unchanged.",
        }
    },
)
TOOL["annotations"] = {"readOnlyHint": True}
COUNTER = 0


def on_call(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any], bool] | None:
    global COUNTER
    COUNTER += 1
    if MODE == "call":
        os._exit(7)
    if MODE == "after_probes" and COUNTER >= 5:
        return tool_result("done"), True
    return tool_result("invalid input", is_error=True), False


if __name__ == "__main__":
    serve(
        pages=[{"tools": [TOOL]}],
        on_call=on_call,
        exit_after_list=MODE == "list",
        pidfile=os.environ.get("CARETAKER_TEST_PIDFILE"),
    )
