"""Raw fixture with one tool that has no description. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

tool = clean_tool()
del tool["description"]

if __name__ == "__main__":
    serve(pages=[{"tools": [tool]}])
