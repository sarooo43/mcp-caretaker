"""T0 b: installed SDK dispatcher handling of late answers. Evidence only."""
import inspect
from mcp.shared import jsonrpc_dispatcher as jd

for line in inspect.getsource(jd).splitlines():
    stripped = line.strip()
    if "late" in stripped.lower() or "_pending.pop" in stripped:
        print(stripped[:160])
