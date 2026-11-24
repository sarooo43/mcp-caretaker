"""T0 c/f/g: raw stdlib probe server. Test fixture, not a template."""
import json, os, sys, time

TOOL = {"name": "echo", "description": "Return a short text length.",
        "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}},
                        "required": ["text"]},
        "annotations": {"readOnlyHint": True}}

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def ok(mid, value):
    send({"jsonrpc": "2.0", "id": mid, "result": value})

def err(mid, code, message):
    send({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}})

mode = os.environ.get("PR3_MODE", "echo")
for line in sys.stdin:
    try:
        msg = json.loads(line)
    except ValueError:
        continue
    if not isinstance(msg, dict) or "id" not in msg:
        continue
    mid, method = msg["id"], msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        ok(mid, {"protocolVersion": params.get("protocolVersion", "test-protocol"),
                 "capabilities": {"tools": {}},
                 "serverInfo": {"name": "raw-probe", "version": "1.0"}})
    elif method == "tools/list":
        ok(mid, {"tools": [TOOL]})
    elif method == "tools/call":
        if mode == "exit_call":
            os._exit(7)
        if mode == "jsonrpc_error":
            err(mid, -32602, "Unknown tool: caretaker_no_such_tool")
            continue
        if mode == "slow_call":
            time.sleep(float(os.environ.get("PR3_DELAY", "3")))
        args = params.get("arguments") or {}
        text = args.get("text")
        length = len(text) if isinstance(text, str) else None
        ok(mid, {"content": [{"type": "text", "text": "len=" + str(length)}],
                 "isError": False})
    elif method == "ping":
        ok(mid, {})
    else:
        err(mid, -32601, "method not found")
