# 0008 - Release readiness

PR 7 makes the package installable and releasable by a stranger, without adding
a single check and without changing any check behaviour. It restores
`--version`, moves the version to one source, widens the SDK pin to a range,
fills in the package metadata a PyPI page needs, adds a `package` CI job that
installs the built wheel into a fresh environment on Linux and Windows, adds
`docs/RELEASING.md` for the owner, and closes the four carry-overs from PR 6.
Nothing is published: no PyPI account, token, workflow, tag or upload exists in
this PR.

## T0 findings (all real runs, before coding)

- T0.1 Base VERIFIED: `origin/main` is `e9dc130` ("Merge pull request #6"),
  `docs/gallery.md` is present, and `pytest --collect-only -q` reports
  `200 tests collected`.
- T0.2 Version VERIFIED by reading the tree. The version text `0.0.0.dev0`
  appeared in `pyproject.toml` (line 7) and in `src/mcp_caretaker/__init__.py`
  (line 3), and as prose in `docs/limitations.md`. The JSON report gets it from
  `report.py` (`"version": run.caretaker_version`), which `runner.py` fills from
  `from . import __version__`; the runtime source is therefore
  `src/mcp_caretaker/__init__.py`. `mcp_types` IS imported directly from
  `src/` (`session.py:35`, `checks/robustness.py:18`), so the direct dependency
  on `mcp-types` stays.
- T0.3 SDK versions VERIFIED with `python -m pip index versions mcp` and the
  same command for `mcp-types`:

  | Package | Versions at or above 2.3.0 | Inside `>=2.3.0,<2.4` | At or above 2.4 |
  | --- | --- | --- | --- |
  | mcp | 2.3.0 | 2.3.0 only | none |
  | mcp-types | 2.3.0 | 2.3.0 only | none |

  The installed `mcp` 2.3.0 METADATA declares `Requires-Dist: mcp-types==2.3.0`.
  No newer release exists in the range, so no extra run was possible and no
  2.4-or-higher run could be made either. D3 does not apply.
- T0.4 README VERIFIED by reading it: it had no install section at all, and
  nine documentation references, all relative paths (`docs/report-format.md`,
  `docs/limitations.md`, `docs/gallery.md`, `docs/checks/README.md`,
  `examples/servers/README.md`, `docs/decisions/0005-canary-and-stability.md`,
  `docs/decisions/` as a directory, `docs/DEV-WINDOWS.md`,
  `docs/decisions/0004-robustness-foundation.md`).
- T0.5 Existing tests VERIFIED: `tests/test_cli.py` has
  `test_bare_invocations_print_usage_on_stderr_and_exit_2` covering `[]` and
  `["check"]` only (no unknown command); the date and banned-word test is
  `tests/test_docs.py::test_new_docs_have_no_dates_or_chained_shell_commands`
  and covers README, the fixtures README, the checks README, `docs/gallery.md`,
  `docs/limitations.md` and the 25 check pages; the gallery parser is
  `tests/test_gallery.py::_rows_and_problems` with `_expected` and `_split`;
  the installed-command helper is `tests/test_cli.py::_console_command`.
- T0.6 Build VERIFIED in a throwaway environment with `python -m build` on this
  tree: wheel with 22 files, sdist with a single top-level entry
  (`mcp_caretaker-0.0.0.dev0`, 144 entries), and METADATA lines `Name`,
  `Version`, `Summary`, `Project-URL` for Homepage and Repository, `Author`,
  `License: MIT`, `License-File: LICENSE`, `Requires-Python: >=3.11`,
  `Requires-Dist: mcp==2.3.0` and `mcp-types==2.3.0`. No build warning was
  printed.

## Quoted facts for the follow-up review

A1. `python -m pip index versions mcp` printed these lines verbatim. Each run
also printed one warning first, quoted here once because it is about the
command and not about either package:

```
WARNING: pip index is currently an experimental command. It may be removed/changed in a future release without prior warning.
```

The package lines from the first run:

