# CT-DESC-005 — Every top-level property is typed

## What it checks
Each top-level `inputSchema.properties` entry has at least one typed equivalent: `type`, `$ref`, `anyOf`, `oneOf`, `allOf`, `enum`, or `const`. Problems are aggregated into one result.

## Why it matters
A client needs some declared shape for an argument. The spec allows more than a simple `type`, so equivalent schema keys are accepted.

## Verdict
`warn`: one or more top-level properties have no typed key. `pass`: every top-level property has one. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Add one of the typed keys to each top-level property.

## Limits
Only top-level properties are inspected. The value of a typed key is not validated, and nested properties are out of scope.
