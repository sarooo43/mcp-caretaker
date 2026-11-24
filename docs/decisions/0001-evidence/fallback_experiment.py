"""T0 evidence: our own spawn + SDK ClientSession over memory object streams."""

import os
import pathlib
import signal
import sys
import tempfile

import anyio
import psutil
from anyio.streams.text import TextReceiveStream
from mcp import ClientSession
from mcp.shared.message import SessionMessage
from mcp_types import jsonrpc_message_adapter

TINY = str(pathlib.Path(__file__).with_name("tiny_server.py"))


def stripped(tmp):
    env = {"PATH": os.environ.get("PATH", ""), "TEMP": str(tmp), "TMP": str(tmp), "TMPDIR": str(tmp)}
    env["CARETAKER_PIDFILE"] = str(tmp / "pid")
    return env


async def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="t0-fallback-"))
    errfile = tmp / "stderr.bin"
    errlog = errfile.open("wb")
    proc = await anyio.open_process([sys.executable, TINY], env=stripped(tmp), cwd=str(tmp),
                                    stderr=errlog, start_new_session=True)
    print("spawned in own session/group:", proc.pid == os.getpgid(proc.pid))
    rs, rr = anyio.create_memory_object_stream[SessionMessage | Exception](0)
    ws, wr = anyio.create_memory_object_stream[SessionMessage](0)

    async def reader():
        buf = ""
        async with rs:
            async for chunk in TextReceiveStream(proc.stdout, encoding="utf-8", errors="replace"):
                lines = (buf + chunk).split("\n")
                buf = lines.pop()
                for line in lines:
                    if line.strip():
                        await rs.send(SessionMessage(jsonrpc_message_adapter.validate_json(line, by_name=False)))

    async def writer():
        async with wr:
            async for msg in wr:
                await proc.stdin.send((msg.message.model_dump_json(by_alias=True, exclude_unset=True) + "\n").encode())

    tg = anyio.create_task_group()
    await tg.__aenter__()
    tg.start_soon(reader)
    tg.start_soon(writer)
    client = ClientSession(rr, ws)
    await client.__aenter__()
    init = await client.initialize()
    print("SDK ClientSession handshake over our streams:", init.protocol_version)
    r = await client.call_tool("env_names")
    print("child env NAMES:", "".join(b.text for b in r.content))
    r = await client.call_tool("spawn_grandchild")
    gpid = int("".join(b.text for b in r.content))
    print("grandchild alive inside:", psutil.pid_exists(gpid))
    await client.__aexit__(None, None, None)
    tg.cancel_scope.cancel()
    await tg.__aexit__(None, None, None)
    with anyio.move_on_after(2):
        while proc.returncode is None:
            await anyio.sleep(0.01)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
    print("grandchild alive AFTER group kill:", psutil.pid_exists(gpid))
    errlog.close()


if __name__ == "__main__":
    anyio.run(main)
