# CT-DESC-003 — Tool names are unique

## What it checks
Duplicate raw tool names across all collected `tools/list` pages. Names are case-sensitive.

## Why it matters
The official tools page says names **SHOULD** be unique within a server. Duplicate names make a tool choice ambiguous for a client.

## Verdict
`fail`: one or more duplicate names were found. `pass`: all names are unique. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Give every tool one distinct name.

## Limits
Only names in the collected pages are compared. Uniqueness across different servers is out of scope; CT-DESC-009 checks the allowed characters.
