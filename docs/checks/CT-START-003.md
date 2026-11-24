# CT-START-003 — tools/list works

## What it checks
`tools/list` answers captured as raw wire result dicts by the bounded bridge tap. `nextCursor` is followed for at most 10 pages; this number is a guess; it lives in thresholds.py. A JSON-RPC error or unusable raw answer fails this check. An empty tool list is valid for a server offering other features, so it warns with an explanation. A still-present cursor after the page cap also warns.

## Why it matters
Description/schema checks need the raw tool dicts. SDK objects can drop raw keys or reject a malformed page, while the tap retains a bounded copy for inspection.

## Verdict
`pass`: tools were returned, with no empty list and no page cap. `warn`: zero tools or the page cap was hit. `fail`: `tools/list` failed. `not_tested`: with a reason after startup failure or a runner error. `not_tested` is never counted or displayed as pass.

## How to fix
Answer `tools/list` with a valid result, return tools, and finish pagination before the cap.

## Limits
Only `tools/list` is exercised; `tools/call` is not. The whole stream is not stored, and pages beyond the cap are not read.
