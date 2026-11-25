# Check library

This PR adds a library, not a command. `mcp_caretaker.run_checks(spec, *, confirmed)` returns a frozen `RunResult`; it never prints and never writes a report file. `confirmed=True` is mandatory: `ConfirmationRequired` propagates before any process is spawned. The handshake stays with the current installed SDK.

Twenty-five check IDs run in five groups: startup, description/schema basics, robustness, canary, and stability. One result per ID is always present in registry order. Verdicts are exactly `pass`, `warn`, `fail`, and `not_tested`. A `not_tested` result always has a reason and is never counted or displayed as pass. A crash inside one check becomes `not_tested` with reason `internal error in check: <ExceptionType>: <message, redacted>`, while other checks still run. Per-tool problems are aggregated into one `CheckResult` per ID. Probe results use a partial-coverage summary that counts tested and skipped probes; skipped probes never pass.

All server text is untrusted input. It is only inspected and quoted; it is never executed, used as a path, or sent to a network. `argv` is not placed into the result in this PR. Evidence strings are redacted with the run's `extra_env`, canary values, standard base64 forms, and values following `--env`, non-printables are shown as `\\uXXXX` escapes, long strings end with `...[truncated]`, items are capped, and omitted items appear as `N more not shown`. A replay line is constructed, not captured, is not byte-exact, and needs initialize handshake first. Evidence includes `replay` as `null` unless a finding or failing probe has a constructed line. Only `tools/call` and `tools/list` are sent by the probe group; stability uses the final liveness list and a second-session list.

The official SDK and specification facts behind these checks were VERIFIED in `../decisions/0004-robustness-foundation.md` and `../decisions/0004-evidence/`. The canary and stability findings are recorded in `../decisions/0005-canary-and-stability.md`. The tool name rule is SHOULD in the official tools page, so CT-DESC-009 warns. The unknown-tool protocol rule is VERIFIED from the official tools page and the pinned SDK.

## Thresholds

Only `src/mcp_caretaker/thresholds.py` holds these check thresholds. The numbers are guesses, not measurements. The probe guesses are `1 MiB, 50 tools, 120 s` in `thresholds.py`. The stderr scan cap is also `1 MiB` per session, and every session's stderr is scanned.

- `DESC_MIN_LENGTH = 10` — this number is a guess; it lives in thresholds.py.
- `DESC_MAX_LENGTH = 1000` — this number is a guess; it lives in thresholds.py.
- `WHITESPACE_RUN_LIMIT = 40` — this number is a guess; it lives in thresholds.py.
- `MAX_TOOLS_PAGES = 10` — this number is a guess; it lives in thresholds.py.
- `EVIDENCE_MAX_ITEMS = 20` — this number is a guess; it lives in thresholds.py.
- `EVIDENCE_MAX_CHARS = 300` — this number is a guess; it lives in thresholds.py.
- `SHUTDOWN_GRACE_SECONDS = 5` — this number is a guess; it lives in thresholds.py.
- `HUGE_STRING_LENGTH = 1048576` — this number is a guess; it lives in thresholds.py.
- `MAX_TOOLS_PROBED = 50` — this number is a guess; it lives in thresholds.py.
- `PROBE_BUDGET_SECONDS = 120` — this number is a guess; it lives in thresholds.py.
- `REPLAY_MAX_CHARS = 2000` — this number is a guess; it lives in thresholds.py.
- `STDERR_SCAN_MAX_BYTES = 1048576` — this number is a guess; it lives in thresholds.py.

## Check index

| Group | ID | Title | Page |
| --- | --- | --- | --- |
| startup | CT-START-001 | Server starts and completes handshake | [CT-START-001](CT-START-001.md) |
| startup | CT-START-002 | Handshake reports server name and version | [CT-START-002](CT-START-002.md) |
| startup | CT-START-003 | tools/list works | [CT-START-003](CT-START-003.md) |
| startup | CT-START-004 | No non-protocol text on stdout | [CT-START-004](CT-START-004.md) |
| startup | CT-START-005 | Server exits after input is closed | [CT-START-005](CT-START-005.md) |
| description/schema basics | CT-DESC-001 | Every tool has a description | [CT-DESC-001](CT-DESC-001.md) |
| description/schema basics | CT-DESC-002 | Description length is within limits | [CT-DESC-002](CT-DESC-002.md) |
| description/schema basics | CT-DESC-003 | Tool names are unique | [CT-DESC-003](CT-DESC-003.md) |
| description/schema basics | CT-DESC-004 | Every tool has an object inputSchema | [CT-DESC-004](CT-DESC-004.md) |
| description/schema basics | CT-DESC-005 | Every top-level property is typed | [CT-DESC-005](CT-DESC-005.md) |
| description/schema basics | CT-DESC-006 | Every top-level property has a description | [CT-DESC-006](CT-DESC-006.md) |
| description/schema basics | CT-DESC-007 | No hidden characters in scanned text | [CT-DESC-007](CT-DESC-007.md) |
| description/schema basics | CT-DESC-008 | No long horizontal whitespace runs | [CT-DESC-008](CT-DESC-008.md) |
| description/schema basics | CT-DESC-009 | Tool names match the spec name rule | [CT-DESC-009](CT-DESC-009.md) |
| robustness | CT-ROB-001 | Wrong-type input is rejected | [CT-ROB-001](CT-ROB-001.md) |
| robustness | CT-ROB-002 | Missing required input is rejected | [CT-ROB-002](CT-ROB-002.md) |
| robustness | CT-ROB-003 | Unknown tool name is rejected | [CT-ROB-003](CT-ROB-003.md) |
| robustness | CT-ROB-004 | Large string input is handled | [CT-ROB-004](CT-ROB-004.md) |
| robustness | CT-ROB-005 | Valid read-only call succeeds | [CT-ROB-005](CT-ROB-005.md) |
| robustness | CT-ROB-006 | Server remains responsive after probes | [CT-ROB-006](CT-ROB-006.md) |
| canary | CT-CANARY-001 | Canary values are absent from tool answers | [CT-CANARY-001](CT-CANARY-001.md) |
| canary | CT-CANARY-002 | Canary values are absent from handshake and tool listings | [CT-CANARY-002](CT-CANARY-002.md) |
| canary | CT-CANARY-003 | Canary values are absent from stderr and stray stdout | [CT-CANARY-003](CT-CANARY-003.md) |
| stability | CT-STAB-001 | Tool listings are stable across a second session | [CT-STAB-001](CT-STAB-001.md) |
| stability | CT-STAB-002 | Tool listing is stable after probes | [CT-STAB-002](CT-STAB-002.md) |

## What is not here

No score, grade, JUnit output, pytest helper, MCP front end, Docker, HTTP transport, OAuth, LLM, extra CLI command, publishing, tag, or changelog. No raw protocol garbage. No allow-list widening, opt-out flags, or suppression for v0.1. No dependency pin change and no new runtime dependency. At most 4 probes per tool by design; there is no `MAX_PROBES_PER_TOOL` constant. Secret-value probes and tool-list comparison are now part of the library; findings are facts, not verdicts of intent.

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
- Only three canary names are planted; a deliberate show-environment tool is flagged and v0.1 has no suppress.
- Only the value encoded on its own with standard base64 is detected; stderr is capped at 1 MiB per session.
- Windows local verification is limited to GitHub Actions CI.
- `readOnlyHint` is untrusted; only test servers you trust.
- An empty tool list is valid for a server offering other features, so it warns rather than fails.
