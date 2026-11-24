"""T0 e: SDK list_tools against malformed raw tool dicts."""
import asyncio, json, os, pathlib, sys, tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(pathlib.Path(__file__).with_name("raw_tools_server.py"))
BASE = {"inputSchema": {"type": "object", "properties": {}}, "unknownField": "x"}
CASES = {
    "no_description": [{"name": "a", **BASE}],
    "no_inputSchema": [{"name": "b", "description": "A clear description.", "unknownField": "x"}],
    "string_schema": [{"name": "c", "description": "A clear description.", "inputSchema": {"type": "string"}, "unknownField": "x"}],
    "duplicate_names": [{"name": "dup", "description": "A clear description.", **BASE}, {"name": "dup", "description": "Another clear description.", **BASE}],
    "non_string_description": [{"name": "d", "description": 123, **BASE}],
}

def describe(e):
    chain, leaves = [], []
    def walk(x):
        chain.append(type(x).__name__)
        children = getattr(x, "exceptions", None) or []
        if children:
            for y in children:
                walk(y)
        else:
            leaves.append(x)
    walk(e)
    leaf = leaves[-1] if leaves else e
    detail = " | ".join(str(leaf).splitlines()[:3])[:200]
    return ">".join(chain) + ": " + detail

async def one(label, tools):
    env = {"T0_PAGES_JSON": json.dumps({"tools": tools})}
    with tempfile.TemporaryDirectory() as tmp, open(os.devnull, "w") as errlog:
        params = StdioServerParameters(command=sys.executable, args=[SERVER], env=env, cwd=tmp)
        async with stdio_client(params, errlog=errlog) as (r, w), ClientSession(r, w) as c:
            await c.initialize()
            result = await c.list_tools()
            got = [t.model_dump(by_alias=True, exclude_none=False) for t in result.tools]
            lost = sorted(set(tools[0]) - set(got[0]))
            added = sorted(set(got[0]) - set(tools[0]))
            print(label, "returned tools=", len(got), "names=", [t["name"] for t in got], "lost=", lost, "added=", added)
            print(label, "first=", json.dumps(got[0], sort_keys=True)[:220])
    return

for label, tools in CASES.items():
    try:
        asyncio.run(one(label, tools))
    except BaseException as e:
        print(label, "raises", describe(e))
