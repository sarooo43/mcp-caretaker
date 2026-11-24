"""T0 evidence: SDK ClientSession over our own stripped spawn.

The SDK session lives in a runner task; that keeps its cancel scopes out of the
caller task. The runner deliberately does NOT close stdin before the process-group
kill, so this isolates tree-kill, not graceful shutdown, on Linux.
"""

import os, pathlib, signal, sys, tempfile
import anyio, psutil
from anyio.streams.text import TextReceiveStream
from mcp import ClientSession
from mcp.shared.message import SessionMessage
from mcp_types import jsonrpc_message_adapter

TINY = str(pathlib.Path(__file__).with_name("tiny_server.py"))


def stripped(tmp):
    env = {"PATH": os.environ.get("PATH", ""), "TEMP": str(tmp), "TMP": str(tmp), "TMPDIR": str(tmp)}
    env["CARETAKER_PIDFILE"] = str(tmp / "pid")
    return env


async def reader(proc, rs):
    buf = ""
    async with rs:
        async for chunk in TextReceiveStream(proc.stdout, encoding="utf-8", errors="replace"):
            lines = (buf + chunk).split("\n"); buf = lines.pop()
            for line in lines:
                if line.strip():
                    await rs.send(SessionMessage(jsonrpc_message_adapter.validate_json(line, by_name=False)))


async def writer(proc, wr):
    async with wr:
        async for msg in wr:
            await proc.stdin.send((msg.message.model_dump_json(by_alias=True, exclude_unset=True) + "\n").encode())


async def client_runner(rr, ws, ready, stop, gpid_out):
    async with ClientSession(rr, ws) as client:
        print("SDK ClientSession handshake over our streams:", (await client.initialize()).protocol_version)
        tools = await client.list_tools()
        print("readOnlyHint over our streams:", [(t.name, (t.annotations.read_only_hint if t.annotations else None)) for t in tools.tools])
        r = await client.call_tool("env_names")
        print("child env NAMES:", "".join(b.text for b in r.content))
        r = await client.call_tool("spawn_grandchild")
        gpid = int("".join(b.text for b in r.content))
        gpid_out.append(gpid)
        print("grandchild alive inside:", psutil.pid_exists(gpid))
        ready.set()
        await stop.wait()


async def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="t0-fallback-"))
    errlog = (tmp / "stderr.bin").open("wb")
    proc = await anyio.open_process([sys.executable, TINY], env=stripped(tmp), cwd=str(tmp),
                                    stderr=errlog, start_new_session=True)
    print("spawned in own session/group:", proc.pid == os.getpgid(proc.pid))
    rs, rr = anyio.create_memory_object_stream[SessionMessage | Exception](0)
    ws, wr = anyio.create_memory_object_stream[SessionMessage](0)
    ready, stop = anyio.Event(), anyio.Event()
    gpid_out = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(reader, proc, rs)
        tg.start_soon(writer, proc, wr)
        tg.start_soon(client_runner, rr, ws, ready, stop, gpid_out)
        await ready.wait()
        stop.set()
        tg.cancel_scope.cancel()
    gpid = gpid_out[0]
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try: os.killpg(proc.pid, sig)
        except ProcessLookupError: pass
    with anyio.move_on_after(3):
        while psutil.pid_exists(gpid):
            await anyio.sleep(0.01)
    with anyio.move_on_after(3):
        while proc.returncode is None:
            await anyio.sleep(0.01)
    print("grandchild alive AFTER group kill:", psutil.pid_exists(gpid))
    print("direct child returncode after group kill:", proc.returncode)
    errlog.close()


if __name__ == "__main__":
    anyio.run(main)
