"""Pytest configuration: the anyio plugin ships with the SDK's dependencies."""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Use the asyncio backend; no pytest-asyncio is needed."""
    return "asyncio"
