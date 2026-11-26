# CT-START-005 — Server exits after input is closed

## What it checks
Cleanup closes stdin, waits 5 seconds; this number is a guess; it lives in thresholds.py. The session records `exited_by_itself` before killing the process tree. The tree kill and temp cleanup still run on every path.

## Why it matters
A stdio server should stop when its input ends. The check reports whether it stopped by itself or had to be killed, without delaying cleanup.

## How it is decided

After stdin is closed the runner waits up to `SHUTDOWN_GRACE_SECONDS = 5` seconds. `pass` when the child exits by itself, `warn` when the launcher has to kill it, and `not_tested` when the outcome was not recorded, for example because the session never started.

## How to reproduce

Run one command per line with absolute paths: `<python>` is the interpreter that has this package installed and `<repo>` is this repository. This row is in [the fixture gallery](../gallery.md).

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_ignores_stdin_close.py
```

## Verdict
`pass`: the server exited by itself. `warn`: the server had to be killed. `not_tested`: with a reason when the exit outcome was not recorded. `not_tested` is never counted or displayed as pass.

## How to fix
Stop reading and exit when stdin reaches EOF.

## Limits
The grace period is configurable on `LaunchSpec`. The cleanup uses POSIX process groups on POSIX and the SDK's Windows helpers on Windows; the Windows path is exercised by the test suite in the Windows CI jobs.
