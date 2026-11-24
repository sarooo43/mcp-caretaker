"""T0 evidence: real subprocesses through the SDK's stdio_client helper.

Runs the tiny_server fixture twice: once with env=None and once with env=given.
Prints names/booleans and one deliberately fake token; no real secrets.
"""

import asyncio, os, pathlib, sys, tempfile
import psutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TINY = str(pathlib.Path(__file__).with_name("tiny_server.py"))


async def one(label, extra):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="t0-sdk-"))
    pidfile = tmp / "grandchild.pid"
    env = {"CARETAKER_PIDFILE": str(pidfile), **extra}
    params = StdioServerParameters(command=sys.executable, args=[TINY], env=env or None, cwd=tmp)
    errlog = (tmp / "stderr.log").open("w", encoding="utf-8")
    async with stdio_client(params, errlog=errlog) as (read, write), ClientSession(read, write) as client:
        init = await client.initialize()
        print(f"{label} handshake:", init.protocol_version)
        tools = await client.list_tools()
        print(f"{label} readOnlyHint:", [(t.name, (t.annotations.read_only_hint if t.annotations else None)) for t in tools.tools])
        names = await client.call_tool("env_names")
        print(f"{label} child env NAMES:", "".join(x.text for x in names.content))
        cwd = await client.call_tool("cwd")
        print(f"{label} child cwd is temp dir:", "".join(x.text for x in cwd.content) == str(tmp))
        await client.call_tool("shout_env", {"name": "T0_FAKE_SECRET"})
        bad = await client.call_tool("add", {"a": "not-an-int", "b": 1})
        print(f"{label} wrong-typed args sent, isError:", bad.is_error)
        missing = await client.call_tool("no_such_tool", {})
        print(f"{label} unknown tool sent, isError:", missing.is_error)
        spawned = await client.call_tool("spawn_grandchild")
        gpid = int("".join(x.text for x in spawned.content))
        print(f"{label} grandchild alive inside:", psutil.pid_exists(gpid))
    print(f"{label} grandchild alive AFTER context exit:", psutil.pid_exists(gpid))
    errlog.close()
    print(f"{label} stderr file lines:", [ln.strip() for ln in pathlib.Path(errlog.name).read_text().splitlines()])
    try: os.kill(gpid, 9)
    except (ProcessLookupError, PermissionError): pass


async def main():
    await one("env=None", {})
    await one("env=given", {"T0_EXTRA": "FAKE-NOT-REAL-1", "T0_FAKE_SECRET": "FAKE-TOKEN-NOT-REAL-1234"})


if __name__ == "__main__":
    asyncio.run(main())
