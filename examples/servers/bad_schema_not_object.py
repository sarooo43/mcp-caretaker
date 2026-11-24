"""Raw fixture with one missing and one non-object inputSchema. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import clean_tool, serve

missing_schema = clean_tool("missing_schema")
del missing_schema["inputSchema"]
string_schema = clean_tool("string_schema")
string_schema["inputSchema"] = {"type": "string"}

if __name__ == "__main__":
    serve(pages=[{"tools": [missing_schema, string_schema]}])
