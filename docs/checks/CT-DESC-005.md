# CT-DESC-005 — Every top-level property is typed

## What it checks
Each top-level `inputSchema.properties` entry has at least one typed equivalent: `type`, `$ref`, `anyOf`, `oneOf`, `allOf`, `enum`, or `const`. Problems are aggregated into one result.

## Why it matters
A client needs some declared shape for an argument. The spec allows more than a simple `type`, so equivalent schema keys are accepted.

## How it is decided

Every top-level property in `inputSchema.properties` must contain one of `type`, `$ref`, `anyOf`, `oneOf`, `allOf`, `enum` or `const`. Each untyped property adds evidence; `warn` when at least one does, otherwise `pass`. Nested properties are not checked.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_missing_types.py
```

## Verdict
`warn`: one or more top-level properties have no typed key. `pass`: every top-level property has one. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Add one of the typed keys to each top-level property.

## Limits
Only top-level properties are inspected. The value of a typed key is not validated, and nested properties are out of scope.
