# Case study: three reference servers

One run per server, against three reference servers from the
[modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
repository. The saved reports in `docs/case-study/` are the source of every
number on this page, and they are committed exactly as the tool wrote them.

## What this is and is not

- mcp-caretaker is **pre-release**: check IDs, wording and thresholds can change
  between versions, and the version used here is `0.0.0.dev0`.
- Every threshold in this tool is a **guess**. The check pages and
  [docs/limitations.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/limitations.md)
  say so next to each number.
- A **warning is not a defect claim**. It records that one observed answer
  differed from what the tool expected, and the tool states which value it sent.
- A **pass is not a safety guarantee**. A run with 25 `pass` results means the 25
  rules matched in one short session; it says nothing about behaviour the tool
  never looks at.
- The tool is **not a sandbox**. Starting a server runs its code on this machine.
- The maintainers of these servers were notified through
  [modelcontextprotocol/servers issue 5660](https://github.com/modelcontextprotocol/servers/issues/5660)
  before this page was published, and no reply asked for a change or a removal.
- It ran on **one machine type (Linux)**, once per server. Windows was not part
  of this run.

## The servers

| Package | Version | License | Reach |
| --- | --- | --- | --- |
| [mcp-server-time](https://github.com/modelcontextprotocol/servers/tree/main/src/time) | 2026.11.18 | MIT | local |
| [mcp-server-git](https://github.com/modelcontextprotocol/servers/tree/main/src/git) | 2026.11.18 | MIT | local |
| [mcp-server-fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | 2026.11.11 | MIT | network-capable |

Package name, version, license and reach come from the installed package
metadata. The `Summary` field of each package is the source of the last column:
`tools for time queries and timezone conversions`, `tools to read, search, and
manipulate Git repositories`, and `tools to fetch and convert web content`.

## How it was run

The caretaker checkout was at commit `30b5bbb98230589529e9d35d28de2fb73214a9c1`
of `main`, installed with `pip install .` into its own virtual environment.

| Item | Value |
| --- | --- |
| Python | 3.11.2 |
| mcp | 2.3.0 |
| mcp-types | 2.3.0 |
| mcp-caretaker | 0.0.0.dev0 |

Each server was installed in a separate virtual environment under `/tmp`, so its
own `mcp` version could not clash with the caretaker's. Run one command per line:

```sh
python -m venv /tmp/ct8b/venv-time
/tmp/ct8b/venv-time/bin/pip install mcp-server-time==2026.11.18
python -m venv /tmp/ct8b/venv-git
/tmp/ct8b/venv-git/bin/pip install mcp-server-git==2026.11.18
python -m venv /tmp/ct8b/venv-fetch
/tmp/ct8b/venv-fetch/bin/pip install mcp-server-fetch==2026.11.11
```

The git server was confined to a throwaway repository outside this checkout,
which held one empty commit and no remote:

```sh
git init
git -c user.name=case-study -c user.email=case-study@example.invalid commit --allow-empty -m initial
```

The path `/tmp/ct8b/repo` in the saved reports is that throwaway folder, created
for this run; it is not a path inside this repository, and it does not exist on
the machine of anyone who reproduces the run.

The three runs, from the root of this checkout:

```sh
/tmp/ct8b/venv-caretaker/bin/mcp-caretaker check --trust --json docs/case-study/time.json --markdown docs/case-study/time.md -- /tmp/ct8b/venv-time/bin/mcp-server-time
/tmp/ct8b/venv-caretaker/bin/mcp-caretaker check --trust --json docs/case-study/git.json --markdown docs/case-study/git.md -- /tmp/ct8b/venv-git/bin/mcp-server-git -r /tmp/ct8b/repo
/tmp/ct8b/venv-caretaker/bin/mcp-caretaker check --trust --json docs/case-study/fetch.json --markdown docs/case-study/fetch.md -- /tmp/ct8b/venv-fetch/bin/mcp-server-fetch
```

`mcp-server-git --help` documents `-r, --repository PATH` as the option that
confines operations to one repository, so the run used it. `mcp-server-time
--help` and `mcp-server-fetch --help` need no argument for a stdio run, so
neither was given one.

On Windows a virtual environment puts its executables in `Scripts` instead of
`bin`, so the two paths above would differ. **Not run**: Windows was not part of
this run.

## Results at a glance

| Package | Version | Counts | Exit code |
| --- | --- | --- | --- |
| mcp-server-time | 2026.11.18 | pass=21 warn=1 fail=0 not_tested=3 | 0 |
| mcp-server-git | 2026.11.18 | pass=23 warn=2 fail=0 not_tested=0 | 0 |
| mcp-server-fetch | 2026.11.11 | pass=22 warn=0 fail=0 not_tested=3 | 0 |

`not_tested` never changes the exit code; the exit code is `1` only when a `fail`
result exists, and no run produced one.

## Observation about a server

`mcp-server-git` produced `CT-DESC-006` as a `warn`. Its summary reads
`21 top-level properties have no description.` The report lists 20 of them by
name, for example `git_status properties[repo_path]`, `git_commit
properties[message]` and `git_checkout properties[branch_name]`, and its 21st
evidence entry reads `1 more not shown`, so one further property is behind the
evidence cap. These are the properties the tool could see in the tool listing of
one session. The saved report holds the full list.

## What this run could not test

Each item is a limit of this tool, not a statement about the server.

| Server | Check | Limit |
| --- | --- | --- |
| time | CT-ROB-001 | `not_tested`: `get_current_time` and `get_time_ago` have no required property, so no wrong-type probe could be built. Reason: `no required property was available for wrong-type input`. |
| time | CT-ROB-002 | `not_tested` for the same two tools, reason `no required property was available for missing-required input`. |
| time | CT-ROB-005 | `warn`: the placeholder `A` was rejected by `convert_time` with `Invalid time format. Expected HH:MM [24-hour format]`. Rejecting a value that does not fit a format the schema does not state is correct behaviour. |
| time | CT-CANARY-001 | `not_tested` as a consequence of the two `not_tested` robustness checks. |
| git | CT-ROB-005 | `warn`: `6 tested, 2 skipped`, and all 6 answers differed because every probe sent the placeholder `A` as `repo_path`, which the server rejected. The tool has no way to invent a real repository path, so this is a probe limit. |
| git | CT-ROB-005 | 2 of the read-only tools were skipped with `valid input could not be generated for this tool` (`git_log` and `git_branch`). |
| fetch | CT-ROB-004 | `not_tested`: `valid input could not be generated for a huge string`. |
| fetch | CT-ROB-005 | `not_tested`: `valid input could not be generated for this tool` for `fetch`, whose `url` property the tool will not invent a value for. This page makes no claim about network activity. |
| fetch | CT-CANARY-001 | `not_tested` as a consequence of the two `not_tested` robustness checks. |

## What was not run or measured

- Tools with side effects were never given valid input: the tool only calls tools
  that declare the read-only hint, and it builds its own arguments.
- No load, timing, memory or concurrency measurement was made. Each server was
  started once, for one session.
- Stability was checked across a second session inside one run
  (`CT-STAB-001`, `CT-STAB-002`); nothing was repeated across runs or machines.
- Network activity was not measured. The report lists CT-ROB-004 and CT-ROB-005 as
  `not_tested` for the fetch server because valid input could not be generated for
  its tool. This page makes no claim about network activity.

## How to read a result

- `pass`: the observed behaviour matched the rule for that check.
- `warn`: something differed from what the tool expects; it prints the value it
  sent and the answer it got, and it does not conclude that the server is wrong.
- `fail`: a rule that the tool treats as a failure was broken.
- `not_tested`: the tool could not build the input this check needs, so the check
  made no observation. It is never counted as a pass.

The full definitions and every known limit are in
[docs/limitations.md](https://github.com/sarooo43/mcp-caretaker/blob/main/docs/limitations.md).

## Reproduce it

Use the commands in [How it was run](#how-it-was-run), with your own `/tmp` paths
and your own throwaway repository, and compare your `Totals:` line with the
counts above. The evidence text can differ between runs because the time server
reports its own clock. This page does not claim that totals are identical on
every run.
