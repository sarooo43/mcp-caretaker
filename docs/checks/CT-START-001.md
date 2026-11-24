# CT-START-001 — Server starts and completes handshake

## What it checks
The child starts and the current SDK handshake completes within the caller's `startup_timeout`. `confirmed=True` is required; `ConfirmationRequired` propagates before any process is spawned. `argv` is not placed into the result.

## Why it matters
Without a completed handshake, later checks have no negotiated session and cannot be tested. A startup failure therefore leaves one factual result for this ID and a reasoned `not_tested` result for every other ID.

## Verdict
`pass`: the handshake completed. `fail`: the server exited before handshake, timed out, or raised another startup error. `not_tested`: the runner could not record the outcome; a reason is always present. `not_tested` is never counted or displayed as pass.

## How to fix
Start a stdio MCP server that answers `initialize` with fields accepted by the installed SDK. Use an absolute script path in `argv`.

## Limits
This does not add modern-handshake work, does not retry, and does not judge server intent. stderr is quoted evidence only.
