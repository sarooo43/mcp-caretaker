# 0011 - Case study on three reference servers

PR 8b publishes `docs/case-study.md` with three unedited runs. It changes no
`src/` file, no check, no threshold, no wording in the tool, no version and no
workflow, and it adds no dependency. The test count goes from 211 to 212.

## T0 findings (before any change)

- Base VERIFIED: the checkout's local base was again a one-file stub commit, so
  the branch base was aligned to `origin/main` (`30b5bbb`, "Merge pull request
  #9") with a hard reset before any edit. `git status --porcelain` was then
  empty. `git merge-base --is-ancestor b913f68 HEAD` confirmed that PR 8c is on
  `main`.
- Test count VERIFIED: `pytest --collect-only -q` reported `211 tests collected`.
- Versions VERIFIED by `pip install` into three separate virtual environments
  under `/tmp`: `mcp-server-time==2026.11.18`, `mcp-server-git==2026.11.18`,
  `mcp-server-fetch==2026.11.11`. `pip show` reported `License: MIT` for each and
  `Version` equal to the pinned number. No substitution was needed.
- Caretaker environment VERIFIED: a fresh virtual environment installed with
  `pip install .` from the clean checkout at commit
  `30b5bbb98230589529e9d35d28de2fb73214a9c1`, Python 3.11.2, `mcp 2.3.0`,
  `mcp-types 2.3.0`, `mcp-caretaker 0.0.0.dev0`.
- Report keys VERIFIED at `src/mcp_caretaker/report.py:65-70`: the JSON holds
  `"counts"` with the four keys `pass`, `warn`, `fail` and `not_tested`, and
  `build_report_dict` (`report.py:87-100`) writes `"server": {"program": ...}`
  plus `"tool": {"name": ..., "version": ...}`. The new test reads those key
  names rather than assuming them.
- Totals VERIFIED against the pre-run expectation: time `pass=21 warn=1 fail=0
  not_tested=3`, git `pass=23 warn=2 fail=0 not_tested=0`, fetch `pass=22
  warn=0 fail=0 not_tested=3`, all three runs exit code 0.

## Versions and commands

The caretaker virtual environment was `/tmp/ct8b/venv-caretaker`; each server had
its own environment, so their `mcp` versions never mixed. One command per line:

```sh
python -m venv /tmp/ct8b/venv-time
/tmp/ct8b/venv-time/bin/pip install mcp-server-time==2026.11.18
python -m venv /tmp/ct8b/venv-git
/tmp/ct8b/venv-git/bin/pip install mcp-server-git==2026.11.18
python -m venv /tmp/ct8b/venv-fetch
/tmp/ct8b/venv-fetch/bin/pip install mcp-server-fetch==2026.11.11
git init
git -c user.name=case-study -c user.email=case-study@example.invalid commit --allow-empty -m initial
/tmp/ct8b/venv-caretaker/bin/mcp-caretaker check --trust --json docs/case-study/time.json --markdown docs/case-study/time.md -- /tmp/ct8b/venv-time/bin/mcp-server-time
/tmp/ct8b/venv-caretaker/bin/mcp-caretaker check --trust --json docs/case-study/git.json --markdown docs/case-study/git.md -- /tmp/ct8b/venv-git/bin/mcp-server-git -r /tmp/ct8b/repo
/tmp/ct8b/venv-caretaker/bin/mcp-caretaker check --trust --json docs/case-study/fetch.json --markdown docs/case-study/fetch.md -- /tmp/ct8b/venv-fetch/bin/mcp-server-fetch
```

The throwaway repository lived at `/tmp/ct8b/repo`, held one empty commit and no
remote, and `-r` is the option `mcp-server-git --help` documents for confining
operations to one repository.

## Exit codes and totals

| Server | Exit code | Totals line |
| --- | --- | --- |
| time | 0 | `Totals: pass=21 warn=1 fail=0 not_tested=3` |
| git | 0 | `Totals: pass=23 warn=2 fail=0 not_tested=0` |
| fetch | 0 | `Totals: pass=22 warn=0 fail=0 not_tested=3` |

## Why the evidence is unedited

The six files under `docs/case-study/` are committed byte for byte as the tool
wrote them, because a report that is edited by hand stops being evidence: a
reader could no longer tell which numbers came from a run. Two consequences are
accepted on purpose.

- **The path `/tmp/ct8b/repo` appears** in `git.json` and `git.md`, because the
  server echoed it in the answers to the probes. It is a scratch folder on the
  run machine, not a path in this repository.
- **One clock value appears** in `time.json` and `time.md`, because
  `get_current_time` answered a call and the answer carries the time of that
  call. This is the only exception to the rule that the documentation holds no
  dates, and `docs/case-study.md` repeats no part of that value.

## The limit of the test

`tests/test_case_study.py` reads the four counts out of each saved JSON file and
asserts that one line of `docs/case-study.md` holds both the package name and the
`pass=N warn=N fail=N not_tested=N` string. It checks that the page and the saved
files agree; it cannot check that the numbers are correct, that the run was
honest, or that a claim in the surrounding prose follows from the evidence. Only
a re-run and a reading of the report can do that.

## Mutation proofs

- M1, page number: the time row of the results table was changed to
  `pass=20 warn=1 fail=0 not_tested=3`. `pytest -q tests/test_case_study.py` went
  red with `AssertionError: time` and `1 failed`; the row was restored and the
  test went green again.
- M2, saved count: `pass` was changed from 21 to 20 in
  `docs/case-study/time.json`. The same test went red with `AssertionError:
  time`; the file was restored with `git checkout -- docs/case-study/time.json`
  and `git diff --stat -- docs/case-study/time.json` was empty afterwards.
- Missing print or missing file was not needed here: the test is a pure
  documentation check with no console output of its own.
