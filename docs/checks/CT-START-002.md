# CT-START-002 — Handshake reports server name and version

## What it checks
The negotiated `protocolVersion`, `serverInfo.name`, and `serverInfo.version` from the SDK initialize result. `RunResult.protocol_version` carries the negotiated version; this check also puts it in evidence with the subject `protocolVersion`.

## Why it matters
Callers need the negotiated version and basic server identity in the result. Empty identity fields are useful to surface without treating the session as unusable.

## Verdict
`pass`: both name and version are present. `warn`: one or both are empty. `not_tested`: with a reason when the handshake or runner did not provide the fields. `not_tested` is never counted or displayed as pass.

## How to fix
Return non-empty `serverInfo.name` and `serverInfo.version` in `initialize`.

## Limits
Only empty versus non-empty is checked; no version comparison, no semantic version parsing, and no schema of the name is imposed.
