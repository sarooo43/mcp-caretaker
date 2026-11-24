"""T0 d/e/f: SDK probe server. Test fixture, not a template."""
from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

server = MCPServer("sdk-probe", version="1.0")
ro = ToolAnnotations(read_only_hint=True)


@server.tool(description="Return the supplied string unchanged.", annotations=ro)
def echo(text: str) -> str:
    return text


@server.tool(description="Accept one integer and return text.", annotations=ro)
def integer_tool(value: int) -> str:
    return "ok"


@server.tool(description="Accept one number and return text.", annotations=ro)
def number_tool(value: float) -> str:
    return "ok"


@server.tool(description="Accept one boolean and return text.", annotations=ro)
def boolean_tool(value: bool) -> str:
    return "ok"


@server.tool(description="Accept one array and return text.", annotations=ro)
def array_tool(value: list[str]) -> str:
    return "ok"


@server.tool(description="Accept one object and return text.", annotations=ro)
def object_tool(value: dict[str, str]) -> str:
    return "ok"


if __name__ == "__main__":
    server.run(transport="stdio")
