# CT-DESC-004 — Every tool has an object inputSchema

## What it checks
Each raw tool has an `inputSchema` dict whose top-level `type` is `object`.

## Why it matters
The official tools page says `inputSchema` MUST be a valid JSON Schema object. A string schema or missing schema loses the whole SDK answer, so the raw tap is used for this check.

## How it is decided

Every tool's `inputSchema` must be a JSON object whose `type` is exactly `object`. Each tool that fails this adds evidence; `fail` when at least one does, otherwise `pass`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_schema_not_object.py
```

## Verdict
`fail`: one or more tools have no object `inputSchema`. `pass`: every tool has one. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Return `"inputSchema": {"type": "object", "properties": {}}` or an equivalent object schema.

## Limits
This is only the top-level object check. Full JSON Schema validation is out of scope, and typed property keys are checked by CT-DESC-005.
