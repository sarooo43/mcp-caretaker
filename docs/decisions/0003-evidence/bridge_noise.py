"""T0 g/i: PR 1 bridge with stdout noise, and shutdown source facts."""
import inspect, json, os, pathlib, sys
import anyio
from mcp.shared import jsonrpc_dispatcher as jd
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.session import ServerSession

SERVER = str(pathlib.Path(__file__).with_name("raw_tools_server.py"))
TOOL = {"name": "a", "description": "A clear description.", "inputSchema": {"type": "object", "properties": {}}}
PAGES = json.dumps([{"tools": [TOOL]}])

def describe(e):
    nested = getattr(e, "exceptions", None) or []
    kinds = "+".join(type(x).__name__ for x in nested) if nested else type(e).__name__
    return kinds, str(e).splitlines()[0][:100]

async def case(noise):
    env = {"T0_PAGES_JSON": PAGES}
    if noise:
        env["T0_STDOUT_NOISE"] = "PLAIN TEXT BEFORE SERVING"
    spec = LaunchSpec(argv=(sys.executable, SERVER), extra_env=env, startup_timeout=2, call_timeout=2)
    try:
        async with ServerSession(spec, confirmed=True) as s:
            result = await s.list_tools()
            print("noise=", bool(noise), "handshake=ok tools=", [t.name for t in result.tools])
    except BaseException as e:
        kind, first = describe(e)
        print("noise=", bool(noise), "bridge outcome=", kind, "|", first)

def shutdown_facts():
    src = inspect.getsource(ServerSession._stop_process_tree)
    print("shutdown closes stdin:", "process.stdin.aclose()" in src)
    print("shutdown waits before kill:", "move_on_after(1.0)" in src)
    print("shutdown kills tree:", "killpg" in src or "terminate_windows_process_tree" in src)
    dispatcher = inspect.getsource(jd)
    print("SDK ignores stream exception without observer:", 'logger.debug("transport yielded exception' in dispatcher)

async def main():
    await case(False)
    await case(True)

if __name__ == "__main__":
    shutdown_facts()
    anyio.run(main)
