"""Raw fixture with a second tools/list page. Test fixture, not a template.

The page-two tool has no description, so a collector that reads only page one
cannot flag it.
"""

from __future__ import annotations

from _raw_tools import clean_tool, serve

first = clean_tool("page_one_tool", "A clear description for the first page tool.")
second = clean_tool("page_two_tool", "This tool appears only on the second page.")
del second["description"]

if __name__ == "__main__":
    serve(
        pages=[
            {"tools": [first], "nextCursor": "1"},
            {"tools": [second]},
        ]
    )
