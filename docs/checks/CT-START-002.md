# CT-START-002 — Handshake reports server name and version

## What it checks
The negotiated `protocolVersion`, `serverInfo.name`, and `serverInfo.version` from the SDK initialize result. `RunResult.protocol_version` carries the negotiated version; this check also puts it in evidence with the subject `protocolVersion`.

## Why it matters
Callers need the negotiated version and basic server identity in the result. Empty identity fields are useful to surface without treating the session as unusable.

## How it is decided

Reads `protocolVersion`, `serverInfo.name` and `serverInfo.version` from the raw initialize result. It counts how many of the two `serverInfo` fields are empty: `warn` when at least one is empty, with that count in the summary, and `pass` when both are present. All three values are quoted as evidence.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_empty_handshake.py
```

## Verdict
`pass`: both name and version are present. `warn`: one or both are empty. `not_tested`: with a reason when the handshake or runner did not provide the fields. `not_tested` is never counted or displayed as pass.

## How to fix
Return non-empty `serverInfo.name` and `serverInfo.version` in `initialize`.

## Limits
Only empty versus non-empty is checked; no version comparison, no semantic version parsing, and no schema of the name is imposed.
