# CT-STAB-001 - Tool listings are stable across a second session

## What it checks

After the first session fully closes, `run_checks` opens a second session with the same `LaunchSpec` and the same run-owned folder. The runner removes that folder at the end, including when a session raises. The second session completes a handshake and a full `tools/list`; its raw tools are compared with the first session's raw tools. Common tools are matched by name, order is ignored, and top-level `_meta` and `icons` are ignored.

## Why it matters

A client may reconnect to the same server and rely on earlier tool definitions. Changed fields can change generated input or displayed behaviour. Findings are facts about differences between two sampled listings, not verdicts of intent.

## How it is decided

`title`, `description`, `inputSchema`, `outputSchema`, and `annotations` are compared as canonical JSON with sorted keys. A changed common-tool field is `FAIL`; added or removed tools only are `WARN`; no change is `PASS`; changed fields win over added or removed tools. A second start or list failure is `not_tested` with a reason and exact redacted error evidence. The check does not run when the first session never reached `tools/list`. `not_tested` is never counted or displayed as pass. Each change has `subject` set to the tool name, `detail` with field before and after values capped and redacted, and a constructed `tools/list` replay line.

## How to reproduce

Set an env variable named `CARETAKER_CANARY_TOKEN` to any value.

Start one fixture server with one shell command per line.

```sh
python examples/servers/bad_rug_pull.py reconnect_description
```

Send this constructed replay line after an initialize handshake.

```text
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

## Verdict

`FAIL` means a common tool's compared field changed. `WARN` means tools were added or removed without a common-field change. `PASS` means the two sampled listings matched. `not_tested` means the second session or its listing was unavailable. `not_tested` is never counted or displayed as pass.

## How to fix

Keep reconnect-time tool definitions stable. Do not change titles, descriptions, schemas, output schemas, or annotations based on a shared-folder marker. If the second session cannot start or list tools, fix startup and listing before relying on this comparison.

## Limits

- Only three names are planted; other environment names are not checked.
- Only the value encoded on its own with standard base64 is detected; no other encoding is generated.
- Changes by time, by more calls, or by specific arguments are not caught; only two sampled listings are compared.
- Stderr and stray stdout are covered by CT-CANARY-003 with a stderr cap; this page compares tool fields.
- Windows local verification is limited to GitHub Actions CI.
