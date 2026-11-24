# mcp-caretaker

**Pre-release. Nothing usable yet.**

mcp-caretaker is intended to become a runtime behaviour tester for **local MCP
servers started over stdio**. The plan is to launch a server and observe what it
actually does: startup, hostile inputs, a planted fake secret, and stability across
connections. It is meant to complement static scanners, not replace them.

Right now this repository contains only a project skeleton, a launcher, and test
servers. There are no checks, no reports, and no command line commands except
`--version` and `--help`.

**NOT a sandbox: only test servers you trust.** Launching a server runs real code on
your machine. The child environment is stripped and the process tree is killed on
exit, but this is not isolation and makes no security guarantee.

The project is MIT licensed, free, and local-first. See `docs/DEV-WINDOWS.md` for
running the tests on Windows and `docs/decisions/` for the SDK verification.
