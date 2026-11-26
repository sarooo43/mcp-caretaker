# CT-ROB-005 - Valid read-only call succeeds

## What it checks

For each tool whose raw `annotations.readOnlyHint` is exactly JSON `true`, one `tools/call` probe sends generated valid input for its required properties. Every other tool receives invalid input only. If valid input cannot be generated, the probe is skipped and the result is `not_tested`.

## Why it matters

A call with generated valid input should return a successful tool result so callers can see the ordinary execution path.

## How it is decided

Valid input is generated from each read-only tool's schema. A child exit is `fail`; an error result, a JSON-RPC error or no answer is `warn`; a success is `pass`. When input cannot be generated the probe is skipped, and the check is `not_tested` when nothing else ran. A `warn` from an error result or a JSON-RPC error says the server rejected a generated placeholder value, and that can be correct: the schema may leave out a format rule the tool enforces, and the summary then says so in the same words.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_valid_call.py
```

## Verdict

- `pass`: every planned valid-input probe returned `success`.
- `warn`: a planned valid-input probe returned `error_result`, `jsonrpc_error`, or `no_answer`.
- `fail`: the child `exited` during a valid-input probe.
- `not_tested`: no read-only tool was available, valid input could not be generated, a probe was skipped, the tool cap was reached, or the probe budget was exhausted. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Accept the generated values that match `inputSchema`, and return a successful tool result for a valid `tools/call`.

## Limits

`readOnlyHint` is untrusted, so a mislabelled writer receives valid and huge calls. Every probe sends a real request, so a server may act on it. Generated values are shown as placeholders. No valid input is generated for a tool whose `inputSchema`, or any of its top-level properties, uses one of the refused keys listed in [the limits page](../limitations.md); its valid-call probe is then skipped, and the check is `not_tested` when no other valid call ran. A generated value meets the declared types only, never a format rule the schema does not state. Replay lines are constructed, not captured, and need the initialize handshake first; they are not byte-exact. The numbers `1 MiB, 50 tools, 120 s` are guesses that live in `thresholds.py`. At most 4 probes per tool by design. Nested properties are not probed.
