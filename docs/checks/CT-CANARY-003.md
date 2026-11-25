# CT-CANARY-003 - Canary values are absent from stderr and stray stdout

## What it checks

This check scans stderr from the start of each session up to `STDERR_SCAN_MAX_BYTES` per session and every full stray stdout line before the bounded display truncates it. Both sessions are scanned: the first session and the second session a rug-pull check starts. The runner prefers stderr read after a session closes when the run-owned folder keeps the file readable, so shutdown output is included. If that is not readable, it uses the raw prefix captured before shutdown. If neither raw read is available, it uses the cached redacted tail and notes that exact-value detection can be incomplete.

## Why it matters

Diagnostics and non-protocol stdout can carry planted text even when tool answers are clean. A deliberate show-environment tool is flagged, and v0.1 has no suppress. Exact values and their standard base64 forms are never written to results, evidence, messages, logs, or files.

## How it is decided

`WARN` is used for any finding. `PASS` is used otherwise, with the exact summed stderr byte count, the number of sessions whose stderr was actually scanned, and the exact stdout line count in the summary: `{N} stderr bytes scanned across {S} session(s) and {M} stdout lines scanned; no findings.` The cap is per session, so the byte count is unclamped, and when a scan reached the cap the summary adds ` Stderr cap of {C} bytes per session reached.` Startup failure leaves this check `not_tested`. `not_tested` is never counted or displayed as pass. Each finding has `subject` set to `stderr` or `stdout`, `detail` with the variable name, `exact` or `base64` encoding, and a redacted excerpt, and `replay` set to `null`.

## How to reproduce

Set an env variable named `CARETAKER_CANARY_TOKEN` to any value.

Start one fixture server with one shell command per line.

```sh
python examples/servers/bad_canary_leaks.py stderr
```

Send this constructed replay line after an initialize handshake.

```text
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"echo","arguments":{"value":"A"}}}
```

## Verdict

`WARN` means at least one planted value or its standard base64 form was found in scanned stderr or stray stdout. `PASS` means no finding was recorded and states the bytes and lines scanned. `not_tested` is only used for startup failure. `not_tested` is never counted or displayed as pass.

## How to fix

Keep planted text out of startup logs, diagnostics, shutdown output, and non-protocol stdout. A deliberate show-environment diagnostic remains flagged because v0.1 has no suppress. Remove the source of the text rather than suppressing the check.

## Limits

- Only three names are planted; other environment names are not checked.
- Only the value encoded on its own with standard base64 is detected; no other encoding is generated.
- Changes by time, by more calls, or by specific arguments are not caught; only observed output is scanned.
- Stderr is capped at `STDERR_SCAN_MAX_BYTES = 1048576` per session; this number is a guess; it lives in thresholds.py. A larger stderr with no finding in the scanned prefix passes, the summary states the bytes scanned and the number of sessions scanned, and it states that the cap was reached.
- The fallback to a cached redacted tail can miss exact values, although standard base64 text can still be found.
