"""Raw fixture with more tools/list pages than the page cap.

Test fixture, not a template. The eleventh page is deliberately never read.
"""

from __future__ import annotations

from _raw_tools import clean_tool, serve

pages: list[dict[str, object]] = []
for index in range(11):
    page: dict[str, object] = {"tools": [clean_tool(f"page_{index}_tool")]}
    if index < 10:
        page["nextCursor"] = str(index + 1)
    pages.append(page)

if __name__ == "__main__":
    serve(pages=pages)
