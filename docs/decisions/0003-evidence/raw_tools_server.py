"""T0 raw stdlib MCP server. Test fixture, not a template."""
import json, os, sys, time

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def result(mid, value):
    send({"jsonrpc": "2.0", "id": mid, "result": value})

def error(mid, code, message):
    send({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}})

def load(name, default):
    return json.loads(os.environ.get(name, default))

noise = os.environ.get("T0_STDOUT_NOISE")
if noise:
    print(noise, flush=True)
pages = load("T0_PAGES_JSON", '[{"tools": []}]')
if isinstance(pages, dict):
    pages = [pages]
info = load("T0_SERVER_INFO_JSON", '{"name":"raw-fixture","version":"1.0"}')
tools_error = load("T0_TOOLS_LIST_ERROR_JSON", "null")

for line in sys.stdin:
    try:
        msg = json.loads(line)
    except ValueError:
        continue
    if "id" not in msg:
        continue
    mid, method = msg["id"], msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        result(mid, {"protocolVersion": params.get("protocolVersion", "2025-11-25"),
                     "capabilities": {"tools": {}}, "serverInfo": info})
    elif method == "tools/list":
        if tools_error is not None:
            error(mid, tools_error.get("code", -32601), tools_error.get("message", "tools/list error"))
        else:
            index = int(params.get("cursor") or 0)
            result(mid, pages[min(index, len(pages) - 1)])
    else:
        error(mid, -32601, "method not found")

if os.environ.get("T0_IGNORE_STDIN_CLOSE"):
    while True:
        time.sleep(1)
