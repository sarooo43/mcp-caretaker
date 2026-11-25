# 0007 - Honesty docs, gallery, and small CLI fixes

PR 6 adds three documentation surfaces (`docs/gallery.md`,
`docs/limitations.md`, and one extra fixture), rewrites the 20 older check
pages so every page has the same seven headings, and makes two small CLI
changes: the `CT-CANARY-003` pass summary now states how many sessions were
scanned, and a bare `mcp-caretaker check` prints the usage line. No new check,
score, grade, JUnit, SARIF, baseline, pytest helper, MCP front end, Docker,
HTTP, OAuth, LLM, `--version` flag, colours, suppress, new CLI option,
timestamp, changelog, or publishing was added. No new runtime dependency was
added and no version pin changed. Product code still makes no network calls,
and server text is still only inspected and quoted.

## T0 verification (all real runs, before coding)

- a. Base VERIFIED: `origin/main` is the PR 5 merge commit `e255b80`
  ("Merge pull request #5"), PR #5 reports state `MERGED`, and the platform
  branch head was `6761dec`.
- b. Installed command VERIFIED: with no arguments `mcp-caretaker` printed
  `usage: mcp-caretaker check --trust [options] -- PROGRAM [ARGS...]` to
  stderr and exited 2. `python -m mcp_caretaker` behaved the same way.
  `mcp-caretaker check` with nothing after it printed only
  `error: missing -- before the server command` and exited 2, with no usage
  line. That missing line is what D4 adds.
- c. CI VERIFIED by reading `.github/workflows/ci.yml`: one job with a matrix
  of ubuntu-latest and windows-latest against Python 3.11 and 3.13, install
  step `pip install -e ".[dev]"`, steps `ruff check`, `ruff format --check`,
  `pytest -q`, `timeout-minutes: 15`, `permissions: contents: read`, and
  `persist-credentials: false`. The console command comes from that install
  step, so D3 needs no workflow change.
- d. Fixtures VERIFIED: 40 files under `examples/servers/`, of which 24 are
  `bad_*.py`. Two of those take a mode argument (`bad_canary_leaks.py`,
  `bad_rug_pull.py`). Six switches are environment-only and have no row of
  their own: `CARETAKER_TEST_ZERO_TOOLS`, `CARETAKER_TEST_MODE`,
  `CARETAKER_TEST_SECOND_START_FAIL`, `CARETAKER_TEST_PIDFILE`,
  `CARETAKER_TEST_CALLLOG`, and `CARETAKER_STDERR_PADDING`.
- e. Page layout VERIFIED by reading every page: 20 pages
  (CT-START-001..005, CT-DESC-001..009, CT-ROB-001..006) had the five
  headings, and 5 pages (CT-CANARY-001..003, CT-STAB-001..002) had the seven
  headings. That is the split D5 closes.
- f. Summary site VERIFIED: `build_output_result` in `canary.py` builds the
  `CT-CANARY-003` result, and `runner._scan_session_stderr` feeds it once per
  session, including the second session. Nothing else writes that summary.
- g. Doc tests VERIFIED: `tests/test_docs.py` accepted either heading list
  (`(BASE, NEW)`), and it checks the banned words, the absence of dates and of
  chained shell commands, the twelve threshold lines, and that the documented
  check set matches the registry. `docs/gallery.md` and `docs/limitations.md`
  were not in those lists, so they were added there and covered by the new
  link test.
- h. Gallery rows VERIFIED by real runs: 33 planned rows were run through the
  installed CLI and the exact warn and fail sets were recorded in
  `docs/gallery.md`. `bad_huge_input.py` and `bad_hangs_on_startup.py` need
  `--call-timeout 2` and `--startup-timeout 2` in their rows, otherwise they
  dominate the run time.

## D1 and D4

`CT-CANARY-003` now reports
`{N} stderr bytes scanned across {S} session(s) and {M} stdout lines scanned; no findings.`
where `S` counts the sessions whose stderr was actually scanned and `N` stays
unclamped because the cap is per session. When a scanned session reached the
cap the summary adds ` Stderr cap of {C} bytes per session reached.` Finding
wording, verdicts, and the JSON field set are unchanged.

