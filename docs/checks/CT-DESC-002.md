# CT-DESC-002 — Description length is within limits

## What it checks
The stripped tool-level description length. The minimum is 10 characters; this number is a guess; it lives in thresholds.py. The maximum is 1000 characters; this number is a guess; it lives in thresholds.py. Both ends are inclusive.

## Why it matters
Very short or very long descriptions can be unhelpful to a client. The boundaries are deliberately modest and easy to change in one file.

## How it is decided

The stripped length of every non-empty description is compared with `DESC_MIN_LENGTH = 10` and `DESC_MAX_LENGTH = 1000`. Each length outside the range adds evidence with the length; `warn` when at least one does, otherwise `pass`. Empty descriptions are left to CT-DESC-001.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_description_length.py
```

## Verdict
`pass`: all descriptions are within both limits. `warn`: one or more descriptions are outside the limits. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Write a concise description between the two limits.

## Limits
Length is measured in Unicode code points after `strip()`, not display width or rendered size. Property descriptions are not measured here.
