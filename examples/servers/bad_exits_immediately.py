"""Bad MCP fixture: prints one stderr line and exits with code 3 before handshake.

Intentionally bad (standard library only, no MCP server at all). test fixture, not
a template.
"""

from __future__ import annotations

import sys


def main() -> None:
    sys.stderr.write("bad_exits_immediately: exiting before any handshake\n")
    sys.stderr.flush()
    sys.exit(3)


if __name__ == "__main__":
    main()
