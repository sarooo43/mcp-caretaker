"""Raw fixture with 5- and 1100-character descriptions. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

too_short = clean_tool("too_short", "short")
too_long = clean_tool("too_long", "x" * 1100)

if __name__ == "__main__":
    serve(pages=[{"tools": [too_short, too_long]}])
