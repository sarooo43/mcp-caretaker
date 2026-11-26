"""Raw fixture mixing an accepted and a rejected generated valid call.

One read-only tool accepts the generated valid call and one read-only tool with
no required property rejects every call. Test fixture, not a template.
"""

from __future__ import annotations

import os
from typing import Any

from _raw_tools import clean_tool, serve, tool_result

MODE = os.environ.get("CARETAKER_TEST_MODE", "mixed")

ACCEPT_TOOL = clean_tool(
    "accept_tool",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)
REJECT_TOOL = clean_tool(
    "reject_tool",
    "Reject every call because its rule is not in its schema.",
    properties={},
)
for TOOL in (ACCEPT_TOOL, REJECT_TOOL):
    TOOL["annotations"] = {"readOnlyHint": True}


def on_call(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if name == "accept_tool" and isinstance(arguments.get("text"), str):
        if MODE == "reject_all":
            return tool_result("generated input rejected", is_error=True), False
        return tool_result("accepted"), False
    return tool_result("invalid input", is_error=True), False


if __name__ == "__main__":
    serve(pages=[{"tools": [ACCEPT_TOOL, REJECT_TOOL]}], on_call=on_call)