```
mcp (2.3.0)
Available versions: 2.3.0, 2.2.0, 2.1.1, 2.1.0, 2.0.1, 2.0.0, 1.30.0, 1.29.1, 1.29.0, 1.28.1, 1.28.0, 1.27.2, 1.27.1, 1.27.0, 1.26.0, 1.25.0, 1.24.0, 1.23.3, 1.23.2, 1.23.1, 1.23.0, 1.22.0, 1.21.2, 1.21.1, 1.21.0, 1.20.0, 1.19.0, 1.18.0, 1.17.0, 1.16.0, 1.15.0, 1.14.1, 1.14.0, 1.13.1, 1.13.0, 1.12.4, 1.12.3, 1.12.2, 1.12.1, 1.12.0, 1.11.0, 1.10.1, 1.10.0, 1.9.4, 1.9.3, 1.9.2, 1.9.1, 1.9.0, 1.8.1, 1.8.0, 1.7.1, 1.7.0, 1.6.0, 1.5.0, 1.4.1, 1.4.0, 1.3.0, 1.2.1, 1.2.0, 1.1.3, 1.1.2, 1.1.1, 1.1.0, 1.0.0, 0.9.1
```

```
mcp-types (2.3.0)
Available versions: 2.3.0, 2.2.0, 2.1.1, 2.1.0, 2.0.1, 2.0.0
```

Every version at or above 2.3.0, and whether it is below 2.4:

| Package | Versions at or above 2.3.0 | Inside `>=2.3.0,<2.4` | Any version at 2.4 or higher |
| --- | --- | --- | --- |
| mcp | 2.3.0 | 2.3.0 | no, 2.3.0 is the newest release |
| mcp-types | 2.3.0 | 2.3.0 | no, 2.3.0 is the newest release |

Plainly: neither project has any release at 2.4 or higher, so there was no
newer release to run the suite against and no 2.4-or-higher environment could
be built. Both projects top out at 2.3.0, so the range `>=2.3.0,<2.4`
contains exactly one version of each.

A2. The installed `mcp` 2.3.0 distribution metadata, read with
`importlib.metadata` and filtered for `mcp-types`, prints exactly one matching
line:

```
Requires-Dist: mcp-types==2.3.0
```

That is the only `mcp-types` constraint in that metadata; the other 19
`Requires-Dist` lines name `anyio`, `httpx2`, `jsonschema`,
`opentelemetry-api`, `pydantic`, `pyjwt`, `python-multipart`, `pywin32`,
`sse-starlette`, `starlette`, `typing-extensions`, `typing-inspection`,
`uvicorn`, `python-dotenv`, `typer` and `rich`. Because `mcp` 2.3.0 pins
`mcp-types` to the exact same version, our range `mcp-types>=2.3.0,<2.4` can
only resolve to 2.3.0 while `mcp` stays at 2.3.0.

A3. `git grep -n "0[.]0[.]0[.]dev0" e9dc130` (the commit this PR branched from)
found every occurrence before this PR:

| File and line before this PR | Text | What this PR did |
| --- | --- | --- |
| `pyproject.toml:7` | `version = "0.0.0.dev0"` | removed the literal; `[project]` now has `dynamic = ["version"]` and `[tool.hatch.version] path = "src/mcp_caretaker/__init__.py"` reads it |
| `src/mcp_caretaker/__init__.py:3` | `__version__ = "0.0.0.dev0"` | kept, unchanged; this is now the only definition |
| `docs/limitations.md:117` | the sentence The version of this tool is a pre-release `0.0.0.dev0`. | prose rewritten to point at `--version` and at the file, so the literal is gone from that page |
| `tests/test_cli.py:456` | `caretaker_version="0.0.0.dev0",` | kept; an expected value inside a report fixture, not a definition |
| `tests/test_cli.py:481` | `caretaker_version="0.0.0.dev0",` | kept; same |
| `tests/test_model.py:104` | `caretaker_version="0.0.0.dev0",` | kept; same |

The two statements that looked contradictory are both true at different times.
"Two places" meant two files that *defined* the version: `pyproject.toml:7` and
`src/mcp_caretaker/__init__.py:3`. "There is no second copy" is the state after
this PR: no other file defines it, because the build reads the one line in
`__init__.py`. The string still appears in three test expectations and in two
documents that quote it (this file and `docs/RELEASING.md`, which shows the line
the owner edits), and none of those feeds the build. `docs/RELEASING.md` now
says "no other file defines it" rather than "no second copy" so the sentence
matches that reading.

