"""T0 evidence: PyPI release metadata and installed SDK signatures.

Run in a throwaway venv with the official "mcp" package installed.
Output is trimmed and contains no personal paths.
"""

import importlib.metadata as md
import inspect
import json
import urllib.request

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client
from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations, version

data = json.load(urllib.request.urlopen("https://pypi.org/pypi/mcp/json", timeout=30))
print("PyPI latest:", data["info"]["version"])
print("PyPI Requires-Python:", data["info"]["requires_python"])
print("PyPI classifiers:", [c for c in data["info"]["classifiers"] if "Python :: 3" in c])
all_versions = list(data["releases"])
print("2.x stable releases:", [v for v in all_versions if v.startswith("2.") and not any(t in v for t in ("a", "b", "rc"))])
print("2.x pre-releases:", [v for v in all_versions if v.startswith("2.") and any(t in v for t in ("a", "b", "rc"))])
print("installed mcp:", md.version("mcp"))
print("protocol revisions:", version.KNOWN_PROTOCOL_VERSIONS)
print("handshake revisions:", version.HANDSHAKE_PROTOCOL_VERSIONS)
print("modern revisions:", version.MODERN_PROTOCOL_VERSIONS)
print("supported:", version.SUPPORTED_PROTOCOL_VERSIONS)
print("stdio_client:", inspect.signature(stdio_client))
print("StdioServerParameters:", inspect.signature(StdioServerParameters))
print("ClientSession:", inspect.signature(ClientSession))
print("ClientSession.initialize:", inspect.signature(ClientSession.initialize))
print("ClientSession.call_tool:", inspect.signature(ClientSession.call_tool))
print("default env NAMES:", sorted(get_default_environment()))
print("MCPServer.tool:", inspect.signature(MCPServer.tool))
print("MCPServer.run:", inspect.signature(MCPServer.run))
print("ToolAnnotations fields:", list(ToolAnnotations.model_fields))
print("read_only_hint alias:", ToolAnnotations.model_fields["read_only_hint"].alias)
