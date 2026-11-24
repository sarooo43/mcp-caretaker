"""Behaviour tests: every one of these starts a REAL subprocess."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import time

import psutil
import pytest
from helpers import result_text, server_argv, wait_until

from mcp_caretaker.errors import (
    CallTimeout,
    ConfirmationRequired,
    ServerExited,
    StartupTimeout,
)
from mcp_caretaker.launch import LaunchSpec
from mcp_caretaker.session import STDERR_CAP, ServerSession


def _read_only_hint(tool: object) -> bool | None:
    annotations = getattr(tool, "annotations", None)
    return (
        getattr(annotations, "read_only_hint", None)
        if annotations is not None
        else None
    )


@pytest.mark.anyio
async def test_unconfirmed_session_never_spawns_process(tmp_path) -> None:
    marker = tmp_path / "marker.txt"
    code = "import pathlib, sys; pathlib.Path(sys.argv[1]).write_text('ran')"
    argv = (sys.executable, "-c", code, str(marker))
    temp_root = pathlib.Path(tempfile.gettempdir())
    before = set(temp_root.glob("mcp-caretaker-*"))

    with pytest.raises(ConfirmationRequired):
        ServerSession(LaunchSpec(argv=argv), confirmed=False)
    assert not marker.exists()
    assert set(temp_root.glob("mcp-caretaker-*")) == before

    # The gate is meaningful: with confirmed=True a REAL subprocess does run.
    session = ServerSession(LaunchSpec(argv=argv, startup_timeout=5), confirmed=True)
    with pytest.raises(ServerExited):
        async with session:
            pass
    assert marker.exists()
    assert session.temp_dir is not None
    assert not session.temp_dir.exists()


@pytest.mark.anyio
async def test_good_server_handshake_and_list_tools() -> None:
    spec = LaunchSpec(argv=server_argv("good_server.py"))
    async with ServerSession(spec, confirmed=True) as session:
        assert session.initialize_result is not None
        assert session.initialize_result.protocol_version
        tools = await session.list_tools()
        by_name = {tool.name: tool for tool in tools.tools}
        assert set(by_name) == {"echo", "add", "save_note"}
        for name in ("echo", "add", "save_note"):
            assert by_name[name].description
        assert _read_only_hint(by_name["echo"]) is True
        assert _read_only_hint(by_name["add"]) is True
        assert not _read_only_hint(by_name["save_note"])


@pytest.mark.anyio
async def test_child_does_not_see_parent_env_names(monkeypatch) -> None:
    monkeypatch.setenv("CARETAKER_PARENT_ONLY_FAKE", "FAKE-PARENT-VALUE-NOT-A-SECRET")
    spec = LaunchSpec(
        argv=server_argv("probe_server.py"),
        extra_env={"CARETAKER_CHILD_FAKE": "FAKE-CHILD-VALUE-1234"},
    )
    async with ServerSession(spec, confirmed=True) as session:
        names = json.loads(result_text(await session.call_tool("env_names", {})))
    assert "CARETAKER_PARENT_ONLY_FAKE" not in names
    assert "CARETAKER_CHILD_FAKE" in names


@pytest.mark.anyio
async def test_child_cwd_is_fresh_empty_temp_dir() -> None:
    spec = LaunchSpec(argv=server_argv("probe_server.py"))
    async with ServerSession(spec, confirmed=True) as session:
        reported = pathlib.Path(result_text(await session.call_tool("cwd", {})))
        assert session.workdir is not None
        assert reported.resolve() == session.workdir.resolve()
        assert session.workdir.is_dir()
        assert list(session.workdir.iterdir()) == []
        assert session.workdir.parent.name.startswith("mcp-caretaker-")


@pytest.mark.anyio
async def test_extra_env_reaches_child() -> None:
    secret = "FAKE-CANARY-VALUE-987654321"
    spec = LaunchSpec(
        argv=server_argv("probe_server.py"),
        extra_env={"CARETAKER_FAKE_SECRET": secret},
    )
    async with ServerSession(spec, confirmed=True) as session:
        names = json.loads(result_text(await session.call_tool("env_names", {})))
        assert "CARETAKER_FAKE_SECRET" in names
        # The child could only write the value if it really reached its env.
        await session.call_tool("shout_env", {"name": "CARETAKER_FAKE_SECRET"})
        assert "[REDACTED:CARETAKER_FAKE_SECRET]" in session.stderr_text
        assert secret not in repr(spec)
        assert secret not in str(spec)
        with pytest.raises(CallTimeout) as caught:
            await session.call_tool("sleep", {"seconds": 5}, timeout=0.2)
        assert secret not in str(caught.value)


@pytest.mark.anyio
async def test_extra_env_value_redacted_from_captured_stderr() -> None:
    secret = "FAKE-STDERR-CANARY-ABCDEF"
    spec = LaunchSpec(
        argv=server_argv("probe_server.py"),
        extra_env={"CARETAKER_FAKE_SECRET": secret},
    )
    async with ServerSession(spec, confirmed=True) as session:
        await session.call_tool("shout_env", {"name": "CARETAKER_FAKE_SECRET"})
        captured = session.stderr_text
    assert secret not in captured
    assert "[REDACTED:CARETAKER_FAKE_SECRET]" in captured
    assert "SHOUT_ENV_DONE" in captured
    # Still available, still redacted, after cleanup removed the temp folder.
    assert secret not in session.stderr_text


@pytest.mark.anyio
async def test_exit_before_handshake_raises_server_exited_with_code_3() -> None:
    spec = LaunchSpec(argv=server_argv("bad_exits_immediately.py"), startup_timeout=5)
    session = ServerSession(spec, confirmed=True)
    with pytest.raises(ServerExited) as caught:
        async with session:
            pass
    assert caught.value.exit_code == 3
    assert "exiting before any handshake" in caught.value.stderr_tail
    assert session.temp_dir is not None
    assert not session.temp_dir.exists()


@pytest.mark.anyio
async def test_startup_hang_raises_startup_timeout() -> None:
    spec = LaunchSpec(argv=server_argv("bad_hangs_on_startup.py"), startup_timeout=2)
    started = time.monotonic()
    session = ServerSession(spec, confirmed=True)
    with pytest.raises(StartupTimeout):
        async with session:
            pass
    assert time.monotonic() - started < 15


@pytest.mark.anyio
async def test_call_timeout_raises_call_timeout() -> None:
    spec = LaunchSpec(argv=server_argv("probe_server.py"), call_timeout=0.3)
    async with ServerSession(spec, confirmed=True) as session:
        with pytest.raises(CallTimeout):
            await session.call_tool("sleep", {"seconds": 5})


@pytest.mark.anyio
async def test_grandchild_is_killed_on_exit(tmp_path) -> None:
    pidfile = tmp_path / "grandchild.pid"
    spec = LaunchSpec(
        argv=server_argv("spawns_grandchild.py"),
        extra_env={"CARETAKER_TEST_PIDFILE": str(pidfile)},
    )
    async with ServerSession(spec, confirmed=True) as session:
        assert result_text(await session.call_tool("ping", {})) == "pong"
        assert pidfile.exists()
        grandchild_pid = int(pidfile.read_text(encoding="utf-8"))
        assert psutil.pid_exists(grandchild_pid)

    def gone() -> bool:
        if not psutil.pid_exists(grandchild_pid):
            return True
        try:
            # A reaped-as-zombie descendant is already dead on some runners.
            return psutil.Process(grandchild_pid).status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return True

    assert await wait_until(gone, timeout=5.0)


@pytest.mark.anyio
async def test_temp_folder_removed_after_normal_exit_and_after_error() -> None:
    good = ServerSession(LaunchSpec(argv=server_argv("good_server.py")), confirmed=True)
    async with good:
        assert good.temp_dir is not None
        assert good.temp_dir.is_dir()
    assert good.temp_dir is not None
    assert not good.temp_dir.exists()

    bad = ServerSession(
        LaunchSpec(argv=server_argv("bad_exits_immediately.py"), startup_timeout=5),
        confirmed=True,
    )
    with pytest.raises(ServerExited):
        async with bad:
            pass
    assert bad.temp_dir is not None
    assert not bad.temp_dir.exists()


@pytest.mark.anyio
async def test_stderr_capture_is_capped_at_64kib_and_flags_truncation() -> None:
    secret = "FAKE-CAP-CANARY-VALUE-123456"
    spec = LaunchSpec(
        argv=server_argv("probe_server.py"),
        extra_env={
            "CARETAKER_FAKE_SECRET": secret,
            "CARETAKER_STDERR_PADDING": "80000",
        },
    )
    async with ServerSession(spec, confirmed=True) as session:
        await session.call_tool("shout_env", {"name": "CARETAKER_FAKE_SECRET"})
        captured = session.stderr_text
        assert session.stderr_truncated is True
    assert len(captured.encode("utf-8")) <= STDERR_CAP
    # The TAIL is kept, the beginning is dropped.
    assert "SHOUT_ENV_DONE" in captured
    assert "STDERR_START" not in captured
    assert secret not in captured
    assert session.stderr_truncated is True
