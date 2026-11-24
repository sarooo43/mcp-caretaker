# CT-ROB-004 - Large string input is handled

## What it checks

One `tools/call` probe sends a string of `1,048,576` characters to a tool whose raw `annotations.readOnlyHint` is exactly JSON `true`. The huge value is shown in evidence as a placeholder, never as the payload. The probe records `error_result`, `jsonrpc_error`, `success`, `no_answer`, or `exited`.

## Why it matters

A call with a large string can reveal a response timeout or a child exit that ordinary descriptions do not show.

## Verdict

- `pass`: the huge-input probe returned `error_result`, `jsonrpc_error`, or `success` within `call_timeout`.
- `warn`: the huge-input probe had `no_answer` within `call_timeout`.
- `fail`: the child `exited` during the huge-input probe.
- `not_tested`: no read-only tool with a suitable string property was available, a probe was skipped, the tool cap was reached, or the probe budget was exhausted. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Keep `tools/call` handling responsive within the caller's timeout, and avoid exiting the process while a large string is being handled.

## Limits

`readOnlyHint` is untrusted; a mislabelled writer receives valid and huge calls. Invalid-input probing not perfectly safe. Generated values placeholders. Replay constructed/not captured/needs initialize handshake first; the line is not byte-exact. Guesses `1 MiB, 50 tools, 120 s` in `thresholds.py`. At most 4 probes per tool by design. Nested properties not probed.
