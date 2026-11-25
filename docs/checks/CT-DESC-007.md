# CT-DESC-007 — No hidden characters in scanned text

## What it checks
Tool name, title, description and top-level input property name, title, description only. Hidden Unicode categories are `Cf`, `Cc` except `\n`, `\r`, `\t`, `Co`, and `Cs`. Variation selectors and combining marks are not flagged. Each hit is aggregated into one result with position and escaped code point.

## Why it matters
Non-visible characters can change how text is read without changing its apparent meaning. Showing the category and position makes the finding inspectable.

## How it is decided

The scanned fields are the tool `name`, `title` and `description` plus each top-level property's name, `title` and `description`. Characters in Unicode categories `Cf`, `Co` and `Cs`, and control characters other than line feed, carriage return and tab, each add one evidence item with the position and code point; `warn` when at least one is found, otherwise `pass`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_hidden_characters.py
```

## Verdict
`warn`: one or more hidden characters were found. `pass`: none were found. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Remove non-visible format, control, private-use or surrogate characters from the scanned text. Keep ordinary combining marks if they are intended.

## Limits
No nested properties, output schema, or annotations are scanned. No intent judgement is made, and no text is executed or used as a path.
