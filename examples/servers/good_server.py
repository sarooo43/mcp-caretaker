"""Good MCP fixture: three well-formed tools, two with readOnlyHint.

Not intentionally bad. test fixture, not a template.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

server = MCPServer("good-server")


@server.tool(
    description="Return the given text unchanged.",
    annotations=ToolAnnotations(read_only_hint=True),
)
def echo(text: str) -> str:
    return text


@server.tool(
    description="Add two integers and return the sum.",
    annotations=ToolAnnotations(read_only_hint=True),
)
def add(a: int, b: int) -> int:
    return a + b


@server.tool(
    description="Append the given text to notes.txt in the current working directory."
)
def save_note(text: str) -> str:
    # Deliberately has NO readOnlyHint: this one writes into the child's cwd.
    with open("notes.txt", "a", encoding="utf-8") as handle:
        handle.write(text + "\n")
    return "saved"


if __name__ == "__main__":
    server.run(transport="stdio")
