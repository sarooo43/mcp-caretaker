# mcp-caretaker

**Pre-release. Library only; no supported command line workflow yet.**

mcp-caretaker is a free, MIT licensed, local-first project for observing **local MCP servers started over stdio**. This repository now contains a launcher, a library with 25 checks in five groups (startup, description/schema basics, robustness, canary, and stability), and fixture servers. The library entry point is `mcp_caretaker.run_checks(spec, *, confirmed)`; it returns a frozen `RunResult` with one result per check ID.

There is no check command yet. The command line interface still has only `--version` and `--help`. There are no report files, no scores or grades, no MCP front end, no Docker or HTTP transport, no OAuth, no LLM, no publishing, no tags, and no changelog. No new runtime dependency was added.

All server text is untrusted input: product code only inspects and quotes it. It is never executed, used as a path, or sent to a network. Product code makes no network calls, telemetry calls, or LLM calls. Guessed check numbers live only in `src/mcp_caretaker/thresholds.py`, and the docs say so. Failing probe evidence may include constructed replay lines; the line is not captured, is not byte-exact, and needs an initialize handshake first. Every other evidence entry has `replay` set to `null`.

**NOT a sandbox: only test servers you trust.** Launching a server runs real code on your machine. The child environment is stripped and the process tree is killed on exit, but this is not isolation and makes no security guarantee.

**From this version, tools that declare readOnlyHint receive real calls with generated input. A server can lie about that hint. Only test servers you trust.**

## Secret canary and stability

`run_checks` plants three fresh fake values named `CARETAKER_CANARY_API_KEY`, `CARETAKER_CANARY_TOKEN`, and `CARETAKER_CANARY_SECRET` on every call through the existing stripped `extra_env` path. No allow-list is widened, and `confirmed=True` remains mandatory. Values are fresh per `run_checks` call and are shared by both sessions in that call. Canary checks scan tool answers, handshake and first-listing text, stderr from the start up to a guessed cap, and full stray stdout lines before display truncation. Exact values and their standard base64 forms are redacted before any result is returned; no real secrets, canary values, or base64 forms are written to results, evidence, messages, logs, or files. Findings are facts, not verdicts of intent. A deliberate show-environment tool is flagged, and v0.1 has no suppress.

Stability checks compare sampled tool listings by name using canonical JSON for `title`, `description`, `inputSchema`, `outputSchema`, and `annotations`. Order, top-level `_meta`, and icons are ignored. CT-STAB-001 opens a second session in one run-owned folder after the first session closes; CT-STAB-002 uses the final liveness listing without a new request. Only three names are planted; only the value encoded on its own with standard base64 is detected; changes by time, by more calls, or by specific arguments are not caught; stderr has a cap. See `docs/decisions/0005-canary-and-stability.md` for the verification record.

See `docs/checks/README.md` for the check index and verdict rules, `examples/servers/README.md` for the fixture gallery, and `docs/decisions/` for SDK verification, including `0004-robustness-foundation.md`. See `docs/DEV-WINDOWS.md` for Windows test instructions.

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
