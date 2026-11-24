# CT-ROB-005 - Valid read-only call succeeds

## What it checks

For each tool whose raw `annotations.readOnlyHint` is exactly JSON `true`, one `tools/call` probe sends generated valid input for its required properties. Every other tool receives invalid input only. If valid input cannot be generated, the probe is skipped and the result is `not_tested`.

## Why it matters

A call with generated valid input should return a successful tool result so callers can see the ordinary execution path.

## Verdict

- `pass`: every planned valid-input probe returned `success`.
- `warn`: a planned valid-input probe returned `error_result`, `jsonrpc_error`, or `no_answer`.
- `fail`: the child `exited` during a valid-input probe.
- `not_tested`: no read-only tool was available, valid input could not be generated, a probe was skipped, the tool cap was reached, or the probe budget was exhausted. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Accept the generated values that match `inputSchema`, and return a successful tool result for a valid `tools/call`.

## Limits

`readOnlyHint` is untrusted; a mislabelled writer receives valid and huge calls. Invalid-input probing not perfectly safe. Generated values placeholders. Replay constructed/not captured/needs initialize handshake first; the line is not byte-exact. Guesses `1 MiB, 50 tools, 120 s` in `thresholds.py`. At most 4 probes per tool by design. Nested properties not probed.
