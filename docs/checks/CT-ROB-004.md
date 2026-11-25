# CT-ROB-004 - Large string input is handled

## What it checks

One `tools/call` probe sends a string of `1,048,576` characters to a tool whose raw `annotations.readOnlyHint` is exactly JSON `true`. The huge value is shown in evidence as a placeholder, never as the payload. The probe records `error_result`, `jsonrpc_error`, `success`, `no_answer`, or `exited`.

## Why it matters

A call with a large string can reveal a response timeout or a child exit that ordinary descriptions do not show.

## How it is decided

A single string of `HUGE_STRING_LENGTH = 1048576` characters is sent to each tool whose raw `readOnlyHint` is exactly `true`. A child exit is `fail`, no answer within `--call-timeout` is `warn`, and an answer is `pass`. When no read-only tool exists the check is `not_tested` with a reason.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust --call-timeout 2 -- <python> <repo>/examples/servers/bad_huge_input.py
```

## Verdict

- `pass`: the huge-input probe returned `error_result`, `jsonrpc_error`, or `success` within `call_timeout`.
- `warn`: the huge-input probe had `no_answer` within `call_timeout`.
- `fail`: the child `exited` during the huge-input probe.
- `not_tested`: no read-only tool with a suitable string property was available, a probe was skipped, the tool cap was reached, or the probe budget was exhausted. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Keep `tools/call` handling responsive within the caller's timeout, and avoid exiting the process while a large string is being handled.

## Limits

`readOnlyHint` is untrusted, so a mislabelled writer receives valid and huge calls. Every probe sends a real request, so a server may act on it. Generated values are shown as placeholders. Replay lines are constructed, not captured, and need the initialize handshake first; they are not byte-exact. The numbers `1 MiB, 50 tools, 120 s` are guesses that live in `thresholds.py`. At most 4 probes per tool by design. Nested properties are not probed.
