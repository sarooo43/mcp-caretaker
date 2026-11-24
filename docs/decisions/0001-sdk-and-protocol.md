# 0001 - SDK and protocol verification

Workspace: Debian 12 (bookworm), Linux 6.1, CPython 3.11.2. All experiments below
were run in a throwaway virtual environment against the official `mcp` package from
PyPI. Scripts and trimmed outputs live in `docs/decisions/0001-evidence/`.

Protocol revision identifiers such as `2026-07-28` are version strings defined by the
specification, not calendar dates added to this document.

Facts are labelled VERIFIED (with how) or NOT VERIFIED. Nothing here comes from a
competitor's README; the claim in that README was checked independently.

## a. Releases, Python versions, protocol versions

- VERIFIED (PyPI JSON API `https://pypi.org/pypi/mcp/json`, read with `urllib`): the
  newest stable, non-pre-release release is **2.3.0**. A 2.x line exists
  (2.0.0, 2.0.1, 2.1.0, 2.1.1, 2.2.0, 2.3.0). Pre-releases also exist
  (2.0.0a2, 2.0.0a3, 2.0.0b1, 2.0.0b2, 2.0.0rc1) and are not adopted.
- VERIFIED (same PyPI metadata): `Requires-Python: >=3.10`; classifiers list 3.10,
  3.11, 3.12, 3.13 and 3.14. Our project still requires Python 3.11+ as decided.
- VERIFIED (read installed `mcp_types/version.py`): known revisions are
  2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, 2026-07-28; handshake revisions
  are the first four; modern (per-request envelope) revision is 2026-07-28.
  `ClientSession.initialize()` offers the newest handshake revision (2025-11-25).
- VERIFIED (official spec pages fetched: `/specification/2026-07-28/basic/versioning`
  and `/specification/2026-07-28/schema`, plus the installed SDK): revision
  2026-07-28 is real, and `server/discover` is real. The versioning page says
  "Servers MUST implement `server/discover`" and the SDK contains a working probe
  (`mcp/client/_probe.py`, `ClientSession.discover`). So the Cisco README claim about
  a newer `mcp 2.0` line and that protocol revision is accurate, but we did not rely
  on that README: it is confirmed by PyPI, the installed package and the official
  spec pages. VERIFIED; not taken on trust.

## b. Client API for stdio

- VERIFIED (`inspect.signature` on the installed package; full output in evidence):
  `stdio_client(server: mcp.client.stdio.StdioServerParameters, errlog: TextIO = sys.stderr)`
  is an async context manager yielding `(ReadStream[SessionMessage | Exception],
  WriteStream[SessionMessage])`.
  `StdioServerParameters(*, command: str, args: list[str] = [], env: dict[str, str] | None = None,
  cwd: str | pathlib.Path | None = None, encoding: str = 'utf-8',
  encoding_error_handler: Literal['strict','ignore','replace'] = 'strict')`.
  `ClientSession(read_stream=None, write_stream=None, read_timeout_seconds=None, ...)`
  accepts streams directly. `initialize() -> InitializeResult`,
  `list_tools(*, params=None) -> ListToolsResult`,
  `call_tool(name, arguments=None, read_timeout_seconds=None, ...) -> CallToolResult | ...`.
- VERIFIED (experiment): `ClientSession` works with streams we create ourselves.

## c. What environment the child receives

- VERIFIED (read installed `mcp/client/stdio.py`): the helper always computes
  `get_default_environment() | (server.env or {})`. When `env` is given it is merged
  OVER the SDK's default safe environment; when `env` is not given the child still
  receives that default environment. The SDK does NOT offer an empty starting
  environment. On POSIX the default allow-list is HOME, LOGNAME, PATH, SHELL, USER;
  on Windows it is APPDATA, HOMEDRIVE, HOMEPATH, LOCALAPPDATA, PATH, PATHEXT,
  PROCESSOR_ARCHITECTURE, SYSTEMDRIVE, SYSTEMROOT, TEMP, USERNAME, USERPROFILE.
- VERIFIED (experiment, real child, NAMES only printed): with `env=None` the child saw
  `['CARETAKER_PIDFILE', 'HOME', 'LC_CTYPE', 'LOGNAME', 'PATH', 'SHELL', 'USER']`;
  with `env={'T0_FAKE_SECRET': ..., 'T0_EXTRA': 'x'}` it saw those two names plus all
  the default names. `LC_CTYPE` is added by CPython itself at startup, not by the SDK.

