"""A confirmed session with one locally spawned MCP server.

The launcher spawns the child itself (see docs/decisions/0001) because the SDK's
stdio helper always merges a default environment and leaves POSIX grandchildren
alive. We bridge the child's pipes into the SDK's ``ClientSession`` using the
SDK's own ``SessionMessage`` and JSON-RPC adapter.

The SDK session lives in a runner task, not in the caller's task: that keeps the
SDK's cancel scopes out of the caller's task, so cleanup cannot leave a stray
cancellation behind. A small bridge tap records raw ``tools/list`` result dicts
and non-protocol stdout lines; it never stores the whole stream.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import anyio
from anyio.streams.text import TextReceiveStream
from mcp import ClientSession
from mcp.shared.exceptions import MCPError
from mcp.shared.message import SessionMessage
from mcp_types import PaginatedRequestParams, jsonrpc_message_adapter

from ._sdk_windows import windows_helpers
from .errors import (
    CallTimeout,
    CaretakerError,
    ConfirmationRequired,
    ServerExited,
    StartupTimeout,
)
from .launch import LaunchSpec, build_child_env, redact_values
from .thresholds import MAX_TOOLS_PAGES

STDERR_CAP = 64 * 1024
_STDERR_TAIL_FOR_ERRORS = 2048
_STDOUT_NOISE_LINES = 5
_STDOUT_NOISE_CHARS = 200


@dataclass
class _BridgeTap:
    """Keep raw first-connection pages and a capped view of stdout noise."""

    raw_tools_pages: list[dict[str, Any]] = field(default_factory=list)
    raw_initialize_result: dict[str, Any] | None = None
    stdout_noise: list[str] = field(default_factory=list)
    stdout_noise_count: int = 0
    tools_list_error: str | None = None
    noise_observer: Callable[[str], None] | None = None
    _tools_list_ids: set[Any] = field(default_factory=set)
    _initialize_id: Any = None
    _initialize_pending: bool = False

    def reset_tools_list_error(self) -> None:
        self.tools_list_error = None

    def note_request(self, data: bytes) -> None:
        try:
            obj = json.loads(data)
        except (ValueError, TypeError, UnicodeDecodeError):
            return
        if isinstance(obj, dict) and "id" in obj:
            if obj.get("method") == "tools/list":
                with suppress(TypeError):
                    self._tools_list_ids.add(obj["id"])
            elif obj.get("method") == "initialize":
                self._initialize_id = obj["id"]
                self._initialize_pending = True

    def inspect_line(self, line: str) -> SessionMessage | None:
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            self._add_noise(line)
            return None
        if isinstance(obj, dict):
            mid = obj.get("id")
            if self._initialize_pending and mid == self._initialize_id:
                self._initialize_pending = False
                initialize_result = obj.get("result")
                if isinstance(initialize_result, dict):
                    self.raw_initialize_result = initialize_result
            try:
                tracked = mid in self._tools_list_ids
            except TypeError:
                tracked = False
            if tracked:
                self._tools_list_ids.discard(mid)
                result = obj.get("result")
                if isinstance(result, dict) and isinstance(result.get("tools"), list):
                    self.raw_tools_pages.append(result)
                elif "error" in obj:
                    error = obj.get("error")
                    if isinstance(error, dict):
                        code = error.get("code", "?")
                        message = error.get("message", "tools/list error")
                        self.tools_list_error = f"JSON-RPC {code}: {message}"[:200]
                    else:
                        self.tools_list_error = f"JSON-RPC error: {error}"[:200]
        try:
            return SessionMessage(
                jsonrpc_message_adapter.validate_json(line, by_name=False)
            )
        except Exception:  # noqa: BLE001 - any non-protocol line becomes noise
            self._add_noise(line)
            return None

    def _add_noise(self, line: str) -> None:
        if self.noise_observer is not None:
            self.noise_observer(line)
        self.stdout_noise_count += 1
        if len(self.stdout_noise) < _STDOUT_NOISE_LINES:
            self.stdout_noise.append(line[:_STDOUT_NOISE_CHARS])


def _walk_exceptions(exc: BaseException) -> Iterator[BaseException]:
    yield exc
    for child in getattr(exc, "exceptions", None) or []:
        yield from _walk_exceptions(child)


def _exception_has_type(exc: BaseException, kind: type[BaseException]) -> bool:
    return any(isinstance(item, kind) for item in _walk_exceptions(exc))


def _error_text(exc: BaseException) -> str:
    leaves = [
        item for item in _walk_exceptions(exc) if not getattr(item, "exceptions", None)
    ]
    leaf = leaves[-1] if leaves else exc
    lines = str(leaf).splitlines()
    first = lines[0] if lines else type(leaf).__name__
    return f"{type(leaf).__name__}: {first}"[:300]


async def _stdout_reader(process: Any, read_send: Any, tap: _BridgeTap) -> None:
    """Forward protocol lines, and count non-protocol lines, with a bounded tap."""
    buffer = ""
    text_stream = TextReceiveStream(process.stdout, encoding="utf-8", errors="replace")
    try:
        async with read_send:
            async for chunk in text_stream:
                lines = (buffer + chunk).split("\n")
                buffer = lines.pop()
                for line in lines:
                    if not line.strip():
                        continue
                    message = tap.inspect_line(line)
                    if message is not None:
                        await read_send.send(message)
    except (
        anyio.EndOfStream,
        anyio.ClosedResourceError,
        anyio.BrokenResourceError,
        OSError,
    ):
        return


async def _stdin_writer(process: Any, write_recv: Any, tap: _BridgeTap) -> None:
    """Forward the session's write stream into the child's stdin."""
    try:
        async with write_recv:
            async for message in write_recv:
                data = (
                    message.message.model_dump_json(by_alias=True, exclude_unset=True)
                    + "\n"
                ).encode("utf-8")
                tap.note_request(data)
                await process.stdin.send(data)
    except (
        anyio.EndOfStream,
        anyio.ClosedResourceError,
        anyio.BrokenResourceError,
        OSError,
    ):
        return


async def _spawn_process(
    argv: tuple[str, ...], env: dict[str, str], cwd: Path, errlog: Any
) -> Any:
    """Spawn argv directly, never through a shell and never as one command string."""
    command, args = str(argv[0]), list(argv[1:])
    if sys.platform == "win32":
        create, _, _ = windows_helpers()
        return await create(command, args, env=env, errlog=errlog, cwd=str(cwd))
    return await anyio.open_process(
        [command, *args],
        env=env,
        cwd=str(cwd),
        stderr=errlog,
        start_new_session=True,
    )


def _group_alive(pgid: int) -> bool:
    """Probe a POSIX process group; only ESRCH proves it is gone."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


