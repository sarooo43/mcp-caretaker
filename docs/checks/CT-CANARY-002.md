# CT-CANARY-002 - Canary values are absent from handshake and tool listings

## What it checks

This check scans the raw first-connection `tools/list` pages and the raw `initialize` result's `serverInfo` name, version, and instructions plus top-level `instructions`. Raw wire text is used so SDK object conversion does not drop a field. Every first-connection page is scanned, including paginated pages. Findings are facts about where planted text appeared, not verdicts of intent.

## Why it matters

Handshake and listing text is server output that a client can display or store. A deliberate show-environment tool or metadata field is flagged, and v0.1 has no suppress. Exact values and their standard base64 forms are never written to results, evidence, messages, logs, or files.

## How it is decided

`FAIL` is used for any finding. `PASS` is used when handshake data and the first `tools/list` succeeded and no finding was recorded. `not_tested` is used when handshake data or `tools/list` failed. `not_tested` is never counted or displayed as pass. Each finding has `subject` set to the page or handshake field, `detail` with the variable name, `exact` or `base64` encoding, and a redacted excerpt, and a constructed `tools/list` replay line.

## How to reproduce

Set an env variable named `CARETAKER_CANARY_TOKEN` to any value.

Start one fixture server with one shell command per line.

```sh
python examples/servers/bad_canary_leaks.py server_name
```

Send this constructed replay line after an initialize handshake.

```text
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

## Verdict

`FAIL` means at least one planted value or its standard base64 form was found in the handshake or a first `tools/list` page. `PASS` means those locations were scanned with no finding. `not_tested` means the handshake or first listing was unavailable. `not_tested` is never counted or displayed as pass.

## How to fix

Keep planted text out of server names, versions, instructions, tool descriptions, titles, schemas, annotations, and other listing fields. A deliberate show-environment description remains flagged because v0.1 has no suppress.

## Limits

- Only three names are planted; other environment names are not checked.
- Only the value encoded on its own with standard base64 is detected; no other encoding is generated.
- Changes by time, by more calls, or by specific arguments are not caught; only the first connection is sampled.
- Stderr and stray stdout are covered by CT-CANARY-003 with a stderr cap; this page covers handshake and first listing text.
- Startup failure leaves this check `not_tested`. `not_tested` is never counted or displayed as pass.