## d. cwd and stderr

- VERIFIED (signature + experiment): `cwd` is a supported parameter; our child ran in
  the temporary folder we chose.
- VERIFIED (read installed `mcp/client/stdio.py` + experiment): `stdio_client` accepts
  `errlog: TextIO`; passing an open file object redirects the child's stderr to that
  file. Our experiment read the file back and the tool's stderr lines were there.

## e. Ending the child, and grandchildren

- VERIFIED (read installed `mcp/client/stdio.py` and `mcp/os/posix/utilities.py`,
  `mcp/os/win32/utilities.py`): shutdown closes stdin, waits up to 2 s for the server
  to exit on its own, and only then kills the tree. POSIX: SIGTERM to the process
  group (the child is spawned with `start_new_session=True`), SIGKILL after a grace
  period. Windows: a Job Object with `KILL_ON_JOB_CLOSE`, terminated with
  `TerminateJobObject`. The SDK's own POSIX utility docstring states that a graceful
  server's children are left alive.
- VERIFIED (experiment on Linux, real grandchild process `sleep 600`): after the
  `stdio_client` + `ClientSession` context managers exited normally, the grandchild
  was **still alive**. Reason: the parent exited on its own after stdin closed, so the
  tree-kill branch was never entered. The SDK stdio helper therefore does not give us
  a reliable process-tree kill on POSIX.
- NOT VERIFIED locally: the same experiment on Windows. We do not have Windows here;
  CI on `windows-latest` is the evidence for that platform.

## f. Wrong-typed arguments and unknown tool names

- VERIFIED (experiment against the tiny SDK server): `ClientSession.call_tool` does
  **not** refuse client-side. `add(a="WRONG_TYPE", b=2)` and `no_such_tool` were both
  sent to the server, which answered with `CallToolResult.is_error == True`. The SDK
  client therefore lets later robustness checks send hostile inputs and read the
  server's answer. JSON-RPC error responses surface as the SDK's `MCPError` from
  `send_request` (read in `mcp/client/session.py`).

## g. Server-side API for our fixtures

- VERIFIED (`inspect.signature` + experiment): in this 2.x SDK the server class is
  `from mcp.server.mcpserver import MCPServer`; the old `mcp.server.fastmcp` import
  deliberately raises a migration error. Tools are declared with
  `@server.tool(description=..., annotations=ToolAnnotations(read_only_hint=True))`
  and the stdio server is started with `server.run(transport="stdio")`.
  `ToolAnnotations.read_only_hint` serialises as the wire name `readOnlyHint`. The
  experiment's `tools/list` returned `read_only_hint=True` for `echo`/`add` and `None`
  for tools declared without annotations.

## h. Meaning of readOnlyHint

- VERIFIED (official spec page `/specification/2026-07-28/schema`, the current
  revision, section `ToolAnnotations`; also stated on the older
  `/specification/2025-06-18/schema` page): `readOnlyHint` is an optional boolean,
  default `false`. "If true, the tool does not modify its environment." All
  `ToolAnnotations` properties are **hints**, not guarantees of behaviour; the
  tools page adds that clients MUST treat tool annotations as untrusted unless they
  come from trusted servers. So this PR only records the hint, it does not enforce it.

## Decision

- Pin **`mcp==2.3.0`** as the runtime dependency. It is the newest stable release on
  PyPI (2.x exists, no pre-release suffix, not yanked), and experiments b to g passed
  on this OS with it. The 1.x line is not needed.
- Use the **fallback launcher**: our launcher spawns the server itself with
  `anyio.open_process` (asyncio subprocess, argv tuple, `start_new_session=True` on
  POSIX; the SDK's Windows Job Object spawn helper is reused on Windows), writes
  stderr to our own file, and bridges the child's stdin/stdout into
  `mcp.ClientSession(read_stream, write_stream)` with the SDK's own `SessionMessage`
  and `mcp_types.jsonrpc_message_adapter`. This is required because the SDK's
  `stdio_client` always merges its default environment (c) and leaves POSIX
  grandchildren alive (e). The fallback is possible because `ClientSession` accepts
  streams directly (b) and was proven by the `fallback_experiment.py` evidence:
  handshake succeeded, the child saw ONLY our stripped environment, and the
  grandchild died after our process-group kill.
- CI (`ubuntu-latest` and `windows-latest`, Python 3.11 and 3.13) is the evidence for
  Windows env stripping and Windows tree kill; those two facts are NOT VERIFIED
  locally.
