"""T0 b/c/g: timeout usability, child death, and exited_by_itself. Evidence only."""
import anyio, pathlib, sys, time
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.session import ServerSession, _error_text

SERVERS = pathlib.Path(__file__).resolve().parents[3] / "examples" / "servers"
RAW = pathlib.Path(__file__).with_name("raw_probe_server.py")

def describe(exc):
    return type(exc).__name__ + ": " + _error_text(exc)[:100]

def spec(script, env=None):
    return LaunchSpec(argv=(sys.executable, str(script)), extra_env=env or {},
                      startup_timeout=5, call_timeout=2, shutdown_grace=2)

async def timeout_case():
    async with ServerSession(spec(SERVERS / "probe_server.py"), confirmed=True) as s:
        started = time.monotonic()
        try:
            await s.call_tool("sleep", {"seconds": 1.0}, timeout=0.2)
        except BaseException as exc:
            print("timeout_call", describe(exc), "elapsed", round(time.monotonic() - started, 2))
        for label in ("after_timeout_list_tools", "after_late_answer_list_tools"):
            try:
                with anyio.fail_after(2):
                    found = await s.list_tools()
                print(label, "ok", len(found.tools))
            except BaseException as exc:
                print(label, describe(exc))
            await anyio.sleep(1.2)
        print("stdout_noise_count", s.stdout_noise_count)

async def exit_case():
    s = ServerSession(spec(RAW, {"PR3_MODE": "exit_call"}), confirmed=True)
    try:
        async with s:
            started = time.monotonic()
            try:
                await s.call_tool("echo", {"text": "x"})
            except BaseException as exc:
                print("exit_during_call", describe(exc), "elapsed", round(time.monotonic() - started, 2))
            print("child_returncode_before_shutdown", getattr(s._process, "returncode", None))
            started = time.monotonic()
            try:
                with anyio.fail_after(2):
                    await s.list_tools()
                print("dead_child_list_tools", "ok")
            except BaseException as exc:
                print("dead_child_list_tools", describe(exc), "elapsed", round(time.monotonic() - started, 2))
    finally:
        print("exited_by_itself", getattr(s, "exited_by_itself", None))

async def main():
    await timeout_case()
    await exit_case()

anyio.run(main)
