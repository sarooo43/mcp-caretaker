"""Clean MCP fixture built with the official SDK. Test fixture, not a template.

Annotated arguments with pydantic Field descriptions produce described top-level
inputSchema properties; the bridge tap inspects those raw wire dicts.
"""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

server = MCPServer("clean-server", version="1.0")


@server.tool(description="Return the supplied text unchanged.")
def echo(
    text: Annotated[str, Field(description="The text to return unchanged.")],
) -> str:
    return text


@server.tool(description="Add two integers and return the sum.")
def add(
    left: Annotated[int, Field(description="The first integer to add.")],
    right: Annotated[int, Field(description="The second integer to add.")],
) -> int:
    return left + right


if __name__ == "__main__":
    server.run(transport="stdio")
