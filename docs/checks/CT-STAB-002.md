# CT-STAB-002 - Tool listing is stable after probes

## What it checks

This check compares the first raw `tools/list` result with the raw page captured from the CT-ROB-006 final liveness `tools/list`. It sends no new request. If that final page is unavailable or CT-ROB-006 did not pass, the check is `not_tested`. Common tools are matched by name, order is ignored, and top-level `_meta` and `icons` are ignored.

## Why it matters

A listing can change while a server is in use. Changed fields can change generated input or displayed behaviour after the first list. Findings are facts about differences between two sampled listings, not verdicts of intent.

## How it is decided

`title`, `description`, `inputSchema`, `outputSchema`, and `annotations` are compared as canonical JSON with sorted keys. A changed common-tool field is `FAIL`; added or removed tools only are `WARN`; no change is `PASS`; changed fields win over added or removed tools. `not_tested` is never counted or displayed as pass. Each change has `subject` set to the tool name, `detail` with field before and after values capped and redacted, and a constructed `tools/list` replay line.

## How to reproduce

Set an env variable named `CARETAKER_CANARY_TOKEN` to any value.

Start one fixture server with one shell command per line.

```sh
python examples/servers/bad_rug_pull.py after_calls_description
```

Send this constructed replay line after an initialize handshake.

```text
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

## Verdict

`FAIL` means a common tool's compared field changed after probes. `WARN` means tools were added or removed without a common-field change. `PASS` means the sampled listings matched. `not_tested` means the final liveness listing was unavailable. `not_tested` is never counted or displayed as pass.

## How to fix

Keep tool definitions stable for the life of one session. Do not change titles, descriptions, schemas, output schemas, or annotations after a call count or a generated valid call. Return one consistent listing for each `tools/list`.

## Limits

- Only three names are planted; other environment names are not checked.
- Only the value encoded on its own with standard base64 is detected; no other encoding is generated.
- Changes by time, by more calls, or by specific arguments are not caught; only the first and final sampled lists are compared.
- Stderr and stray stdout are covered by CT-CANARY-003 with a stderr cap; this page compares tool fields.
- A reordered listing with the same content passes because tools are matched by name.
