# CT-DESC-009 — Tool names match the spec name rule

## What it checks
Each raw tool name matches `^[A-Za-z0-9_.-]{1,128}$`. The official tools page says the 1 to 128 character length, the allowed ASCII characters, and uniqueness **SHOULD** apply; uniqueness is checked separately by CT-DESC-003.

## Why it matters
A predictable name shape is easier for clients to display and quote. The spec wording is SHOULD, so this check does not fail.

## How it is decided

Each tool name must match `^[A-Za-z0-9_.-]{1,128}$`. Every name that does not adds evidence; `warn` when at least one does, otherwise `pass`. The spec states this rule as SHOULD, so the verdict is `warn`, not `fail`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_tool_name_format.py
```

## Verdict
`warn`: one or more names do not match the rule. `pass`: every name matches. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Use 1 to 128 ASCII letters, digits, underscores, hyphens, or dots, with no spaces or commas.

## Limits
Names are case-sensitive. This is a character and length rule only; uniqueness is a separate check, and SHOULD is not treated as MUST.
