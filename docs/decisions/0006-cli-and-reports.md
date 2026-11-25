# 0006 - Command line and reports

PR 5 adds the `check` command, a JSON report as the source of truth, Markdown
rendered from the same data, and a short ASCII terminal summary. No new check,
score, grade, JUnit or SARIF output, baseline, pytest helper, MCP front end,
Docker, HTTP, OAuth, LLM, `--version` flag, colours, suppress, config file,
or publishing was added. No new runtime dependency was added: only the
standard library (`argparse`, `json`, `pathlib`, `dataclasses`, `asyncio`)
plus existing project modules. Server text is untrusted input: product code
only inspects and quotes it. It is never executed, used as a path, or sent to
a network. Product code makes no network calls.

## T0 verification (all real runs, before coding)

- a. Entry points VERIFIED: `pyproject.toml` already has
  `[project.scripts] mcp-caretaker = "mcp_caretaker.cli:main"`;
  `src/mcp_caretaker/__main__.py` exists and calls `raise SystemExit(main())`;
  `src/mcp_caretaker/__init__.py` holds `__version__` as the runtime version
  source. The old `cli.py` was a stub with only `--version` and `--help`.
- b. Library surface VERIFIED by inspection: `run_checks(spec, *, confirmed)`
  is async with keyword-only `confirmed`; `RunResult` holds
  `caretaker_version`, `protocol_version`, `server_name`, `server_version`,
  and `results`; `to_dict()` returns those keys plus per-result `check_id`,
  `title`, `verdict`, `summary`, `evidence`, and `reason`, with evidence
  `subject`, `detail`, and `replay`. `LaunchSpec` holds `argv`,
  `extra_env`, `startup_timeout` 30.0, `call_timeout` 10.0, and
  `shutdown_grace`. The negotiated protocol version lives in
  `RunResult.protocol_version`.
- c. Dead server VERIFIED by real runs: a non-existent program and
  `bad_exits_immediately.py` both return normally with `CT-START-001` FAIL
  and 24 `not_tested` results. No exception escapes `run_checks`. The CLI
  therefore treats a dead server as a normal run with exit code 1.
- d. `--env` precedence VERIFIED by a real run with fixed canary values: a
  user `extra_env` entry named `CARETAKER_CANARY_TOKEN` never reaches the
  child. The runner overwrites it with the fresh canary value, so the
  stderr scan still finds the canary value and the user value is absent.
  This is why the CLI rejects `--env` names starting with
  `CARETAKER_CANARY_`.
- e. Text safety VERIFIED: `visible_text` escapes escape and control
  characters as visible escapes but keeps printable non-ASCII letters. The
  terminal therefore needs its own ASCII-only escape function (D6).
- f. Determinism VERIFIED: two real `run_checks` runs against
  `clean_server.py` gave byte-identical `to_dict()` JSON, and two real CLI
  runs gave byte-identical JSON files (D9).
- g. Stderr cap VERIFIED by a real subprocess with the cap set to 64 and
  100 bytes of padding: the summary reports `128 stderr bytes scanned` and
  the value past the cap is not found (D10).
- h. Timing VERIFIED: one clean-server `run_checks` run took about 1.5
  seconds locally. `pyproject.toml` sets a 60 second per-test timeout, so
  CLI subprocess tests use a 30 second timeout: above real runtime, below
  the pytest timeout. CI allows 15 minutes per job.
- i. Docs constraints VERIFIED: `tests/test_docs.py` passed (5 tests). New
  docs avoid dates, chained shell commands, personal paths, and banned
  words. One shell command is shown per line.

## Decisions

- D1: The CLI splits the argument list at the first literal `--` itself,
  before argparse runs. The server command after it is launched directly
  with no shell, and later `--` values reach the server unchanged. No
  separator or an empty server command is exit code 2.
- D2: Without `--trust` the CLI prints a short message saying `--trust`
  means this runs the server on your machine and is not a sandbox, then
  exits 2. Nothing is launched and no file is written. The check happens
  before any launch.
- D3: Each `--env` item is split at the first `=`. An item with no `=` or
  an empty name is exit code 2. A name starting with `CARETAKER_CANARY_`
  is exit code 2, because the runner would overwrite it anyway (T0 d).
- D4: `--startup-timeout` and `--call-timeout` are floats greater than 0.
  Defaults are read from `LaunchSpec` field defaults, never duplicated.
- D5: Output parent folders are validated before launch: each must exist
  and be a folder, and `--json` and `--markdown` must differ. Existing
  files are overwritten. Full text is rendered first, then each file is
  written once as UTF-8 with a trailing newline. A write failure exits 2
  after the terminal summary.
