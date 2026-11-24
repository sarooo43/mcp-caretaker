"""Raw fixture for a tools/list error or an empty tool list.

Test fixture, not a template.
"""

from __future__ import annotations

import os

from _raw_tools import serve

if __name__ == "__main__":
    if os.environ.get("CARETAKER_TEST_ZERO_TOOLS") == "1":
        serve(pages=[{"tools": []}])
    else:
        serve(
            tools_error={
                "code": -32000,
                "message": "tools/list unavailable in this fixture",
            }
        )