A4. From the final head, `python -m build --outdir /tmp/a4 .` produced one wheel
and one sdist and printed no warning:

- wheel: 22 files, of which 5 are `mcp_caretaker-0.0.0.dev0.dist-info/METADATA`,
  `RECORD`, `WHEEL`, `entry_points.txt` and `licenses/LICENSE`, and 17 are
  package modules under `mcp_caretaker/`.
- sdist: 146 members with a single top-level entry,
  `mcp_caretaker-0.0.0.dev0/`.
- METADATA lines, verbatim:

```
Name: mcp-caretaker
Version: 0.0.0.dev0
Project-URL: Homepage, https://github.com/sarooo43/mcp-caretaker
Project-URL: Source, https://github.com/sarooo43/mcp-caretaker
Project-URL: Issues, https://github.com/sarooo43/mcp-caretaker/issues
License-Expression: MIT
License-File: LICENSE
Requires-Python: >=3.11
Requires-Dist: mcp-types<2.4,>=2.3.0
Requires-Dist: mcp<2.4,>=2.3.0
Requires-Dist: psutil>=7.2.2; extra == 'dev'
Requires-Dist: pytest-timeout>=2.4.0; extra == 'dev'
Requires-Dist: pytest>=9.2.0; extra == 'dev'
Requires-Dist: ruff>=0.17.6; extra == 'dev'
```

A5. The `-V` short flag was reviewed and does not exist. `cli.main` compares
`args == ["--version"]` and nothing else, no test or document names `-V` for
this tool, and `python -m mcp_caretaker -V` prints the usage line to stderr and
exits 2, exactly like any other unrecognised first argument:

```
usage: mcp-caretaker check --trust [options] -- PROGRAM [ARGS...]
```

## Decisions as built

- D1 `--version` is handled in `cli.main` before the `check` dispatch:
  `args == ["--version"]` prints `mcp-caretaker {__version__}` to stdout and
  returns 0, with nothing on stderr. The version comes from
  `src/mcp_caretaker/__init__.py`, the same value the JSON report carries.
  `pyproject.toml` now declares `dynamic = ["version"]` with
  `[tool.hatch.version] path = "src/mcp_caretaker/__init__.py"`, so the release
  edit is one file, one line.
- D2 Dependencies are `mcp>=2.3.0,<2.4` and `mcp-types>=2.3.0,<2.4`. This
  supersedes the exact pin recorded in `docs/decisions/0001-sdk-and-protocol.md:120`;
  that record is left as history and is not edited.
- D3 Not applied: T0.3 found no release greater than 2.3.0 and below 2.4, so an
  `sdk-lowest` job would install the same version as the existing jobs and
  prove nothing. The existing test jobs resolve to the newest release in range,
  which is 2.3.0.
- D4 The `package` job runs on ubuntu-latest and windows-latest with Python 3.11
  and 3.13, with `permissions: contents: read` and checkout
  `persist-credentials: false`. It installs `build` and `twine` inside the job
  only, builds, runs `twine check`, creates a venv in `$RUNNER_TEMP` (outside
  the checkout), installs the wheel there, runs `pip check` and `pip list`,
  compares `--version` with the installed distribution metadata, and runs one
  real clean-server check from a directory that is not the checkout.
- D5 No publishing. `docs/RELEASING.md` holds the owner's steps and says the
  owner runs them and that tokens never go into the repository or a chat.
- D6 All four carry-overs are in: the page-vs-gallery test, the unknown-command
  exit code, banned words across `docs/decisions/*.md` and
  `docs/RELEASING.md`, and the three re-checked sentences.
- D7 `workflow_dispatch` is kept, and the six identical CT-ROB `Limits`
  paragraphs are unchanged.
- D8 The README install section uses a local clone (`pip install .` and
  `pipx install .`) and says the package is not published yet.
  `docs/RELEASING.md` lists the exact lines to change after publishing.
- D9 Every README link is now an absolute
  `https://github.com/sarooo43/mcp-caretaker/blob/main/<path>` URL, and
  `tests/test_links.py` maps that prefix back to the local file and checks it
  exists. The test still makes no network call.