- D6: One escape function escapes every character outside printable ASCII
  (including escape and control characters) for the terminal. Backslash is
  doubled so server text cannot fake an escape sequence. Output does not
  depend on the console code page.
- D7: The JSON dict has fixed key order, indent 2, escaped non-ASCII, and
  a trailing newline, with no timestamp or per-run value. `server.program`
  is the file name only for both slash styles. `server.argument_count`
  counts arguments after the program. Server arguments are never written.
  The version comes from the existing single source via
  `RunResult.caretaker_version`. Results reuse `RunResult.to_dict()`.
- D8: Markdown is rendered from the same dict. The table holds only
  constant strings (ID, title, verdict). Every server-derived string
  (summary, reason, evidence subject, detail, replay) appears only inside
  a fenced code block whose fence is longer than the longest backtick run
  inside it, minimum 3. One small pure fence function does this.
- D9: Two unchanged-server runs give byte-identical JSON. No result-text
  change was needed, so there is no deviation.
- D10: The `128 stderr bytes scanned` figure is the sum of two capped
  reads, one per session, each capped at 64. The cap is applied per
  `read_stderr_prefix` call, so no single scan exceeds the cap. The total
  across two sessions is twice the cap. This is explained here and proven
  by a real-subprocess test; no code change was needed.

## Fixtures

- `examples/servers/bad_hostile_text.py` is new. Its tool description
  carries 3- and 5-backtick runs, a markdown link, an HTML tag, an escape
  character, and a non-ASCII letter. Checks never quote a description
  (verified by a real run: the description text never reached any result),
  so the same text is also written as one stdout noise line. The startup
  check quotes that line in evidence, which is what report rendering must
  fence and escape. Without the noise line the hostile text would never
  reach a report.
- No marker fixture was added. The existing `bad_huge_input.py` pidfile
  proves no launch: without `--trust` the pidfile is never created.

## Forced test change

- `tests/test_cli.py::test_cli_version_runs` was removed. It asserted
  `python -m mcp_caretaker --version`, and PR 5 explicitly has no
  `--version` flag. The file now holds the `check` command tests. No other
  pre-existing test was modified.

## T7 unused-code review

Exact commands, one per line:

```sh
.venv/bin/ruff check
.venv/bin/ruff format --check
python3 -m venv /tmp/pr5-vulture-venv
/tmp/pr5-vulture-venv/bin/python -m pip install -q --disable-pip-version-check vulture
/tmp/pr5-vulture-venv/bin/vulture src tests examples
grep -RInE "TODO|FIXME|NotImplemented" src tests examples docs README.md pyproject.toml .github
```

`ruff check` printed `All checks passed!`; `ruff format --check` printed
`102 files already formatted`. The grep printed one match: the quoted grep
command itself in `docs/decisions/0005-canary-and-stability.md`. There is no
TODO, FIXME, or NotImplemented marker in code. One throwaway
`vulture src tests examples` invocation exited with code 3 and printed
exactly eight items, all false positives:

1. `examples/servers/good_server.py:30: unused function 'save_note' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
2. `examples/servers/probe_server.py:23: unused function 'env_names' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
3. `examples/servers/probe_server.py:41: unused function 'shout_env' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
4. `examples/servers/spawns_grandchild.py:36: unused function 'ping' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
5. `src/mcp_caretaker/session.py:580: unused variable 'exc_type' (100% confidence)` — false positive; `__aexit__` requires this parameter.
6. `src/mcp_caretaker/session.py:582: unused variable 'tb' (100% confidence)` — false positive; `__aexit__` requires this parameter.
7. `tests/conftest.py:8: unused function 'anyio_backend' (60% confidence)` — false positive; pytest discovers this fixture.
8. `tests/test_canary_runner.py:27: unused function 'fixed_canary' (60% confidence)` — false positive; pytest discovers this autouse fixture.

No dead code was removed: vulture found no new item in `report.py`,
`cli.py`, or `bad_hostile_text.py`. Reused helpers: `redact_values`,
`run_checks`, `LaunchSpec`, `RunResult.to_dict`, `CHECKS`, `CHECK_IDS`,
`EVIDENCE_MAX_CHARS`, `server_path`, and `server_argv` shapes. No new
runtime dependency, development dependency, CI step, helper script, or
output file was added for the unused-code review.

## T8 mutation proof

Local mutations were applied one at a time to working-tree files. Each ran
the named pytest node, saw a red result, restored the exact original text,
saw a green result, and left the file unchanged. No mutation helper script
or output file was stored in the repository.