`mcp-caretaker` with no arguments and `mcp-caretaker check` with nothing after
it now both print the usage line to stderr and exit 2. No other CLI behaviour
changed.

## Gallery and limits pages

`docs/gallery.md` has one row per fixture with the columns `Fixture`,
`Arguments`, `Options`, `Expected warn/fail results`, and `Note`. Rows whose
run records no warn or fail result say `none` and are marked as not detected.
Environment-only fixtures are listed outside the table in words.
`tests/test_gallery.py` collects one real CLI run per row, asserts the warn
and fail set equals the listed set exactly, rejects malformed rows, and fails
if a `bad_*.py` fixture has no row.

`docs/limitations.md` states what the tool does not check, and the README
links to it and to the gallery. `tests/test_links.py` checks that every
relative Markdown link in the README, `docs/**/*.md`, and the fixtures README
resolves.

## Mutation proofs

Each mutation was applied to the working tree, the listed tests were run with
the project virtual environment, and the file was restored afterwards. The
restore was confirmed by re-reading the file, and `ruff check` plus
`ruff format --check` were run on every changed Python file, or on the whole
tree for the packaging mutation.

| ID | File | Mutation | Catching test | Observed result |
| --- | --- | --- | --- | --- |
| M1 | `canary.py` | Dropped the session count and the words "across ... session(s)" from the pass summary | `test_stderr_summary_names_two_sessions`, `test_stderr_summary_names_one_session_when_second_did_not_run`, `test_stderr_cap_counts_two_capped_scans` | 3 failed, 1 passed; ruff clean |
| M2 | `runner.py` | Second session's stderr scan call replaced with `second_exit_error = None` | `test_stderr_summary_names_two_sessions` | 1 failed, 1 passed; summary read `257 stderr bytes scanned across 1 session(s)`; ruff clean |
| M3 | `cli.py` | Usage line removed from the empty-argument branch of `check` | `test_bare_invocations_print_usage_on_stderr_and_exit_2` | 1 failed; stderr was empty; ruff clean |
| M4 | `pyproject.toml` | `[project.scripts]` entry removed, then the package reinstalled so the console command really disappeared | `test_console_command_runs_clean_server` | 1 failed at the helper (`assert None is not None`); ruff clean; pyproject restored and reinstalled |
| M5 | `docs/checks/CT-DESC-005.md` | The two new sections removed, leaving five headings | `test_every_check_has_docs_page_with_required_headings` | 1 failed at index 2; restored |
| M6 | `README.md` | Link target changed to a file that does not exist | `test_relative_markdown_links_point_to_existing_files` | 1 failed, reporting `README.md -> docs/limits-not-here.md`; restored |
| M7 | `docs/gallery.md` | `CT-DESC-001:warn` changed to `CT-DESC-001:fail` in one row | `test_gallery_row[bad_no_descriptions.py]` | 1 failed, 33 passed; restored |
| M8 | `docs/gallery.md` | Verdict token `CT-DESC-002:warn` changed to `CT-DESC-002:warns` in one row | `test_gallery_row[bad_description_length.py]`, `test_gallery_rows_are_well_formed` | 2 failed, 32 passed; restored |
| B1 | `checks/description.py` | `if run >= WHITESPACE_RUN_LIMIT:` became `if run >= WHITESPACE_RUN_LIMIT * 100:`, so `CT-DESC-008` can no longer warn for the 80-space fixture | `test_gallery_row[bad_whitespace_run.py]` | red: 1 failed, `assert set() == {('CT-DESC-008', 'warn')}`; after restore green: 1 passed; `git diff --stat` empty; ruff check and format clean |
| B2 | `docs/gallery.md` | The `bad_hostile_text.py` row was deleted from the Bad servers table | `test_every_bad_fixture_is_in_the_gallery` | red: 1 failed, `Extra items in the left set: 'bad_hostile_text.py'`; after restore green: 1 passed; `git diff --stat` empty |

## What is not verified here

- Windows timings and the Windows half of the matrix are only observed in CI.
- One earlier variant of M2 made the cached-stderr fallback stop counting its
  session. It stayed green on Linux, because the raw stderr reads succeed
  there, so it proves nothing locally. It is recorded as unverified.
