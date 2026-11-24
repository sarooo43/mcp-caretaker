"""Pure unit test for the bounded bridge tap."""

from __future__ import annotations

import json

from mcp_caretaker.session import (
    _STDOUT_NOISE_CHARS,
    _STDOUT_NOISE_LINES,
    _BridgeTap,
)


def test_bridge_tap_is_bounded_and_tracks_raw_pages() -> None:
    tap = _BridgeTap()
    tap.note_request(
        json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/list"}).encode()
    )
    page = {
        "tools": [
            {
                "name": "ok",
                "description": "A clear description for this tool.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]
    }
    response = {"jsonrpc": "2.0", "id": 7, "result": page}
    assert tap.inspect_line(json.dumps(response)) is not None
    assert tap.raw_tools_pages == [page]

    tap.inspect_line("noise 0 " + "X" * 300)
    for index in range(1, 25):
        tap.inspect_line(f"noise {index}")
    assert tap.stdout_noise_count == 25
    assert len(tap.stdout_noise) == _STDOUT_NOISE_LINES
    assert len(tap.stdout_noise[0]) == _STDOUT_NOISE_CHARS
    assert all(len(line) <= _STDOUT_NOISE_CHARS for line in tap.stdout_noise)
