# CT-ROB-001 - Wrong-type input is rejected

## What it checks

For each tool, one `tools/call` probe sends a required property with a value whose type does not match the declared type. The probe records `error_result`, `jsonrpc_error`, `success`, `no_answer`, or `exited`. Tools without `readOnlyHint` exactly JSON `true` receive invalid input only.

## Why it matters

A successful result for input that does not match `inputSchema` gives callers an unclear contract and makes later argument handling harder to reason about.

## How it is decided

One wrong-type value is built from each eligible tool's schema and sent in a `tools/call`. A success is `warn` because bad input was accepted, no answer or a child exit is `fail`, and a proper rejection is `pass`. The summary counts tested and skipped probes.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_wrong_type.py
```

## Verdict

- `pass`: every planned wrong-type probe returned `error_result` or `jsonrpc_error`.
- `warn`: at least one planned wrong-type probe returned `success`.
- `fail`: at least one planned wrong-type probe had `no_answer` or `exited`.
- `not_tested`: no probe could run, a probe was skipped, the tool cap was reached, or the probe budget was exhausted. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Validate `tools/call` arguments against `inputSchema` before doing work. Return a tool result with `isError: true` or a JSON-RPC error when a declared type does not match.

## Limits

`readOnlyHint` is untrusted; a mislabelled writer receives valid and huge calls. Invalid-input probing not perfectly safe. Generated values placeholders. Replay constructed/not captured/needs initialize handshake first; the line is not byte-exact. Guesses `1 MiB, 50 tools, 120 s` in `thresholds.py`. At most 4 probes per tool by design. Nested properties not probed.
