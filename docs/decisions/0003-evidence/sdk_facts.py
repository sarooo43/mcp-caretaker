"""T0 SDK facts: dependency, Windows helper, models and pagination API."""
import importlib.metadata as md
import inspect

import mcp
import mcp.os
import mcp.os.win32
import mcp.os.win32.utilities as u
from mcp import ClientSession
from mcp_types import Implementation, InitializeResult, ListToolsResult, PaginatedRequestParams

print("mcp:", md.version("mcp"), "mcp-types:", md.version("mcp-types"))
print("mcp Requires-Dist mcp-types:", [r for r in (md.requires("mcp") or []) if "mcp-types" in r])
names = ("create_windows_process", "terminate_windows_process_tree", "close_process_job")
print("windows helper callables:", [n for n in names if hasattr(u, n)])
print("exported from mcp/os/win32:", [hasattr(x, names[0]) for x in (mcp, mcp.os, mcp.os.win32)])
print("utilities __all__:", getattr(u, "__all__", None))
print("list_tools:", inspect.signature(ClientSession.list_tools))
print("PaginatedRequestParams fields:", list(PaginatedRequestParams.model_fields))
print("InitializeResult aliases:", [(f, v.alias) for f, v in InitializeResult.model_fields.items()])
print("ListToolsResult aliases:", [(f, v.alias) for f, v in ListToolsResult.model_fields.items()])
print("Implementation fields:", list(Implementation.model_fields))
for raw in ({}, {"name": "", "version": ""}, {"name": "x"}):
    try:
        obj = Implementation.model_validate(raw)
        print("Implementation", raw, "->", obj.model_dump(by_alias=True, exclude_unset=True))
    except Exception as e:
        print("Implementation", raw, "->", type(e).__name__, str(e).splitlines()[0])
