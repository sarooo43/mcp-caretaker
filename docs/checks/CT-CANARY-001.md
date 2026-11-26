# CT-CANARY-001 - Canary values are absent from tool answers

## What it checks

Each `run_checks` call plants three fresh fake values named `CARETAKER_CANARY_API_KEY`, `CARETAKER_CANARY_TOKEN`, and `CARETAKER_CANARY_SECRET` through the existing stripped `extra_env` path. This check scans every `tools/call` answer when it is received, including PR 3 probes, unknown-tool answers, final valid calls, tool results with `isError`, and `MCPError` code, message, and data. The whole result JSON text, including `content`, `structuredContent`, and `isError`, is inspected. Only counts and findings are kept; all answers are not retained.

## Why it matters

A finding is a fact about where planted text appeared. Findings are not verdicts of intent. A deliberate show-environment tool is flagged, and v0.1 has no suppress. Exact values and their standard base64 forms are never written to results, evidence, messages, logs, or files.

## How it is decided

`FAIL` is used for any finding, and it wins over every reason: an answer that was scanned and contains a planted value fails this check even while the robustness stage is incomplete. `PASS` requires at least one scanned answer with no finding. `not_tested` is used for zero answers, an earlier-stage `tools/list` failure, or robustness checks that did not complete. When the robustness stage did not complete, the reason names how many of the six robustness checks failed, how many were `not_tested`, and how many `tools/call` answers were scanned, as in `robustness checks: 0 failed, 2 not tested; 6 tools/call answers were scanned`. `not_tested` is never counted or displayed as pass. Every finding has `subject` set to where it was found, `detail` with the variable name, `exact` or `base64` encoding, and a redacted excerpt, and a constructed `tools/call` replay line.

## How to reproduce

Set an env variable named `CARETAKER_CANARY_TOKEN` to any value.

Start one fixture server with one shell command per line.

```sh
python examples/servers/bad_canary_leaks.py result_text
```

Send this constructed replay line after an initialize handshake.

```text
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"echo","arguments":{"value":"A"}}}
```

## Verdict

`FAIL` means at least one planted value or its standard base64 form was found in a tool answer. `PASS` means answers were scanned and no finding was recorded. `not_tested` means the earlier stage did not provide comparable answers. `not_tested` is never counted or displayed as pass.

## How to fix

Do not place environment text or its standard base64 form in tool content, structured content, tool errors, or JSON-RPC error fields. Keep error data short and free of planted names. A deliberate show-environment tool remains flagged because v0.1 has no suppress.

## Limits

- Only three names are planted; other environment names are not checked.
- Only the value encoded on its own with standard base64 is detected; no other encoding is generated.
- Changes by time, by more calls, or by specific arguments are not caught; only observed answers are compared.
- Stderr and stray stdout are covered by CT-CANARY-003 with a stderr cap; this page covers tool answers.
- A robustness check that is `not_tested` only because probes were skipped still makes this check `not_tested`, even when answers were scanned.
- A finding still fails this check in that situation, because findings are checked before any reason.
- Startup failure leaves this check `not_tested`. `not_tested` is never counted or displayed as pass.
