# 0003 - Checks foundation verification

Protocol revision identifiers such as `2025-11-25` and `2026-07-28` are version
strings defined by the specification, not calendar dates added to this document.
Evidence scripts and trimmed outputs live in `docs/decisions/0003-evidence/`.
Scripts are at most 60 lines each; outputs contain no personal paths.
Only this repository, the installed official `mcp` SDK package, PyPI metadata and
official MCP specification pages were read.

Precondition VERIFIED: `git rev-parse origin/main^{tree}` equals
`origin/arena/b946922e-mcp-caretaker^{tree}` (`116aa559dbdccba9b41bab256530b375fbc29d11`),
so `main` contains the merged PR 1 code. Work continues on the fixed branch
`arena/b946922e-mcp-caretaker`.

## a. Workspace

- VERIFIED (`/etc/os-release`, `uname`, `python3 --version`): Debian 12 (bookworm),
  Linux `6.1.158+` x86_64, CPython 3.11.2.
- VERIFIED (fresh venv): `mcp==2.3.0` was installed alone. This is exactly the
  pinned SDK. No dependency pin is changed in this PR.

## b. Windows cleanup helper

- VERIFIED (read installed SDK source `mcp/os/win32/utilities.py`, `mcp/client/stdio.py`,
  package `__init__.py` files, and `inspect` on the installed package): PR 1 uses
  `mcp.os.win32.utilities.create_windows_process` to create the Job Object, plus
  `terminate_windows_process_tree` and `close_process_job` during cleanup. The three
  names have no leading underscore and have docstrings.
- VERIFIED (same source): the module has no `__all__`; none of the three names is
  re-exported from `mcp`, `mcp.os`, or `mcp.os.win32`; `mcp.client.stdio` imports
  `create_windows_process` by the explicit module path. I classify the helper as
  **internal by packaging**. NOT VERIFIED: whether the SDK project documents this
  module as a public API. Decision: isolate the import in one small function with a
  clear error message if it is missing, and add
  `test_sdk_windows_helper_is_importable`. Do not redesign the launcher.

## c. mcp-types dependency

- VERIFIED (fresh venv with only `mcp==2.3.0`): the resolver installs
  `mcp-types==2.3.0`; `Requires-Dist` is `mcp-types==2.3.0`. The explicit pin in
  `pyproject.toml` is not needed to resolve that version, but PR 1 pinned it and
  this PR does not change pins. See `sdk_facts.out.txt`.

## d. Tool-name rules in the official spec

- VERIFIED (fetched `https://modelcontextprotocol.io/specification/2025-11-25/server/tools`,
  section `Tool Names`): the page says **SHOULD**, not MUST. Exact wording:
  "Tool names **SHOULD** be between 1 and 128 characters in length (inclusive)."
  "Tool names **SHOULD** be considered case-sensitive."
  "The following **SHOULD** be the only allowed characters: uppercase and lowercase
  ASCII letters (A-Z, a-z), digits (0-9), underscore (\\_), hyphen (-), and dot (.)"
  "Tool names **SHOULD NOT** contain spaces, commas, or other special characters."
  "Tool names **SHOULD** be unique within a server."
- Decision: CT-DESC-009 uses `^[A-Za-z0-9_.-]{1,128}$` and stays **WARN** because
  the spec wording is SHOULD. Length is 1 to 128 inclusive; allowed characters are
  ASCII letters, digits, underscore, hyphen and dot.

## e. Malformed tools through the SDK client

- VERIFIED (real subprocess: `raw_tools_server.py` + `stdio_client` +
  `ClientSession.list_tools`; output in `malformed_tools.out.txt`):
  1. A tool with no `description` returns data; `description` becomes `None`.
     Extra raw keys such as `unknownField` are dropped; model default fields with
     `None` are added.
  2. A tool with no `inputSchema` raises `ValidationError` for `ListToolsResult`
     (`tools.0.inputSchema Field required`); the whole answer is lost.
  3. A tool whose `inputSchema.type` is `"string"` raises `ValidationError`
     (`tools.0.inputSchema.type Input should be 'object'`); the whole answer is lost.
  4. Two tools with the same name return two tools; both names are preserved.
     Extra raw keys are dropped.
  5. A tool with a non-string `description` raises `ValidationError`
     (`tools.0.description Input should be a valid string`); the whole answer is lost.
- Decision: SDK objects do **not** keep everything the checks need. Raw-only keys,
  the omitted-versus-`None` distinction, and three whole malformed answers are lost.
  Therefore the runner uses a bridge tap for raw `tools/list` result dicts, not
  `model_dump(by_alias=True)`. This does not trigger the T0 e/g stop condition:
  the raw wire is available.

## f. Pagination

- VERIFIED (`inspect.signature` and real subprocess with two raw pages):
  `ClientSession.list_tools(*, params: PaginatedRequestParams | None = None)` accepts
  a cursor through `PaginatedRequestParams.cursor`; `ListToolsResult.next_cursor`
  has alias `nextCursor`. The experiment returned page 1 with `next_cursor='1'`
  and page 2 with `next_cursor=None`. See `initialize_pagination.out.txt`.

## g. Raw access and stdout noise

- VERIFIED (read PR 1 `session.py`): the bridge sees every child stdout line before
  the SDK parses it. Decision: tap `_stdin_writer` to record outgoing `tools/list`
  request ids, and tap `_stdout_reader` to keep only the matching raw `tools/list`
  `result` dicts for all pages, plus a count and first 5 non-protocol stdout lines,
  each cut at 200 characters. No whole stream is stored.
- VERIFIED (real subprocess `bridge_noise.py` with a plain text line before serving):
  PR 1 `_parse_line` returns a `ValueError` for that line; the SDK dispatcher logs
  it at debug level and returns when no stream-exception observer is set. Handshake
  and `tools/list` still succeeded. The SDK client/bridge therefore **ignores** the
  non-protocol line. The new tap will consume such lines so START-004 is
  **warn-capable**, not `not_tested`.

## h. Initialize result

- VERIFIED (`sdk_facts.py`, `initialize_pagination.py`, and real subprocesses):
  exact attribute names are `InitializeResult.protocol_version` (alias
  `protocolVersion`), `.server_info` (alias `serverInfo`), and
  `server_info.name` / `server_info.version` on `Implementation`. The negotiated
  version in the experiment was `2025-11-25`.
- VERIFIED (same evidence): `serverInfo` with empty strings gives
  `server_info.name == ""` and `server_info.version == ""`. A missing `name` or
  missing `version` makes `ClientSession.initialize` raise `ValidationError` from
  `Implementation`; no `InitializeResult` is produced.

## i. Shutdown

- VERIFIED (read PR 1 `ServerSession._stop_process_tree` source): session exit already
  closes the child's stdin, waits up to 1.0 second with `anyio.move_on_after(1.0)`,
  and then kills the whole tree. It does **not** kill immediately.
- Decision for T2: keep the close/wait/kill order, add the configurable
  `shutdown_grace`, and only add the recorded outcome `exited_by_itself`. Tree kill
  and temp removal remain on every path.
