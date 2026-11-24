"""T0: exact SDK pin facts. Evidence only."""
import importlib.metadata as md

print("mcp", md.version("mcp"))
print("mcp-types", md.version("mcp-types"))
print("requires", [r for r in (md.requires("mcp") or []) if "mcp-types" in r])
