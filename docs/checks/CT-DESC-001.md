# CT-DESC-001 — Every tool has a description

## What it checks
Each raw tool has a non-empty string `description`. Omitted and non-string values are aggregated into one `CheckResult` with one evidence item per problem.

## Why it matters
Tool text is what a client sees when choosing a tool. A missing description gives the client less information.

## Verdict
`pass`: zero tools lack a description. `warn`: one or more tools lack a usable description. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Add a plain string description to every tool.

## Limits
Only the tool-level description is checked; top-level property descriptions are checked by CT-DESC-006. No quality judgement is made.
