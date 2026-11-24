"""Raw fixture with hidden Unicode characters in scanned text.

Test fixture, not a template. The wire is ASCII because json.dumps escapes it.
"""

from __future__ import annotations

from _raw_tools import clean_tool, serve

tool = clean_tool("hidden", "A description with hidden characters for this check.")
tool["title"] = "Read\u200bme"
tool["description"] = "A description with \u202e direction control."
tool["inputSchema"]["properties"]["field\u200b"] = {
    "type": "string",
    "title": "Field\ue000",
    "description": "A value with \u0001 control.",
}

if __name__ == "__main__":
    serve(pages=[{"tools": [tool]}])
