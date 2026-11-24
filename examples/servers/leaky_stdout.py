"""Raw fixture with non-protocol stdout lines. Test fixture, not a template.

The text is an obvious fake test value supplied through extra_env. No real
secret is used. A control character and padding exercise evidence safety.
"""

from __future__ import annotations

import os

from _raw_tools import serve

value = os.environ.get("CARETAKER_FAKE_TEXT", "no-value")
noise = [
    "PLAIN TEXT BEFORE SERVING " + value,
    "CONTROL\u0001CHAR " + value + " " + "X" * 250,
]

if __name__ == "__main__":
    serve(stdout_noise=noise)
