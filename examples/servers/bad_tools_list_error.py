"""Raw fixture whose tools/list answers with a JSON-RPC error.

Test fixture, not a template.
"""

from __future__ import annotations

from _raw_tools import serve

if __name__ == "__main__":
    serve(
        tools_error={
            "code": -32000,
            "message": "tools/list unavailable in this fixture",
        }
    )
