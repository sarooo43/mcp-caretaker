"""Raw fixture with two tools sharing one name. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

first = clean_tool("duplicate", "A clear description for the first duplicate tool.")
second = clean_tool("duplicate", "A clear description for the second duplicate tool.")

if __name__ == "__main__":
    serve(pages=[{"tools": [first, second]}])
