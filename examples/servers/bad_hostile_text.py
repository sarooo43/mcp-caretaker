"""Raw fixture with hostile-looking text. Test fixture only.

The tool description carries backtick runs, a markdown link, an HTML tag, an
escape character and a non-ASCII letter. Checks never quote a description,
so the same text is also written as one stdout noise line: the startup
check quotes that line in evidence, which is what report rendering must
keep inside fences and escape for the terminal. No real secret is used.
"""

from __future__ import annotations

from _raw_tools import clean_tool, serve

HOSTILE = (
    "Hostile ``` triple and ````` five [link](https://example.invalid) "
    "<b>tag</b> \x1b[31m caf\u00e9 text for this tool."
)
TOOL = clean_tool("hostile", HOSTILE)

if __name__ == "__main__":
    serve(pages=[{"tools": [TOOL]}], stdout_noise=[HOSTILE])