| ID | Changed file and mutation | Named pytest node | Red | Restored | File unchanged |
| --- | --- | --- | --- | --- | --- |
| M1 | `cli.py`: trust gate disabled | `test_missing_trust_exits_2_and_launches_nothing` | `1 failed in 4.37s` | `1 passed in 1.24s` | YES |
| M2 | `cli.py`: full argv joined into JSON program | `test_server_arguments_never_written` | `1 failed in 2.84s` | `1 passed in 2.84s` | YES |
| M3 | `cli.py`: `--fail-on` ignored | `test_warn_server_exit_codes` | `1 failed in 2.16s` | `1 passed in 2.15s` | YES |
| M4 | `report.py`: `not_tested` counts as fail | `test_only_writers_not_tested_keeps_exit_zero` | `1 failed in 1.39s` | `1 passed in 1.37s` | YES |
| M5 | `report.py`: fixed 3-backtick fence | `test_hostile_text_escaped_and_fenced` | `1 failed in 1.36s` | `1 passed in 1.31s` | YES |
| M6 | `report.py`: terminal escape disabled | `test_hostile_text_escaped_and_fenced` | `1 failed in 1.39s` | `1 passed in 1.44s` | YES |
| M7 | `report.py`: timestamp added to JSON | `test_clean_server_exit_zero_with_json_and_markdown` | `1 failed in 2.82s` | `1 passed in 2.68s` | YES |
| M8 | `cli.py`: startup timeout not passed | `test_startup_and_call_timeouts` | `1 failed in 30.75s` | `1 passed in 6.11s` | YES |
| M9 | `cli.py`: path checks moved after the run | `test_output_paths_validated_before_launch` | `1 failed in 4.43s` | `1 passed in 1.92s` | YES |

M8 went red because the hanging server then used the 30 second default and
the 30 second subprocess timeout fired.

M6 remote proof used the throwaway branch `mutation/pr5-m6-windows`,
mutation commit `8e74b7910bbb85602214a98a37f8075befe8c98a`, parent commit
`2672eea52481481b2e3513392386f1796e532da8`, and `workflow_dispatch` run
`https://github.com/sarooo43/mcp-caretaker/actions/runs/45518255957`. The
run conclusion was `failure`. Per-job results were: windows 3.11 job
`138883214062` `failure`; ubuntu 3.13 job `138883214390` `failure`; windows
3.13 job `138883214406` `failure`; ubuntu 3.11 job `138883214506`
`failure`. The Windows 3.11 signed log showed `2 failed, 158 passed in
93.01s`, including the hostile-text subprocess test failing because the
unescaped terminal output could not be written. The branch was deleted and
no pull request was opened from it.

The mutation commit differs from the final head in
`docs/decisions/0006-cli-and-reports.md` and `src/mcp_caretaker/report.py`.
The final head includes this proof text and the restored escape function;
the mutation commit contains the disabled escape and lacks the appended
proof text. No canary value, base64 form, helper script, or output file
was stored for the mutation proof.

## Windows CI fixes after the first pull request run

The first pull request run `45518867135` on head
`aa43059963aa43237159473edf688ba212f73c06` was green on both Ubuntu jobs and
red on both Windows jobs: windows 3.13 job `138885305592` `failure` and
windows 3.11 job `138885305607` `failure`, with `2 failed, 158 passed` in the
Windows 3.11 job. Both failures were in the CLI tests, not in a check.

1. `test_clean_server_exit_zero_with_json_and_markdown` expected the output
   path back exactly as given. The terminal reported it with doubled
   backslashes, because the escape function doubles backslash and a Windows
   path contains backslash. Decision: the two output file paths are the
   user's own arguments and not server text, so they now use the same escape
   function with `escape_backslash=False`. Every other string keeps the
   strict escaping, and a pure test
   `test_terminal_prints_local_paths_without_doubling_backslashes` covers a
   Windows-style path. `docs/report-format.md` records the rule.
2. `test_hostile_text_escaped_and_fenced` expected `caf\u00E9` in the
   terminal output. On Windows the fixture wrote the hostile stdout line
   through text mode, which encodes as the console code page, so the UTF-8
   byte for `\u00e9` was replaced before the tool saw it. Decision: the
   fixture now writes stdout noise as UTF-8 bytes
   (`sys.stdout.buffer.write`), so the byte stream is the same on every
   platform; the tool was not changed. Verified locally by running the
   fixture with `PYTHONIOENCODING=cp1252` and observing the two UTF-8 bytes
   `0xC3 0xA9`.

Both changes are test and fixture changes plus one rendering choice for
non-server paths; no check, threshold, or scoring behaviour changed.
