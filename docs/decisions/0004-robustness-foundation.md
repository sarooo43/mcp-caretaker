# 0004 - Robustness foundation verification

Evidence scripts and trimmed outputs live in `docs/decisions/0004-evidence/`. Each
script and output is at most 60 lines. Outputs contain no personal paths. Only this
repository, the installed official `mcp` SDK package, its API signatures/docstrings,
and official MCP specification pages were read. No SDK or specification claim below
is from memory; unverified items are labelled `NOT VERIFIED`. This decision file was
written before any product code for the new check group.

## a. Workspace, merged PR 2 and exact SDK pin

- VERIFIED (`workspace_main.py` / `workspace_main.out.txt`): Debian GNU/Linux 12
  (bookworm), Linux `6.1.158+`, CPython 3.11.2, branch
  `arena/b946922e-mcp-caretaker`.
- VERIFIED (`git rev-parse`, `gh pr view 2`): PR 2 is `MERGED`; merge commit
  `f2a605e14de28ccc1b5bf4ee3e076b23f63b87c6` is `origin/main`. The main tree
  `5049132b2d5b83d4cd47afff98e12620157e961b` equals the PR 2 head tree, and the
  PR 2 head is an ancestor of main. PR 2 files such as `runner.py`,
  `checks/description.py` and `docs/checks/CT-DESC-001.md` are present on main.
- VERIFIED (fresh venv, `sdk_pinned.py` / `sdk_pinned.out.txt`): `mcp==2.3.0`
  installs exactly `mcp-types==2.3.0`; its distribution metadata requires
  `mcp-types==2.3.0`. No runtime dependency or pin was changed.

## b. After CallTimeout and a late answer

- VERIFIED (`timeout_and_exit.py` / `timeout_and_exit.out.txt`, real subprocess
  using `examples/servers/probe_server.py`): a short `tools/call` timeout raised
  `CallTimeout` after 0.2 seconds; the following `tools/list` returned 4 tools;
  after waiting past the slow answer, a second `tools/list` also returned 4 tools.
- VERIFIED (`sdk_dispatcher.py` / `sdk_dispatcher.out.txt`, installed SDK source):
  the dispatcher removes the pending waiter on every path and debug-logs an
  unknown or late request id. The late answer is dropped, not applied to a later
  request. `NOT VERIFIED`: the exact wire bytes of that late answer were not
  captured; that is not needed for the session-usability fact above.
- Decision: a timed-out probe is classified `no_answer`; the runner continues only
  after a liveness `tools/list`.

## c. Child exit during a call and after the child is dead

- VERIFIED (`timeout_and_exit.py`, `raw_probe_server.py`): when the child called
  `os._exit(7)` on `tools/call`, the PR 2 bridge raised
  `MCPError: Connection closed` in 0.0 seconds, not `CallTimeout`; a following
  `tools/list` raised the same promptly. The child's return code was 7 before
  shutdown. PR 2 did not raise `ServerExited` for this post-handshake exit.
- Decision: T2 must convert a closed connection with a dead child into
  `ServerExited` promptly, for both `call_tool` and `list_tools`.

## d. One MiB string and wrong values against the SDK server

- VERIFIED (`sdk_probe_behaviour.py` / `.out.txt`, `sdk_probe_server.py`): a
  `1,048,576`-character string sent through `ServerSession.call_tool` to an SDK
  `echo` tool round-tripped as exactly `1,048,576` characters in 0.08 seconds.
  The T0 d stop condition is not triggered: the bridge can deliver the string.
- VERIFIED (same output): object-for-string, `"not-a-number"` for integer and
  number, `"not-a-bool"` for boolean, and two extra wrong values for array and
  object tools all produced `CallToolResult.is_error=True`. None was coerced to a
  successful result. No wrong value needs changing.
- `NOT VERIFIED`: behaviour of SDK versions other than the exact pin; no other
  version is used.

## e. Raw wire shape for ToolAnnotations(read_only_hint=True)

- VERIFIED (raw bridge-tap page, `sdk_probe_behaviour.out.txt`): the SDK server's
  tool dict has `annotations` containing exactly `{"readOnlyHint": true}`. The
  exact key path is `tool["annotations"]["readOnlyHint"]`, and it is Python
  `True` after JSON parsing. The `inputSchema` is an object schema with keys
  `properties`, `required`, `title` and `type`; the `text` property has `type`
  `string` and a `title`.
- Decision: the new pure detector reads the raw `annotations.readOnlyHint` key and
  requires exactly JSON `true`; any other value or missing key is treated as a
  writer for probe planning.

## f. Unknown tool name and protocol/tool error rules

- VERIFIED (`sdk_probe_behaviour.out.txt`, real SDK server): calling
  `caretaker_no_such_tool` returned a `CallToolResult` with `is_error=True` and
  text `Unknown tool: caretaker_no_such_tool`.
- VERIFIED (`raw_probe_server.py`, same output): a raw JSON-RPC error with code
  `-32602` and message `Unknown tool: caretaker_no_such_tool` raised
  `MCPError`; its `error.code` is `-32602` and `error.message` is that string.
- VERIFIED (`fetch_page` of
  `https://modelcontextprotocol.io/specification/latest/server/tools`,
  `official_tools_page.out.txt`): the official Tools page says Protocol Errors
  include unknown tools and are returned as standard JSON-RPC errors; Tool
  Execution Errors such as input validation are reported in tool results with
  `isError: true`. The page also says clients MUST consider tool annotations
  untrusted unless they come from trusted servers.
- Decision: the new checks treat both `isError` tool results and JSON-RPC errors
  as error answers, never as successful tool execution.

## g. exited_by_itself when the child is already dead

- VERIFIED (`timeout_and_exit.out.txt`): PR 2 recorded
  `exited_by_itself=True` when the child had exited before session cleanup closed
  stdin. This is not `None`.
- Decision: T2 must keep `exited_by_itself=None` for a child that had already
  exited, must still kill the process tree and remove the temp folder, and must
  make CT-START-005 `not_tested` with reason
  `server had already exited before shutdown`.

## T2 requirement and stop conditions

- T0 a: VERIFIED, main contains PR 2 code.
- T0 b: VERIFIED, session is usable after `CallTimeout`; the late answer is dropped.
- T0 c: VERIFIED, PR 2 raised `MCPError`, not `ServerExited`, promptly.
- T0 d: VERIFIED, one MiB can be delivered; no wrong value was coerced to success.
- T0 e: VERIFIED, raw key path and schema shape recorded.
- T0 f: VERIFIED, SDK result, raw exception attributes, and official error rules recorded.
- T0 g: VERIFIED, PR 2 recorded `True`; T2 is required.
- T2 is required because c and g found launcher/session behaviour to change. This
  is not the T2 "no change needed" branch. None of the three stop conditions
  applies.

## Decisions I made

- The PR 2 audit brief says 32 names but enumerates 33; all 33 are treated as required.
- The official Tools page was fetched through its `latest` URL; no calendar date is copied into docs.
- Probe planning uses raw `readOnlyHint` from the bounded bridge tap, not SDK model defaults.
- Unknown-tool `isError` results and raw JSON-RPC errors are both classified as error answers.
- SDK-version claims are limited to the exact pinned version; other versions are NOT VERIFIED.
- No new runtime dependency, network call, report file, CLI command or telemetry is added.
