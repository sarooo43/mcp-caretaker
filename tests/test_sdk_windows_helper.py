"""Pure import test for the isolated SDK Windows helper."""

from __future__ import annotations

from mcp_caretaker._sdk_windows import windows_helpers


def test_sdk_windows_helper_is_importable() -> None:
    helpers = windows_helpers()
    assert len(helpers) == 3
    assert all(callable(helper) for helper in helpers)
