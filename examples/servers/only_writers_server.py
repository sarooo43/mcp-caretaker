"""Raw fixture with writer tools only. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

TOOL = clean_tool(
    "string_tool",
    "Return the supplied text unchanged.",
    properties={"text": {"type": "string", "description": "The text to return."}},
)

if __name__ == "__main__":
    serve(pages=[{"tools": [TOOL]}])
