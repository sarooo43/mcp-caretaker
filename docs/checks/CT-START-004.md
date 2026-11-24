# CT-START-004 — No non-protocol text on stdout

## What it checks
The bridge sees child stdout before the SDK parses it. A bounded tap counts non-protocol lines and keeps a capped view of the first lines. Evidence is capped at 20 items; this number is a guess; it lives in thresholds.py. Each evidence string is capped at 300 characters; this number is a guess; it lives in thresholds.py. All exposed evidence is redacted with `extra_env`, non-printable characters are shown as `\uXXXX` escapes, and omitted items are shown as `N more not shown`.

## Why it matters
The SDK dispatcher debug-ignores a stream exception when no observer is set, so a plain text line would otherwise disappear. The tap makes this condition warn-capable.

## Verdict
`pass`: zero non-protocol stdout lines were seen. `warn`: one or more lines were seen. `not_tested`: with a reason after startup failure or a runner error. `not_tested` is never counted or displayed as pass.

## How to fix
Keep stdout protocol-only and write logs to stderr.

## Limits
Only stdout lines seen during this run are counted; the whole stream is not stored. stderr is not part of this check.
