"""Raw fixture with an 80-space whitespace run. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

tool = clean_tool()
tool["description"] = (
    "A clear description for this tool." + " " * 80 + "harmless filler"
)

if __name__ == "__main__":
    serve(pages=[{"tools": [tool]}])
