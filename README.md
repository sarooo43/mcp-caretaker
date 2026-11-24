# mcp-caretaker

**Pre-release. Library only; no supported command line workflow yet.**

mcp-caretaker is a free, MIT licensed, local-first project for observing **local MCP servers started over stdio**. This repository now contains a launcher, a library with 14 startup and description/schema checks, and fixture servers. The library entry point is `mcp_caretaker.run_checks(spec, *, confirmed)`; it returns a frozen `RunResult` with one result per check ID.

There is no check command yet. The command line interface still has only `--version` and `--help`. There are no report files, no scores or grades, no MCP front end, no Docker or HTTP transport, no OAuth, no LLM, no publishing, no tags, and no changelog. No new runtime dependency was added.

All server text is untrusted input: product code only inspects and quotes it. It is never executed, used as a path, or sent to a network. Product code makes no network calls, telemetry calls, or LLM calls. Guessed check numbers live only in `src/mcp_caretaker/thresholds.py`, and the docs say so.

**NOT a sandbox: only test servers you trust.** Launching a server runs real code on your machine. The child environment is stripped and the process tree is killed on exit, but this is not isolation and makes no security guarantee.

See `docs/checks/README.md` for the check index and verdict rules, `examples/servers/README.md` for the fixture gallery, and `docs/decisions/` for SDK verification. See `docs/DEV-WINDOWS.md` for Windows test instructions.

## Shell instructions

Run one command per line. POSIX:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/ruff check
.venv/bin/ruff format --check
.venv/bin/pytest -q
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\ruff.exe check
.venv\Scripts\ruff.exe format --check
.venv\Scripts\pytest.exe -q
```
