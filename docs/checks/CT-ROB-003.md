# CT-ROB-003 - Unknown tool name is rejected

## What it checks

One `tools/call` probe uses a name that does not appear in `tools/list`. The probe records `error_result`, `jsonrpc_error`, `success`, `no_answer`, or `exited`. This probe is sent exactly once even when the server has zero tools.

## Why it matters

A successful result for an unknown name gives callers an unclear contract about which operations a server accepts.

## Verdict

- `pass`: the unknown-tool probe returned `error_result` or `jsonrpc_error`.
- `warn`: the unknown-tool probe returned `success`.
- `fail`: the unknown-tool probe had `no_answer` or `exited`.
- `not_tested`: the probe could not run or was skipped. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Look up the requested name in the tool registry. Return a tool result with `isError: true` or the protocol error described by the official tools page when the name is unknown.

## Limits

`readOnlyHint` is untrusted; a mislabelled writer receives valid and huge calls. Invalid-input probing not perfectly safe. Generated values placeholders. Replay constructed/not captured/needs initialize handshake first; the line is not byte-exact. Guesses `1 MiB, 50 tools, 120 s` in `thresholds.py`. At most 4 probes per tool by design. Nested properties not probed.
