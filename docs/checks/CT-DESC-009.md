# CT-DESC-009 — Tool names match the spec name rule

## What it checks
Each raw tool name matches `^[A-Za-z0-9_.-]{1,128}$`. The official tools page says the 1 to 128 character length, the allowed ASCII characters, and uniqueness **SHOULD** apply; uniqueness is checked separately by CT-DESC-003.

## Why it matters
A predictable name shape is easier for clients to display and quote. The spec wording is SHOULD, so this check does not fail.

## Verdict
`warn`: one or more names do not match the rule. `pass`: every name matches. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Use 1 to 128 ASCII letters, digits, underscores, hyphens, or dots, with no spaces or commas.

## Limits
Names are case-sensitive. This is a character and length rule only; uniqueness is a separate check, and SHOULD is not treated as MUST.
