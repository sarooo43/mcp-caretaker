# Check library

This PR adds a library, not a command. `mcp_caretaker.run_checks(spec, *, confirmed)` returns a frozen `RunResult`; it never prints and never writes a report file. `confirmed=True` is mandatory: `ConfirmationRequired` propagates before any process is spawned. The handshake stays with the current installed SDK.

Fourteen check IDs run in registry order, and one result per ID is always present. Verdicts are exactly `pass`, `warn`, `fail`, and `not_tested`. A `not_tested` result always has a reason and is never counted or displayed as pass. A crash inside one check becomes `not_tested` with reason `internal error in check: <ExceptionType>: <message, redacted>`, while other checks still run. Per-tool problems are aggregated into one `CheckResult` per ID.

All server text is untrusted input. It is only inspected and quoted; it is never executed, used as a path, or sent to a network. `argv` is not placed into the result in this PR. Evidence strings are redacted with the run's `extra_env`, non-printables are shown as `\uXXXX` escapes, long strings end with `...[truncated]`, items are capped, and omitted items appear as `N more not shown`.

The official SDK and specification facts behind these checks were VERIFIED in `../decisions/0003-checks-foundation.md` and `../decisions/0003-evidence/`. The tool name rule is SHOULD in the official tools page, so CT-DESC-009 warns.

## Thresholds

Only `src/mcp_caretaker/thresholds.py` holds these check thresholds. The numbers are guesses, not measurements.

- `DESC_MIN_LENGTH = 10` — this number is a guess; it lives in thresholds.py.
- `DESC_MAX_LENGTH = 1000` — this number is a guess; it lives in thresholds.py.
- `WHITESPACE_RUN_LIMIT = 40` — this number is a guess; it lives in thresholds.py.
- `MAX_TOOLS_PAGES = 10` — this number is a guess; it lives in thresholds.py.
- `EVIDENCE_MAX_ITEMS = 20` — this number is a guess; it lives in thresholds.py.
- `EVIDENCE_MAX_CHARS = 300` — this number is a guess; it lives in thresholds.py.
- `SHUTDOWN_GRACE_SECONDS = 5` — this number is a guess; it lives in thresholds.py.

## Check index

| ID | Title | Page |
| --- | --- | --- |
| CT-START-001 | Server starts and completes handshake | [CT-START-001](CT-START-001.md) |
| CT-START-002 | Handshake reports server name and version | [CT-START-002](CT-START-002.md) |
| CT-START-003 | tools/list works | [CT-START-003](CT-START-003.md) |
| CT-START-004 | No non-protocol text on stdout | [CT-START-004](CT-START-004.md) |
| CT-START-005 | Server exits after input is closed | [CT-START-005](CT-START-005.md) |
| CT-DESC-001 | Every tool has a description | [CT-DESC-001](CT-DESC-001.md) |
| CT-DESC-002 | Description length is within limits | [CT-DESC-002](CT-DESC-002.md) |
| CT-DESC-003 | Tool names are unique | [CT-DESC-003](CT-DESC-003.md) |
| CT-DESC-004 | Every tool has an object inputSchema | [CT-DESC-004](CT-DESC-004.md) |
| CT-DESC-005 | Every top-level property is typed | [CT-DESC-005](CT-DESC-005.md) |
| CT-DESC-006 | Every top-level property has a description | [CT-DESC-006](CT-DESC-006.md) |
| CT-DESC-007 | No hidden characters in scanned text | [CT-DESC-007](CT-DESC-007.md) |
| CT-DESC-008 | No long horizontal whitespace runs | [CT-DESC-008](CT-DESC-008.md) |
| CT-DESC-009 | Tool names match the spec name rule | [CT-DESC-009](CT-DESC-009.md) |

## What is not here

No score, grade, report file, JUnit output, pytest helper, MCP front end, Docker, HTTP transport, OAuth, LLM, extra CLI command, publishing, tag, or changelog. No new runtime dependency was added. No future check group is built or described as working.

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

## Open design points

- Relative script paths in `argv` are not rewritten; tests use absolute paths.
- The stripped child environment may break servers needing `HOME`, `USERPROFILE`, or arbitrary parent variables.
- `extra_env` values shorter than 4 characters are not redacted.
- Windows local verification is limited to GitHub Actions CI.
- `readOnlyHint` remains an untrusted hint and is not used by these checks.
- An empty tool list is valid for a server offering other features, so it warns rather than fails.
