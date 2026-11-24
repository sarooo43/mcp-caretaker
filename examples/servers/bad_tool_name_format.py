"""Raw fixture with a spaced and a 129-character name. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

spaced = clean_tool("name with space", "A clear description for the spaced name.")
too_long = clean_tool("a" * 129, "A clear description for the long name.")

if __name__ == "__main__":
    serve(pages=[{"tools": [spaced, too_long]}])
