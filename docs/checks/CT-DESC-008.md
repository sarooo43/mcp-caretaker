# CT-DESC-008 — No long horizontal whitespace runs

## What it checks
Runs of horizontal space, tab, or Unicode `Zs` characters in the same scanned fields as CT-DESC-007. A run of 40 or more is flagged; 40 is the limit; this number is a guess; it lives in thresholds.py. A run of exactly 40 is included.

## Why it matters
Long horizontal runs can push meaningful text out of a client's visible area. The trailing text is quoted in evidence so the position is inspectable.

## How it is decided

The same fields are scanned for runs of space, tab or Unicode `Zs` characters. A run of `WHITESPACE_RUN_LIMIT = 40` or more characters adds evidence with its length, its position and the 60 characters that follow; `warn` when at least one run is found, otherwise `pass`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_whitespace_run.py
```

## Verdict
`warn`: one or more runs met the limit. `pass`: every run was shorter. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Replace long horizontal runs with ordinary spacing or line breaks.

## Limits
Newline and carriage return are not counted. Nested properties are not scanned, and no rendered-width calculation is attempted.
