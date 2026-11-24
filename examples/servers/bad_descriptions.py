"""Raw fixture with one separate problem for every description/schema check.

Test fixture, not a template. Some malformed answers are rejected by SDK objects
but remain visible to the bounded bridge tap as raw tools/list result dicts.
"""

from __future__ import annotations

from _raw_tools import clean_tool, serve

missing_description = clean_tool(
    "no_description", "A clear description would normally be here."
)
del missing_description["description"]

too_short = clean_tool("too_short", "short")
too_long = clean_tool("too_long", "x" * 1001)
first_duplicate = clean_tool(
    "duplicate", "A clear description for the first duplicate tool."
)
second_duplicate = clean_tool(
    "duplicate", "A clear description for the second duplicate tool."
)

bad_schema = clean_tool("bad_schema", "A clear description for this tool.")
bad_schema["inputSchema"] = {"type": "string"}

untyped_property = clean_tool("untyped_property", "A clear description for this tool.")
untyped_property["inputSchema"]["properties"]["loose"] = {
    "description": "An untyped value for this tool."
}

undocumented_property = clean_tool(
    "undocumented_property", "A clear description for this tool."
)
undocumented_property["inputSchema"]["properties"]["value"] = {"type": "string"}

hidden = clean_tool("hidden", "A description with a hidden character here.")
hidden["description"] += "\u200b"

long_space = clean_tool("long_space", "A clear description for this tool.")
long_space["description"] += " " * 40 + "after the run"

invalid_name = clean_tool("name with space", "A clear description for this tool.")

non_string = clean_tool("non_string", "A clear description for this tool.")
non_string["description"] = 123

tools = [
    missing_description,
    too_short,
    too_long,
    first_duplicate,
    second_duplicate,
    bad_schema,
    untyped_property,
    undocumented_property,
    hidden,
    long_space,
    invalid_name,
    non_string,
]

if __name__ == "__main__":
    serve(pages=[{"tools": tools}])
