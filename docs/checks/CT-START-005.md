# CT-START-005 — Server exits after input is closed

## What it checks
Cleanup closes stdin, waits 5 seconds; this number is a guess; it lives in thresholds.py. The session records `exited_by_itself` before killing the process tree. The tree kill and temp cleanup still run on every path.

## Why it matters
A stdio server should stop when its input ends. The check reports whether it stopped by itself or had to be killed, without delaying cleanup.

## Verdict
`pass`: the server exited by itself. `warn`: the server had to be killed. `not_tested`: with a reason when the exit outcome was not recorded. `not_tested` is never counted or displayed as pass.

## How to fix
Stop reading and exit when stdin reaches EOF.

## Limits
The grace period is configurable on `LaunchSpec`. POSIX and Windows use different process-tree helpers; local Windows verification is limited to CI.
