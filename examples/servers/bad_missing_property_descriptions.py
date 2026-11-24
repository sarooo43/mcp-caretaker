"""Raw fixture with an undocumented top-level property. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

tool = clean_tool()
tool["inputSchema"]["properties"] = {"value": {"type": "string"}}

if __name__ == "__main__":
    serve(pages=[{"tools": [tool]}])
