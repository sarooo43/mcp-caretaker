"""Raw fixture that keeps running after stdin EOF. Test fixture, not a template."""

from __future__ import annotations

import os

from _raw_tools import serve

if __name__ == "__main__":
    serve(
        ignore_stdin_close=True,
        pidfile=os.environ.get("CARETAKER_TEST_PIDFILE"),
    )
