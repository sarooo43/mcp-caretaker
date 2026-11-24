"""Raw fixture with an untyped top-level property. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

tool = clean_tool()
tool["inputSchema"]["properties"] = {
    "loose": {"description": "An untyped value for this tool."}
}

if __name__ == "__main__":
    serve(pages=[{"tools": [tool]}])
