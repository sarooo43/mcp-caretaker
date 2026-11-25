# CT-ROB-003 - Unknown tool name is rejected

## What it checks

One `tools/call` probe uses a name that does not appear in `tools/list`. The probe records `error_result`, `jsonrpc_error`, `success`, `no_answer`, or `exited`. This probe is sent exactly once even when the server has zero tools.

## Why it matters

A successful result for an unknown name gives callers an unclear contract about which operations a server accepts.

## How it is decided

One call is sent with the fixed unknown name `caretaker_no_such_tool`. A success is `warn`, no answer or a child exit is `fail`, and a JSON-RPC error is `pass`. The summary counts tested and skipped probes.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_unknown_tool.py
```

## Verdict

- `pass`: the unknown-tool probe returned `error_result` or `jsonrpc_error`.
- `warn`: the unknown-tool probe returned `success`.
- `fail`: the unknown-tool probe had `no_answer` or `exited`.
- `not_tested`: the probe could not run or was skipped. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Look up the requested name in the tool registry. Return a tool result with `isError: true` or the protocol error described by the official tools page when the name is unknown.

## Limits

`readOnlyHint` is untrusted, so a mislabelled writer receives valid and huge calls. Every probe sends a real request, so a server may act on it. Generated values are shown as placeholders. Replay lines are constructed, not captured, and need the initialize handshake first; they are not byte-exact. The numbers `1 MiB, 50 tools, 120 s` are guesses that live in `thresholds.py`. At most 4 probes per tool by design. Nested properties are not probed.
