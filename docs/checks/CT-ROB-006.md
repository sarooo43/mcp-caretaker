# CT-ROB-006 - Server remains responsive after probes

## What it checks

After `no_answer` or `exited` from a probe, an immediate `tools/list` liveness request is sent. If that liveness request fails, all further probes stop and this check is `fail`. If liveness succeeds, probing continues. If no failure stopped the run, one final `tools/list` liveness request is sent. Only `tools/call` and `tools/list` are sent by the probe group.

## Why it matters

A server that stops answering after a probe cannot complete the remaining observations in this run.

## How it is decided

After the probes one more `tools/list` is sent within `--call-timeout`. A failure is `fail` and a success is `pass`; when the probe phase was skipped or the time budget ran out the check is `not_tested`.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_dies_after_probes.py
```

## Verdict

- `pass`: the final liveness request returned within `call_timeout` and the child was still active.
- `fail`: the child exited, a call errored, or no answer arrived within `call_timeout` during liveness.
- `not_tested`: the session was unavailable before liveness or the outcome was not recorded. Skipped probes never pass, and the summary counts tested and skipped probes. `not_tested` is never counted or displayed as pass.

## How to fix

Keep the stdio session active after handling `tools/call`, and answer `tools/list` within the caller's timeout.

## Limits

`readOnlyHint` is untrusted, so a mislabelled writer receives valid and huge calls. Every probe sends a real request, so a server may act on it. Generated values are shown as placeholders. Replay lines are constructed, not captured, and need the initialize handshake first; they are not byte-exact. The numbers `1 MiB, 50 tools, 120 s` are guesses that live in `thresholds.py`. At most 4 probes per tool by design. Nested properties are not probed.
