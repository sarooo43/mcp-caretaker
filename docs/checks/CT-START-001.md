# CT-START-001 — Server starts and completes handshake

## What it checks
The child starts and the current SDK handshake completes within the caller's `startup_timeout`. `confirmed=True` is required; `ConfirmationRequired` propagates before any process is spawned. `argv` is not placed into the result.

## Why it matters
Without a completed handshake, later checks have no negotiated session and cannot be tested. A startup failure therefore leaves one factual result for this ID and a reasoned `not_tested` result for every other ID.

## How it is decided

The session is started with the configured `startup_timeout` and the handshake is awaited. `pass` when it completes, `fail` when the child exits or the handshake does not complete in time, and `not_tested` only when confirmation was refused in-process before a launch was attempted.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust --startup-timeout 2 -- <python> <repo>/examples/servers/bad_hangs_on_startup.py
```

The option keeps the run short, because this fixture never answers `initialize`.

## Verdict
`pass`: the handshake completed. `fail`: the server exited before handshake, timed out, or raised another startup error. `not_tested`: the runner could not record the outcome; a reason is always present. `not_tested` is never counted or displayed as pass.

## How to fix
Start a stdio MCP server that answers `initialize` with fields accepted by the installed SDK. Use an absolute script path in `argv`.

## Limits
The handshake is the installed SDK's own; this check adds no extra handshake round, no retry, and no judgement of intent. Text the server wrote to stderr is quoted as evidence only.