async def remove_temp_area(path: Path | None) -> None:
    """Delete a temp area, retrying late Windows handle release for five seconds."""
    if path is None:
        return
    if sys.platform == "win32":
        deadline = time.monotonic() + 5.0
        while True:
            try:
                shutil.rmtree(path)
                return
            except OSError:
                if time.monotonic() >= deadline:
                    return
                await anyio.sleep(0.1)
    shutil.rmtree(path, ignore_errors=True)


class ServerSession:
    """Async context manager for one confirmed local MCP server session.

    ``confirmed=True`` is mandatory: without it the constructor raises
    ``ConfirmationRequired`` before any temp folder is created or process spawned.
    """

    def __init__(
        self,
        spec: LaunchSpec,
        *,
        confirmed: bool,
        temp_area: Path | None = None,
        stderr_name: str = "stderr.log",
    ) -> None:
        if confirmed is not True:
            raise ConfirmationRequired("launching a server requires confirmed=True")
        self.spec = spec
        self._owns_temp_area = temp_area is None
        self._external_temp_area = temp_area
        self._stderr_name = stderr_name
        self.initialize_result: Any = None
        self.exit_code: int | None = None
        self.exited_by_itself: bool | None = None
        self.exited_before_shutdown: bool = False

        self._tap = _BridgeTap()
        self._temp_area: Path | None = None
        self._workdir: Path | None = None
        self._stderr_path: Path | None = None
        self._errlog: Any = None
        self._process: Any = None
        self._task_group: Any = None
        self._client: ClientSession | None = None
        self._read_send: Any = None
        self._read_recv: Any = None
        self._write_send: Any = None
        self._write_recv: Any = None
        self._start_event: Any = None
        self._stop_event: Any = None
        self._start_error: BaseException | None = None
        self._stderr_text = ""
        self._stderr_truncated = False
        self._cleaned = False

    @property
    def temp_dir(self) -> Path | None:
        """The temp area we created (also available after cleanup for assertions)."""
        return self._temp_area

    @property
    def workdir(self) -> Path | None:
        """The fresh empty folder the child runs in."""
        return self._workdir

    @property
    def raw_tools_pages(self) -> list[dict[str, Any]]:
        """Raw wire ``result`` dicts for ``tools/list`` responses, in order."""
        return self._tap.raw_tools_pages

    @property
    def raw_initialize_result(self) -> dict[str, Any] | None:
        """Raw first-connection initialize result, when the tap saw one."""
        return self._tap.raw_initialize_result

    def set_noise_observer(self, observer: Callable[[str], None]) -> None:
        """Observe each full stray stdout line before the bounded display."""
        self._tap.noise_observer = observer

    @property
    def stdout_noise(self) -> list[str]:
        """Up to five non-protocol stdout lines, each cut at 200 characters."""
        return self._tap.stdout_noise

    @property
    def stdout_noise_count(self) -> int:
        """Count of all non-protocol stdout lines seen."""
        return self._tap.stdout_noise_count

    @property
    def tools_list_error(self) -> str | None:
        """A capped JSON-RPC error message for a tapped tools/list response."""
        return self._tap.tools_list_error

    @property
    def stderr_text(self) -> str:
        """Captured stderr, redacted, capped at 64 KiB, keeping the TAIL."""
        if self._stderr_path is not None and self._stderr_path.exists():
            self._refresh_stderr()
        return self._stderr_text

    @property
    def stderr_truncated(self) -> bool:
        """Whether captured stderr was longer than the 64 KiB cap."""
        if self._stderr_path is not None and self._stderr_path.exists():
            self._refresh_stderr()
        return self._stderr_truncated

    def _refresh_stderr(self) -> None:
        self._stderr_text, self._stderr_truncated = self._read_stderr()

    def _read_stderr(self) -> tuple[str, bool]:
        if self._stderr_path is None:
            return "", False
        try:
            data = self._stderr_path.read_bytes()
        except OSError:
            return "", False
        truncated = len(data) > STDERR_CAP
        tail = data[-STDERR_CAP:]
        text = tail.decode("utf-8", errors="replace")
        result = redact_values(text, self.spec.extra_env)
        # Redaction can make the text longer, so the 64 KiB cap is applied to
        # the exposed text as well (still keeping the tail).
        encoded = result.encode("utf-8")
        if len(encoded) > STDERR_CAP:
            result = encoded[-STDERR_CAP:].decode("utf-8", errors="replace")
            truncated = True
        return result, truncated

    def _read_stderr_tail(self) -> str:
        if self._stderr_path is None:
            return ""
        if self._errlog is not None:
            with suppress(Exception):
                self._errlog.flush()
        try:
            data = self._stderr_path.read_bytes()[-_STDERR_TAIL_FOR_ERRORS:]
        except OSError:
            return ""
        return redact_values(
            data.decode("utf-8", errors="replace"), self.spec.extra_env
        )

    def read_stderr_prefix(self, limit: int) -> tuple[str, int, bool] | None:
        """Read raw stderr from the start, up to limit, if the file is readable."""
        if self._stderr_path is None:
            return None
        if self._errlog is not None:
            with suppress(Exception):
                self._errlog.flush()
        try:
            with self._stderr_path.open("rb") as handle:
                handle.seek(0, 2)
                size = handle.tell()
                handle.seek(0)
                data = handle.read(limit)
        except OSError:
            return None
        return data.decode("utf-8", errors="replace"), len(data), size > limit

    def _safe(self, text: str) -> str:
        """Never let a secret value into an error message."""
        return redact_values(text, self.spec.extra_env)

    async def __aenter__(self) -> Self:
        if self._temp_area is not None or self._cleaned:
            raise CaretakerError("a ServerSession can only be entered once")
        if self._external_temp_area is None:
            self._temp_area = Path(tempfile.mkdtemp(prefix="mcp-caretaker-"))
        else:
            self._temp_area = Path(self._external_temp_area)
            self._temp_area.mkdir(parents=True, exist_ok=True)
        self._workdir = self._temp_area / "cwd"
        self._workdir.mkdir(exist_ok=True)
        self._stderr_path = self._temp_area / self._stderr_name
        self._errlog = self._stderr_path.open("wb")
        try:
            await self._start()
        except BaseException:
            # __aexit__ is NOT called when __aenter__ raises, so clean up here.
            await self._cleanup()
            raise
        return self

    async def _start(self) -> None:
        child_env = build_child_env(self.spec, self._temp_area)
        self._process = await _spawn_process(
            self.spec.argv, child_env, self._workdir, self._errlog
        )
        self._read_send, self._read_recv = anyio.create_memory_object_stream[
            SessionMessage | Exception
        ](0)
        self._write_send, self._write_recv = anyio.create_memory_object_stream[
            SessionMessage
        ](0)
        self._start_event = anyio.Event()
        self._stop_event = anyio.Event()

        self._task_group = anyio.create_task_group()
        await self._task_group.__aenter__()
        self._task_group.start_soon(
            _stdout_reader, self._process, self._read_send, self._tap
        )
        self._task_group.start_soon(
            _stdin_writer, self._process, self._write_recv, self._tap
        )
        self._task_group.start_soon(self._runner)

        try:
            with anyio.fail_after(self.spec.startup_timeout):
                await self._start_event.wait()
        except TimeoutError as exc:
            raise StartupTimeout(
                self._safe(
                    f"MCP handshake exceeded {self.spec.startup_timeout} seconds"
                )
            ) from exc

        if self._start_error is not None:
            code = await self._wait_for_exit(2.0)
            if code is not None:
                raise ServerExited(
                    code, self._read_stderr_tail()
                ) from self._start_error
            raise CaretakerError(
                self._safe(f"MCP handshake failed: {self._start_error}")
            ) from self._start_error

    async def _runner(self) -> None:
        """Own the SDK session's cancel scopes in a task of their own."""
        client = ClientSession(self._read_recv, self._write_send)
        try:
            async with client:
                self._client = client
                try:
                    self.initialize_result = await client.initialize()
                except BaseException as exc:  # noqa: BLE001 - cancellation must be reported
                    self._start_error = exc
                    self._start_event.set()
                    await self._stop_event.wait()
                    return
                self._start_event.set()
                await self._stop_event.wait()
        except BaseException as exc:  # noqa: BLE001 - cancellation must be reported
            if self._start_error is None:
                self._start_error = exc
            self._start_event.set()

    async def _wait_for_exit(self, seconds: float) -> int | None:
        if self._process is None:
            return None
        with anyio.move_on_after(seconds):
            while self._process.returncode is None:
                await anyio.sleep(0.01)
        return self._process.returncode

    async def _raise_dead_child(self, exc: BaseException) -> None:
        code = await self._wait_for_exit(0.2)
        if code is not None:
            raise ServerExited(code, self._read_stderr_tail()) from exc

    async def list_tools(self, *, params: Any | None = None) -> Any:
        """Return the SDK's ``ListToolsResult`` unchanged. ``params`` may hold a cursor."""
        try:
            return await self._require_client().list_tools(params=params)
        except MCPError as exc:
            await self._raise_dead_child(exc)
            raise

    async def collect_tools_pages(
        self,
    ) -> tuple[list[dict[str, Any]], bool, str | None]:
        """Follow ``nextCursor`` up to MAX_TOOLS_PAGES; return pages, cap flag, error."""
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        for _ in range(MAX_TOOLS_PAGES):
            before = len(self.raw_tools_pages)
            self._tap.reset_tools_list_error()
            try:
                with anyio.fail_after(self.spec.call_timeout):
                    if cursor is None:
                        await self.list_tools()
                    else:
                        await self.list_tools(
                            params=PaginatedRequestParams(cursor=cursor)
                        )
            except BaseException as exc:
                cancelled = anyio.get_cancelled_exc_class()
                if _exception_has_type(exc, cancelled):
                    raise
                if _exception_has_type(exc, TimeoutError) or _exception_has_type(
                    exc, MCPError
                ):
                    return pages, False, _error_text(exc)
                captured = self.raw_tools_pages[before:]
                if not captured:
                    return pages, False, _error_text(exc)
            else:
                captured = self.raw_tools_pages[before:]
                if not captured:
                    return pages, False, "tools/list returned no raw result"
            if self.tools_list_error is not None:
                return pages, False, self.tools_list_error
            page = captured[-1]
            tools = page.get("tools")
            if not isinstance(tools, list) or any(
                not isinstance(item, dict) for item in tools
            ):
                return pages, False, "tools/list returned a non-object tool"
            pages.append(page)
            next_cursor = page.get("nextCursor")
            if not next_cursor:
                return pages, False, None
            cursor = str(next_cursor)
        return pages, True, None

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None, timeout: float | None = None
    ) -> Any:
        """Return the SDK's own result object unchanged (a wrapper may come later).

        Error distinction for later checks: success is a ``CallToolResult`` with
        ``is_error`` False; a server that answered with a tool error returns a
        ``CallToolResult`` with ``is_error`` True (the wire ``isError`` flag); a
        JSON-RPC error response raises the SDK's ``MCPError``. None of those are
        converted into our own errors. ``CallTimeout`` means OUR timeout expired,
        and ``ServerExited`` / ``StartupTimeout`` mean the launcher failed. Therefore
        later checks can tell "server answered with an error" apart from "tool
        succeeded" and from "no answer at all".
        """
        client = self._require_client()
        effective = self.spec.call_timeout if timeout is None else timeout
        try:
            with anyio.fail_after(effective):
                return await client.call_tool(name, arguments)
        except TimeoutError as exc:
            raise CallTimeout(
                self._safe(f"tools/call {name!r} exceeded {effective} seconds")
            ) from exc
        except MCPError as exc:
            await self._raise_dead_child(exc)
            raise

    def _require_client(self) -> ClientSession:
        if self._client is None or self._cleaned:
            raise CaretakerError("session is not open")
        return self._client

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Cleanup runs on normal exit, on errors and on cancellation.
        await self._cleanup()

    async def _cleanup(self) -> None:
        if self._cleaned:
            return
        self._cleaned = True
        if self._stop_event is not None:
            self._stop_event.set()

        stop_error: BaseException | None = None
        # Shield the resource cleanup from an outer cancellation. This shield is
        # entered and exited INSIDE our task group's scope, so the task group's
        # cancel scope is still unwound last (LIFO), like the SDK's stdio client.
        with anyio.CancelScope(shield=True):
            for stream in (self._read_recv, self._write_send):
                if stream is not None:
                    with suppress(Exception):
                        await stream.aclose()

            if self._process is not None:
                try:
                    await self._stop_process_tree(self._process)
                except BaseException as exc:  # noqa: BLE001 - cleanup finishes, then re-raises
                    stop_error = exc
                self.exit_code = self._process.returncode
                for stream in (self._process.stdin, self._process.stdout):
                    if stream is not None:
                        with suppress(Exception):
                            await stream.aclose()

            for stream in (
                self._read_send,
                self._read_recv,
                self._write_send,
                self._write_recv,
            ):
                if stream is not None:
                    with suppress(Exception):
                        await stream.aclose()

            if self._errlog is not None:
                with suppress(Exception):
                    self._errlog.flush()
                    self._errlog.close()
                self._errlog = None

            # Cache stderr before a caller-owned folder is removed by run_checks.
            self._refresh_stderr()
            if self._owns_temp_area:
                await remove_temp_area(self._temp_area)

        if self._task_group is not None:
            # Fallback to guarantee the runner and bridge tasks stop even if a
            # server ignored stdin EOF. __aexit__ consumes this cancellation.
            self._task_group.cancel_scope.cancel()
            with suppress(Exception):
                await self._task_group.__aexit__(None, None, None)
            await anyio.lowlevel.cancel_shielded_checkpoint()
            self._task_group = None
        self._client = None
        if stop_error is not None:
            raise stop_error

    async def _stop_process_tree(self, process: Any) -> None:
        already_exited = process.returncode is not None
        self.exited_before_shutdown = already_exited
        self.exited_by_itself = None
        # Closing stdin gives a well-behaved server a chance to exit on its own.
        with suppress(Exception):
            await process.stdin.aclose()
        with anyio.move_on_after(self.spec.shutdown_grace):
            while process.returncode is None:
                await anyio.sleep(0.01)
        if not already_exited:
            self.exited_by_itself = process.returncode is not None

        if sys.platform == "win32":
            _, terminate, close = windows_helpers()
            await terminate(process)
            close(process)
            with anyio.move_on_after(3.0):
                while process.returncode is None:
                    await anyio.sleep(0.01)
            return

        # POSIX: the child is a session leader, so its pid is the process group.
        # Always signal the group, even if the parent already exited gracefully:
        # that is what kills grandchildren (the SDK helper does not do this).
        pgid = process.pid
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(pgid, signal.SIGTERM)
        with anyio.move_on_after(2.0):
            while _group_alive(pgid):
                await anyio.sleep(0.01)
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(pgid, signal.SIGKILL)
        with anyio.move_on_after(2.0):
            while process.returncode is None:
                await anyio.sleep(0.01)
