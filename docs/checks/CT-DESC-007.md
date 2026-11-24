# CT-DESC-007 — No hidden characters in scanned text

## What it checks
Tool name, title, description and top-level input property name, title, description only. Hidden Unicode categories are `Cf`, `Cc` except `\n`, `\r`, `\t`, `Co`, and `Cs`. Variation selectors and combining marks are not flagged. Each hit is aggregated into one result with position and escaped code point.

## Why it matters
Non-visible characters can change how text is read without changing its apparent meaning. Showing the category and position makes the finding inspectable.

## Verdict
`warn`: one or more hidden characters were found. `pass`: none were found. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Remove non-visible format, control, private-use or surrogate characters from the scanned text. Keep ordinary combining marks if they are intended.

## Limits
No nested properties, output schema, or annotations are scanned. No intent judgement is made, and no text is executed or used as a path.
