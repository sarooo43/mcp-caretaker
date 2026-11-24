"""Raw fixture with empty serverInfo name and version. Test fixture, not a template."""

from __future__ import annotations

from _raw_tools import serve

if __name__ == "__main__":
    serve(server_name="", server_version="")
