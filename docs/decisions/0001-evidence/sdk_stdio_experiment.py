"""T0 evidence: SDK stdio_client env / cwd / stderr / errors / grandchild."""

import json
import pathlib
import sys
import tempfile

import anyio
import psutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TINY = str(pathlib.Path(__file__).with_name("tiny_server.py"))


def text(result):
    return "".join(getattr(block, "text", "") for block in result.content)


async def one(label, env):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="t0-"))
    errfile = tmp / "stderr.txt"
    merged = dict(env or {}) | {"CARETAKER_PIDFILE": str(tmp / "pid")}
    params = StdioServerParameters(command=sys.executable, args=[TINY], env=merged, cwd=str(tmp))
    with errfile.open("w", encoding="utf-8") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                print(label, "handshake:", init.protocol_version)
                tools = await session.list_tools()
                print(label, "readOnlyHint:", [(t.name, t.annotations.read_only_hint if t.annotations else None) for t in tools.tools])
                print(label, "child env NAMES:", json.loads(text(await session.call_tool("env_names"))))
                print(label, "child cwd is temp dir:", (tmp / "").resolve() == pathlib.Path(text(await session.call_tool("cwd"))).resolve())
                await session.call_tool("shout_env", {"name": "T0_FAKE_SECRET"})
                bad = await session.call_tool("add", {"a": "WRONG_TYPE", "b": 2})
                print(label, "wrong-typed args sent, isError:", bad.is_error)
                missing = await session.call_tool("no_such_tool", {})
                print(label, "unknown tool sent, isError:", missing.is_error)
                gpid = int(text(await session.call_tool("spawn_grandchild")))
                print(label, "grandchild alive inside:", psutil.pid_exists(gpid))
    print(label, "grandchild alive AFTER context exit:", psutil.pid_exists(gpid))
    print(label, "stderr file lines:", errfile.read_text(encoding="utf-8").splitlines())


async def main():
    await one("env=None", None)
    await one("env=given", {"T0_FAKE_SECRET": "FAKE-TOKEN-NOT-REAL-1234", "T0_EXTRA": "x"})


if __name__ == "__main__":
    anyio.run(main)
