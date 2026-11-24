# CT-DESC-008 — No long horizontal whitespace runs

## What it checks
Runs of horizontal space, tab, or Unicode `Zs` characters in the same scanned fields as CT-DESC-007. A run of 40 or more is flagged; 40 is the limit; this number is a guess; it lives in thresholds.py. A run of exactly 40 is included.

## Why it matters
Long horizontal runs can push meaningful text out of a client's visible area. The trailing text is quoted in evidence so the position is inspectable.

## Verdict
`warn`: one or more runs met the limit. `pass`: every run was shorter. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Replace long horizontal runs with ordinary spacing or line breaks.

## Limits
Newline and carriage return are not counted. Nested properties are not scanned, and no rendered-width calculation is attempted.
