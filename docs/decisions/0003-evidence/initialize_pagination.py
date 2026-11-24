"""T0 f/h: initialize attributes, missing serverInfo and pagination cursor."""
import asyncio, json, os, pathlib, sys, tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import PaginatedRequestParams

SERVER = str(pathlib.Path(__file__).with_name("raw_tools_server.py"))
TOOL = {"name": "a", "description": "A clear description.", "inputSchema": {"type": "object", "properties": {}}}
PAGES = [{"tools": [TOOL], "nextCursor": "1"}, {"tools": [dict(TOOL, name="b")]}]

async def init_case(info):
    env = {"T0_SERVER_INFO_JSON": json.dumps(info), "T0_PAGES_JSON": json.dumps([{"tools": []}])}
    with tempfile.TemporaryDirectory() as tmp, open(os.devnull, "w") as errlog:
        params = StdioServerParameters(command=sys.executable, args=[SERVER], env=env, cwd=tmp)
        async with stdio_client(params, errlog=errlog) as (r, w), ClientSession(r, w) as c:
            result = await c.initialize()
            print("init", json.dumps(info, sort_keys=True), "-> protocol=", result.protocol_version,
                  "serverInfo.name=", repr(result.server_info.name), "serverInfo.version=", repr(result.server_info.version))

async def pagination():
    env = {"T0_PAGES_JSON": json.dumps(PAGES)}
    with tempfile.TemporaryDirectory() as tmp, open(os.devnull, "w") as errlog:
        params = StdioServerParameters(command=sys.executable, args=[SERVER], env=env, cwd=tmp)
        async with stdio_client(params, errlog=errlog) as (r, w), ClientSession(r, w) as c:
            await c.initialize()
            p1 = await c.list_tools()
            print("page1 tools=", [t.name for t in p1.tools], "next_cursor=", repr(p1.next_cursor))
            p2 = await c.list_tools(params=PaginatedRequestParams(cursor=p1.next_cursor))
            print("page2 tools=", [t.name for t in p2.tools], "next_cursor=", repr(p2.next_cursor))

for info in ({"name": "raw", "version": "1"}, {"name": "", "version": ""}, {}, {"name": "x"}):
    try:
        asyncio.run(init_case(info))
    except BaseException as e:
        nested = getattr(e, "exceptions", None) or []
        inner = getattr(nested[0], "exceptions", None) or [] if nested else []
        kinds = "+".join(type(x).__name__ for x in (inner or nested)) or type(e).__name__
        print("init", json.dumps(info, sort_keys=True), "raises", kinds, "|", str(e).splitlines()[0][:100])
try:
    asyncio.run(pagination())
except BaseException as e:
    print("pagination raises", type(e).__name__, str(e).splitlines()[0][:100])
