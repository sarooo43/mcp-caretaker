"""Bad MCP fixture: reads stdin forever and never answers an MCP request.

Intentionally bad (standard library only, no MCP server at all). test fixture, not
a template.
"""

from __future__ import annotations

import sys


def main() -> None:
    stream = sys.stdin.buffer
    while stream.read(1):
        # Deliberately never write anything to stdout: no handshake, ever.
        continue


if __name__ == "__main__":
    main()
