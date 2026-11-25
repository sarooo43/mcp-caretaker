# mcp-caretaker

**Pre-release. Command line and library; no supported release workflow yet.**

mcp-caretaker is a free, MIT licensed, local-first project for observing **local MCP servers started over stdio**. This repository now contains a launcher, a library with 25 checks in five groups (startup, description/schema basics, robustness, canary, and stability), a `check` command with JSON and Markdown reports, and fixture servers. The library entry point is `mcp_caretaker.run_checks(spec, *, confirmed)`; it returns a frozen `RunResult` with one result per check ID.

There are no scores or grades, no MCP front end, no Docker or HTTP transport, no OAuth, no LLM, no publishing, no tags, and no changelog. No new runtime dependency was added.

All server text is untrusted input: product code only inspects and quotes it. It is never executed, used as a path, or sent to a network. Product code makes no network calls, telemetry calls, or LLM calls. Guessed check numbers live only in `src/mcp_caretaker/thresholds.py`, and the docs say so. Failing probe evidence may include constructed replay lines; the line is not captured, is not byte-exact, and needs an initialize handshake first. Every other evidence entry has `replay` set to `null`.

**NOT a sandbox: only test servers you trust.** Launching a server runs real code on your machine. The child environment is stripped and the process tree is killed on exit, but this is not isolation and makes no security guarantee.

**From this version, tools that declare readOnlyHint receive real calls with generated input. A server can lie about that hint. Only test servers you trust.**

## Install

The package is not published on an index yet, so install it from a local clone.
Run one command per line. With pip:

```sh
git clone https://github.com/sarooo43/mcp-caretaker.git
cd mcp-caretaker
python -m pip install .
```

With pipx:

```sh
git clone https://github.com/sarooo43/mcp-caretaker.git
cd mcp-caretaker
pipx install .
```

The console command is `mcp-caretaker`; `python -m mcp_caretaker` runs the same
code from the checkout. Python 3.11 or newer is required. The dependencies
`mcp` and `mcp-types` are installed from the package index with the versions
allowed by the range in `pyproject.toml`.

`mcp-caretaker --version` prints the tool name and version on one line.

## Usage

Run all 25 checks against one local server with the `check` command. The server command goes after the first `--` and is launched directly, never through a shell. Use absolute paths for the server program and script: relative paths are not rewritten, and the server starts in an empty working folder.

```sh
mcp-caretaker check --trust -- /absolute/path/to/server
```

`--trust` is required. It means this runs the server on your machine and is not a sandbox. Without `--trust` nothing is launched and no file is written. The same command works as `python -m mcp_caretaker check --trust -- /absolute/path/to/server`.

Options, all before the first `--`:

- `--trust`: confirm that running the server on this machine is intended.
- `--env NAME=VALUE`: extra environment variable for the server. Repeatable. Names starting with `CARETAKER_CANARY_` are rejected.
- `--startup-timeout SECONDS`: handshake timeout. Default comes from `LaunchSpec`.
- `--call-timeout SECONDS`: per-call timeout. Default comes from `LaunchSpec`.
- `--json PATH`: write the JSON report to `PATH`. Existing files are overwritten.
- `--markdown PATH`: write the Markdown report to `PATH`. Existing files are overwritten.
- `--fail-on fail|warn`: treat warnings as failures too. Default is `fail`.

The terminal prints one short line to stderr before the run, then a summary to stdout. The JSON report is the source of truth; Markdown is rendered from the same data. See [docs/report-format.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/report-format.md) for every field.

Exit codes: `0` means no check failed (and no check warned when `--fail-on warn` is given). `1` means at least one check failed, or at least one warned with `--fail-on warn`. `2` means a usage error, an unwritable output location, or an unexpected internal error. A `not_tested` result never changes the exit code. A server that does not start is a normal run with `CT-START-001` failed and exit code `1`.

A pass is not a safety guarantee. Running a server executes its code; this tool is not a sandbox.

### Limits

- A pass is not a safety guarantee. This tool is not a sandbox.
- Tools that declare readOnlyHint get real calls with generated input.
- The report never shows server arguments. A server could print its own arguments, and the report would then show that output.
- Findings are facts, not verdicts of intent.

The full list, including what is not checked at all, is in [docs/limitations.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/limitations.md). The fixture gallery with the results each fixture produces is in [docs/gallery.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/gallery.md).

## Secret canary and stability

`run_checks` plants three fresh fake values named `CARETAKER_CANARY_API_KEY`, `CARETAKER_CANARY_TOKEN`, and `CARETAKER_CANARY_SECRET` on every call through the existing stripped `extra_env` path. No allow-list is widened, and `confirmed=True` remains mandatory. Values are fresh per `run_checks` call and are shared by both sessions in that call. Canary checks scan tool answers, handshake and first-listing text, stderr from the start up to a guessed cap, and full stray stdout lines before display truncation. Exact values and their standard base64 forms are redacted before any result is returned; no real secrets, canary values, or base64 forms are written to results, evidence, messages, logs, or files. Findings are facts, not verdicts of intent. A deliberate show-environment tool is flagged, and v0.1 has no suppress.

Stability checks compare sampled tool listings by name using canonical JSON for `title`, `description`, `inputSchema`, `outputSchema`, and `annotations`. Order, top-level `_meta`, and icons are ignored. CT-STAB-001 opens a second session in one run-owned folder after the first session closes; CT-STAB-002 uses the final liveness listing without a new request. Only three names are planted; only the value encoded on its own with standard base64 is detected; changes by time, by more calls, or by specific arguments are not caught; stderr has a cap. See [docs/decisions/0005-canary-and-stability.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/decisions/0005-canary-and-stability.md) for the verification record.

See [docs/checks/README.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/checks/README.md) for the check index and verdict rules, [examples/servers/README.md](https://github.com/sarooo43/mcp-caretaker/blob/main/examples/servers/README.md) for the fixture gallery, and [docs/decisions/0001-sdk-and-protocol.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/decisions/0001-sdk-and-protocol.md) and [docs/decisions/0004-robustness-foundation.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/decisions/0004-robustness-foundation.md) for SDK verification. See [docs/DEV-WINDOWS.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/DEV-WINDOWS.md) for Windows test instructions. See [docs/RELEASING.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/RELEASING.md) for the owner's release steps.

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