- D10 Classifiers are the six listed in `pyproject.toml`
  (`Development Status :: 2 - Pre-Alpha`, `Environment :: Console`,
  `Programming Language :: Python :: 3`, `3.11`, `3.13`,
  `Topic :: Software Development :: Testing`). All six were checked against
  `trove-classifiers` 2026.9.21.13 in a throwaway environment: six VALID, zero
  INVALID. The package is not added to the repository.
- D11 Author is a name only; URLs are Homepage and Source (the repository) and
  Issues (the repository plus `/issues`).

## Sentence re-checks

- `docs/report-format.md` said `CT-CANARY-003` is "the only result whose summary
  is built from more than one session". `CT-STAB-001` builds its summary by
  comparing two sessions (`checks/stability.py:compare_lists`), so the sentence
  was false. It now says `CT-CANARY-003` is the only result whose summary
  counts sessions, and that `CT-STAB-001` compares two sessions but counts
  tools.
- `docs/checks/CT-START-001.md` says stderr text is quoted as evidence only.
  Supported: `checks/startup.py:56` adds `Evidence("stderr_tail",
  error.stderr_tail)`, and `model.finalize_result` redacts, escapes and caps
  every evidence detail. The sentence is unchanged.
- `docs/checks/CT-START-005.md` said local Windows verification is limited to
  CI. It now says cleanup uses POSIX process groups on POSIX and the SDK's
  Windows helpers on Windows, and that the Windows path is exercised by the
  test suite in the Windows CI jobs. Supported by `session.py` (the
  `windows_helpers()` branch and the `os.killpg` branch), the Windows matrix in
  `.github/workflows/ci.yml`, and the session tests that run there.

## Local mutation proofs

Each mutation was applied to the working tree, the named test was run with the
project environment, the file was restored, and the test was run again. The
`git diff` output was compared byte for byte before and after; it was identical
each time. Ruff was run on the mutated Python files and was clean, so lint could
not mask pytest.

| ID | Change | Named test | Red evidence | After restore |
| --- | --- | --- | --- | --- |
| M1 | `cli.py`: version line names the tool `mcp-caretakerX` | `test_version_flag_on_module_invocation` | `1 failed`, diff shows `- mcp-caretaker` versus `+ mcp-caretakerX` | `1 passed`; ruff clean |
| M2 | `cli.py`: version line prints `{__version__}.9` instead of the real version | `test_version_matches_json_report` | `1 failed`, `assert '9.9.9' == '0.0.0.dev0'`-style mismatch between the printed line and the report | `1 passed`; ruff clean |
| M3a | `cli.py`: bare invocation returns 0 | `test_bare_and_unknown_invocations_print_usage_on_stderr_and_exit_2` | `1 failed`, `assert 0 == 2` | `1 passed`; ruff clean |
| M3b | `cli.py`: unknown command returns 0 | same test | `1 failed`, `assert 0 == 2` | `1 passed`; ruff clean |
| M4 | `docs/checks/CT-START-001.md`: removed `--startup-timeout 2` from the reproduce command | `test_every_page_reproduce_command_matches_a_gallery_row` | `1 failed`, `assert ["CT-START-001.md: 0 gallery rows match ..."] == []` | `1 passed` |
| M5 | `docs/decisions/0007-honesty-docs-and-gallery.md`: inserted one of the five banned words from the test's list | `test_decisions_and_releasing_avoid_banned_words` | `1 failed`, `AssertionError: 0007-honesty-docs-and-gallery.md contains <word>` | `1 passed` |
| M6 | `README.md`: absolute link path changed to a file that does not exist | `test_relative_markdown_links_point_to_existing_files` | `1 failed`, `README.md -> .../docs/limits-missing.md` | `1 passed` |

M7 is the Windows proof of the console-script wiring: a throwaway branch whose
single commit changes only the `[project.scripts]` target to
`mcp_caretaker.cli:does_not_exist`, started with `workflow_dispatch`. Its
results live in the PR report, not in this file, because the branch is deleted
after the run.

## What is not verified here

- No release was published, so nothing on PyPI, TestPyPI or a tag exists.
- The lowest-version CI job does not exist because no second version exists.
- The PyPI yank and delete buttons in the web interface are NOT VERIFIED.
