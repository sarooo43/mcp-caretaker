# CT-DESC-003 — Tool names are unique

## What it checks
Duplicate raw tool names across all collected `tools/list` pages. Names are case-sensitive.

## Why it matters
The official tools page says names **SHOULD** be unique within a server. Duplicate names make a tool choice ambiguous for a client.

## How it is decided

Tool names are counted with `collections.Counter`. Every name seen more than once is reported with its count; `fail` when at least one duplicate exists, otherwise `pass`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_duplicate_names.py
```

## Verdict
`fail`: one or more duplicate names were found. `pass`: all names are unique. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Give every tool one distinct name.

## Limits
Only names in the collected pages are compared. Uniqueness across different servers is out of scope; CT-DESC-009 checks the allowed characters.
