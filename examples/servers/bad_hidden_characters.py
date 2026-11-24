"""Raw fixture with hidden format characters in scanned text.

Test fixture, not a template. Only Unicode Cf characters are used here, so a
mutation that ignores Cf has nothing else to flag. The wire is ASCII because
json.dumps escapes the characters.
"""

from __future__ import annotations

from _raw_tools import clean_tool, serve

tool = clean_tool("hidden", "A description with hidden characters for this check.")
tool["title"] = "Read\u200bme"
tool["description"] = "A description with \u202e direction control."
tool["inputSchema"]["properties"]["field\u200b"] = {
    "type": "string",
    "title": "Field\u200b",
    "description": "A value with \u202e direction control.",
}

if __name__ == "__main__":
    serve(pages=[{"tools": [tool]}])
