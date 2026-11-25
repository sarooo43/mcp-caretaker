# CT-DESC-006 — Every top-level property has a description

## What it checks
Each top-level `inputSchema.properties` entry has a non-empty string `description`. Problems are aggregated into one result.

## Why it matters
Argument descriptions help a client supply the right value. Tool-level descriptions alone do not explain individual arguments.

## How it is decided

Every top-level property in `inputSchema.properties` must have a non-empty string `description`. Each one without it adds evidence; `warn` when at least one does, otherwise `pass`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_missing_property_descriptions.py
```

## Verdict
`warn`: one or more top-level properties have no usable description. `pass`: every top-level property has one. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Add a plain string description to each top-level property.

## Limits
Only top-level properties are inspected. Description length is checked by CT-DESC-002 for tools, not for properties.
