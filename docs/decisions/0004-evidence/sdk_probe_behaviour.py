"""T0 d/e/f: huge input, wrong values, wire shape and unknown tool. Evidence only."""
import anyio, json, pathlib, sys, time
from mcp.shared.exceptions import MCPError
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.session import ServerSession

SDK = pathlib.Path(__file__).with_name("sdk_probe_server.py")
RAW = pathlib.Path(__file__).with_name("raw_probe_server.py")
HUGE = 1048576
WRONG = [("echo", {"text": {"caretaker_wrong_type": True}}),
         ("integer_tool", {"value": "not-a-number"}),
         ("number_tool", {"value": "not-a-number"}),
         ("boolean_tool", {"value": "not-a-bool"}),
         ("array_tool", {"value": "not-an-array"}),
         ("object_tool", {"value": "not-an-object"})]

def text(result):
    return "".join(getattr(block, "text", "") for block in getattr(result, "content", []))

def spec(script, env=None, timeout=20):
    return LaunchSpec(argv=(sys.executable, str(script)), extra_env=env or {},
                      startup_timeout=10, call_timeout=timeout, shutdown_grace=2)

async def main():
    async with ServerSession(spec(SDK), confirmed=True) as s:
        pages, _, error = await s.collect_tools_pages()
        tools = [t for page in pages for t in page.get("tools", [])]
        echo = next(t for t in tools if t.get("name") == "echo")
        print("tools_list_error", error)
        print("tools", len(tools), "annotations", json.dumps(echo.get("annotations"), sort_keys=True))
        print("key_path", "annotations.readOnlyHint", "exact_true", echo.get("annotations", {}).get("readOnlyHint") is True)
        print("inputSchema", json.dumps(echo["inputSchema"], sort_keys=True))
        started = time.monotonic()
        result = await s.call_tool("echo", {"text": "A" * HUGE})
        print("huge_roundtrip_chars", len(text(result)), "elapsed", round(time.monotonic() - started, 2))
        for name, arguments in WRONG:
            try:
                answer = await s.call_tool(name, arguments)
                coerced = getattr(answer, "is_error", False) is False
                print("wrong", name, "is_error", getattr(answer, "is_error", None), "coerced_to_success", coerced)
            except BaseException as exc:
                print("wrong", name, "raises", type(exc).__name__)
        try:
            answer = await s.call_tool("caretaker_no_such_tool", {})
            print("sdk_unknown_tool", "CallToolResult", "is_error", getattr(answer, "is_error", None), "text", text(answer)[:100])
        except MCPError as exc:
            print("sdk_unknown_tool", type(exc).__name__, "code", exc.error.code, "message", exc.error.message)
    async with ServerSession(spec(RAW, {"PR3_MODE": "jsonrpc_error"}, 2), confirmed=True) as s:
        try:
            await s.call_tool("caretaker_no_such_tool", {})
            print("raw_unknown_tool", "success")
        except MCPError as exc:
            print("raw_unknown_tool", type(exc).__name__, "code", exc.error.code, "message", exc.error.message)

anyio.run(main)
