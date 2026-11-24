# 0005 - Canary and stability verification

This decision file records the PR 4 checks before product code was written. Only this repository and the installed official `mcp` SDK were read. No other repository, scanner source, product-code network call, paid service, account, runtime dependency, CLI command, report file, or generated output file is used. Fake values used by the small checks are not recorded here. Findings are facts, not verdicts of intent. Every finding uses `Evidence(subject, detail, replay)`. The launcher stays stripped and `confirmed=True` remains mandatory.

## Stop conditions and scope

- S1 was not hit: PR 3 is in `origin/main`, its CI results were readable, and a push dry run succeeded.
- S2 is not hit: the work uses the existing free development tools, one throwaway free-tool environment, and GitHub Actions with `permissions: contents: read` and `persist-credentials: false`.
- S3 is not hit: a real child process received a value supplied through `extra_env`; `build_child_env` adds `extra_env` last after the small allow-list. No allow-list widening is needed.
- The PR 4 registry grows from 20 to 25 checks in this order: START, DESC, ROB, CANARY, STAB. No dependency pin changes, version tags, changelog, limitation page, front end, Docker, HTTP, OAuth, LLM, side-effect watching, decoy file, scanner source, or output artifact is added.
- `NOT VERIFIED`: Windows runtime cleanup was not available locally. The Windows retry branch was checked in source and with a simulated late-handle retry on Linux; Windows CI is the runtime proof.

## T0 a. Extra env, temp folder ownership, Windows cleanup

What was checked: `build_child_env` starts from an empty child environment and a small allow-list, adds `extra_env` last, and does not inherit a parent test marker. `LaunchSpec` redacts `extra_env` values. `ServerSession` currently creates a `mcp-caretaker-` temp area containing `cwd/` and `stderr.log`, runs the child in `cwd/`, caches a redacted stderr tail, and deletes the folder at close. `run_checks` did not own that folder. The Windows branch retries `shutil.rmtree` for five seconds.

How: `build_child_env` and `LaunchSpec` were read. A real `probe_server.py` subprocess received a fake value through `extra_env`; the child reported environment names, its cwd, and stderr. The parent marker was absent, the child name was present, the cwd matched `session.workdir`, the cwd started empty, and the temp area and stderr file were removed after close. A temporary directory was used with a simulated Windows platform and a first `rmtree` failure; the retry removed it. The local host was Linux.

Decision: plant all three names through `extra_env`; do not widen the allow-list. D12 changes temp-area ownership so `run_checks` owns one folder for both sessions and removes it at the end, including when a session raises. The Windows retry helper is reused by `run_checks` cleanup.

## T0 b. Stderr path and readability after close

What was checked: `stderr.log` exists while the session is open and raw bytes can be read from it. The `session.stderr_text` property redacts `extra_env` values and keeps only a 64 KiB tail. After the default session close, the file is gone but the cached redacted tail remains readable.

How: a real `probe_server.py` subprocess wrote a fake value to stderr. The file existed and was byte-readable during the session; after close it did not exist, while the cached tail remained readable and redacted. The `STDERR_CAP` constant was read.

Decision: PR 4 needs a raw prefix reader for the canary scan. With the shared run-owned folder, scan stderr after the session closes when the file remains readable, including shutdown output. If the file is not readable after close, use the raw prefix captured before shutdown; if neither raw read is available, use the cached redacted tail and document that exact-value detection can be incomplete. CT-CANARY-003 documents the fallback and the cap.

## T0 c. Stdout noise tap

What was checked: `_BridgeTap.inspect_line` sees every non-blank stdout line, increments the count for all noise lines, and retains only the first five lines with each line cut to 200 characters. The retained strings are raw bridge text; final result redaction is applied later by `finalize_run_result`. The tap had no observer hook.

How: `_BridgeTap` was read and exercised with 25 long noise lines; the count was 25 while only five capped strings were retained. A real `leaky_stdout.py` subprocess emitted two noise lines; the session reported two counted lines and two stored capped lines.

Decision: add a small observer hook called with each full stray stdout line before truncation. CT-CANARY-003 scans those full lines. Evidence is redacted first, then escaped and capped. `CT-START-004` keeps its existing bounded display.

## T0 d. Raw tools pages and CT-ROB-006 final liveness

What was checked: `_BridgeTap.raw_tools_pages` appends every tracked raw `tools/list` result and does not consume them. `collect_tools_pages()` slices new pages from that list. `robustness._liveness()` calls `session.list_tools()` and discards the SDK result, so the final liveness raw page is reachable from the tap without a new `tools/list` request.

How: `session.py` and `robustness.py` were read. A real `paginated_server.py` subprocess returned two pages through `collect_tools_pages()`; the tap held two pages. A following `session.list_tools()` added exactly one more raw page whose `tools` key was a list. The `_liveness` source was checked for the call and the discarded return value.

Decision: `run_robustness_checks` returns the final successful liveness page slice with its results. CT-STAB-002 compares that page with the first listing and does not call `tools/list` again. If no final page is available, CT-STAB-002 is `not_tested`.

## T0 e. Installed MCPError and CallToolResult shapes

What was checked: `MCPError` exposes `code`, `message`, and `data`, and `exc.error` exposes the same fields. `CallToolResult.model_dump_json(by_alias=True, exclude_unset=True)` emits `content`, `structuredContent`, and `isError` when set. `InitializeResult` has top-level `instructions`; an extra `instructions` field inside raw `serverInfo` is dropped by the pinned SDK object.

How: installed SDK classes were inspected directly. A temporary raw stdio server, outside the repository, returned one tool result with `structuredContent` and one call-level JSON-RPC error with `data`. A real `ServerSession` received both. The SDK result dump keys and the raised `MCPError` fields were checked. The same handshake included top-level `instructions` and nested `serverInfo.instructions`; only the top-level field survived on the SDK object.

Decision: CT-CANARY-001 serializes a full `CallToolResult` dump and a `MCPError` payload containing code, message, and data before scanning. CT-CANARY-002 scans the raw first-connection `initialize` result from the bridge tap, selecting `serverInfo` name, version, and instructions plus top-level `instructions`, so raw text is not lost through SDK object conversion.

## T0 f. `_raw_tools.py` capabilities and gaps

What was checked: the helper can emit raw `tools/list` pages, `initialize` with `serverInfo` name and version, `tools/call` results through `on_call`, `isError` results, method-level JSON-RPC errors, stdout noise, an exit after list, and a process-id file. It has no `instructions` option, no JSON-RPC error `data`, no call-level error marker, no stderr control, and no shared-folder state for reconnect or after-call changes.

How: `examples/servers/_raw_tools.py` was read and compared with the temporary raw probe. Its `serve` parameters and `send`, `result`, `error`, `tool_result`, and `clean_tool` helpers were enumerated. The standard library base64 helper was checked to produce one distinct standard encoding of an ASCII value.

Decision: extend this fixture helper only for PR 4 needs: `instructions`, optional JSON-RPC error `data`, a typed call-level error marker, and stderr output. PR 4 fixtures keep their state in the shared working folder. No other encoding is generated by product code.

## T1 evidence audit

`docs/decisions/0004-pr2-audit.md` existed and was not created or changed. It references no `docs/decisions/0004-evidence/` filename. `docs/decisions/0004-robustness-foundation.md` references the kept files below. The audit lists every file that was present before deletion, says whether a decision document references it, and records the action.

| File | Decision-doc reference | Action | Reason |
| --- | --- | --- | --- |
| `official_tools_page.out.txt` | `0004-robustness-foundation.md` | kept | referenced for official Tools-page facts. |
| `pr3-mutation-proof.out.txt` | none | deleted | no decision document referenced it; T1 deletes unreferenced helper outputs; PR 3 mutation facts are recorded in this decision file and the final report instead of a new output file. |
| `raw_probe_server.py` | `0004-robustness-foundation.md` | kept | referenced for raw error and child-exit checks. |
| `sdk_dispatcher.out.txt` | `0004-robustness-foundation.md` | kept | referenced for installed SDK dispatcher facts. |
| `sdk_dispatcher.py` | `0004-robustness-foundation.md` | kept | referenced as the dispatcher evidence script. |
| `sdk_pinned.out.txt` | `0004-robustness-foundation.md` | kept | referenced for exact SDK pin facts. |
| `sdk_pinned.py` | `0004-robustness-foundation.md` | kept | referenced as the SDK pin evidence script. |
| `sdk_probe_behaviour.out.txt` | `0004-robustness-foundation.md` | kept | referenced for SDK behaviour and raw tool shape. |
| `sdk_probe_behaviour.py` | `0004-robustness-foundation.md` | kept | referenced as the SDK behaviour evidence script. |
| `sdk_probe_server.py` | `0004-robustness-foundation.md` | kept | referenced as the dedicated SDK probe server. |
| `timeout_and_exit.out.txt` | `0004-robustness-foundation.md` | kept | referenced for timeout, late answer, and shutdown facts. |
| `timeout_and_exit.py` | `0004-robustness-foundation.md` | kept | referenced as the timeout evidence script. |
| `workspace_main.out.txt` | `0004-robustness-foundation.md` | kept | referenced for workspace and merged PR 2 facts. |
| `workspace_main.py` | `0004-robustness-foundation.md` | kept | referenced as the workspace evidence script. |

Kept list: `official_tools_page.out.txt`, `raw_probe_server.py`, `sdk_dispatcher.out.txt`, `sdk_dispatcher.py`, `sdk_pinned.out.txt`, `sdk_pinned.py`, `sdk_probe_behaviour.out.txt`, `sdk_probe_behaviour.py`, `sdk_probe_server.py`, `timeout_and_exit.out.txt`, `timeout_and_exit.py`, `workspace_main.out.txt`, `workspace_main.py`. Deleted list: `pr3-mutation-proof.out.txt`. No new evidence script or output file was added.

## Decisions D1 through D12

- D1: `run_checks` calls `canary.make_canary()` through the module attribute on every call. It plants `CARETAKER_CANARY_API_KEY`, `CARETAKER_CANARY_TOKEN`, and `CARETAKER_CANARY_SECRET` with one fresh `"ct_canary_" + secrets.token_hex(16)` value each. The values are added through `extra_env` and override any caller values with the same names. Both sessions in one `run_checks` call receive the same three values. `LaunchSpec` redaction and the stripped launcher are unchanged.
- D2: CT-CANARY-001 observes every `tools/call` answer when received, including PR 3 probes, unknown-tool answers, final valid calls, `isError` results, and `MCPError` payloads. It scans the whole result JSON text and the error code, message, and data. The tracker keeps only the answer count, findings, and bytes or lines scanned; it does not retain all answers.
- D3: CT-CANARY-002 scans all raw first-connection `tools/list` pages and the raw `initialize` `serverInfo` name, version, and instructions plus top-level `instructions`. CT-CANARY-003 scans stderr from the start of each session up to `STDERR_SCAN_MAX_BYTES` and every stray stdout line before display truncation.
- D4: CT-CANARY-001 is `FAIL` for any finding, `PASS` when at least one answer was scanned with no finding, and `not_tested` for zero answers, an earlier-stage `tools/list` failure, or robustness checks that did not complete. CT-CANARY-002 is `FAIL` for any finding, `PASS` otherwise, and `not_tested` when handshake data or `tools/list` failed. CT-CANARY-003 is `WARN` for any finding and `PASS` otherwise. Startup failure leaves all other checks `not_tested`. The zero-tools case is `not_tested` for CT-CANARY-001 because robustness coverage did not complete, even though the unknown-tool answer is still scanned.
- D5: each finding has `subject` set to where it was found and `detail` set to the variable name, `exact` or `base64` encoding, and a redacted output excerpt. Redaction applies to the full text first with canary values, their standard base64 forms, and values following `--env`; escaping and the `EVIDENCE_MAX_CHARS` cap follow. Findings never include a canary value or its base64 form. CT-CANARY-001 replay uses the PR 3 `replay_line`; CT-CANARY-002 and stability findings use one constructed `tools/list` line; CT-CANARY-003 uses `None`.
- D6: `STDERR_SCAN_MAX_BYTES = 1_048_576` is added to `thresholds.py` with the same guessed-number comment style and is documented as a guess. A larger stderr with no finding in the scanned prefix yields `PASS`; the summary states the exact scanned byte count and cap use.
- D7: first-session stderr is read after the first session closes when the shared folder keeps the file readable, so shutdown output is included. If it is not readable after close, the raw prefix captured before shutdown is used. The fallback is documented in the CT-CANARY-003 page. Second-session stdout lines are observed through the same pre-truncation hook; second-session stderr is scanned by the same prefix rule.
- D8: CT-STAB-001 starts only after the first session fully closed and only when the first session reached `tools/list`. It opens a second session with the same `LaunchSpec` and the same run-owned folder, completes a handshake and full `tools/list`, and compares that list with the first list. A second start or list failure is `not_tested` with a reason and exact redacted error evidence.
- D9: stability compares `title`, `description`, `inputSchema`, `outputSchema`, and `annotations` as canonical JSON with sorted keys. Tools are matched by name and order is ignored. Top-level `_meta` and `icons` are ignored. A changed common-tool field is `FAIL`; only added or removed tools are `WARN`; no change is `PASS`. A changed field wins over added or removed tools.
- D10: each stability change has `subject` set to the tool name, `detail` with field before and after values capped and redacted, and a constructed `tools/list` replay line. Added and removed tools use the same subject, detail, and replay shape.
- D11: CT-STAB-002 compares the first listing with the CT-ROB-006 final liveness list and sends no new request. It is `not_tested` when that list is unavailable. Changes by time, by more calls, or by specific arguments are not caught; only the sampled lists are compared.
- D12: `run_checks` owns one folder for both sessions and removes it at the end, including when a session raises. `ServerSession` accepts a caller-owned folder without deleting it; standalone sessions still create and delete their own folder so PR 1 cleanup tests stay green. If the shared folder cannot be kept reliably, a fresh second folder is used and recorded as a deviation in the final report and `docs/checks/CT-STAB-001.md`.

## Documentation and honest limits

- The README keeps the PR 3 warning and adds a canary and stability section. It names the three planted variables and describes findings as facts, not verdicts of intent.
- Each new check page has `What it checks`, `Why it matters`, `How it is decided`, `How to reproduce`, `Verdict`, `How to fix`, and `Limits`. The reproduction text says: set an env variable named `CARETAKER_CANARY_TOKEN` to any value, start the server, and send the replay line. One shell command is shown per line.
- Honest limits: only three names are planted; a deliberate show-environment tool is flagged and v0.1 has no suppression; only the value encoded on its own with standard base64 is detected; changes by time, by more calls, or by specific arguments are not caught; stderr is capped; exact values and their base64 forms are never written to results, evidence, messages, logs, or files.
- `vulture` is installed only in a throwaway environment and is not added to `pyproject.toml`, development dependencies, or CI. Its behaviour was VERIFIED by one throwaway run in T7.

## T7 unused-code review

Exact commands, one per line:

```sh
.venv/bin/ruff check
.venv/bin/ruff format --check
python3 -m venv /tmp/pr4-vulture-venv
/tmp/pr4-vulture-venv/bin/python -m pip install -q --disable-pip-version-check vulture
/tmp/pr4-vulture-venv/bin/vulture src tests examples
grep -RInE "TODO|FIXME|NotImplemented" src tests examples docs README.md pyproject.toml .github
```

`ruff check` printed `All checks passed!`; `ruff format --check` printed `99 files already formatted`. The grep printed no matches. One throwaway `vulture src tests examples` invocation exited with code 3 and printed exactly nine items:

1. `examples/servers/good_server.py:30: unused function 'save_note' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
2. `examples/servers/probe_server.py:23: unused function 'env_names' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
3. `examples/servers/probe_server.py:41: unused function 'shout_env' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
4. `examples/servers/spawns_grandchild.py:36: unused function 'ping' (60% confidence)` — false positive; the official SDK decorator registers it and tests call it through MCP.
5. `src/mcp_caretaker/session.py:323: unused property 'child_pid' (60% confidence)` — real dead code; the property was removed after no source, test, or documentation reference was found.
6. `src/mcp_caretaker/session.py:585: unused variable 'exc_type' (100% confidence)` — false positive; `__aexit__` requires this parameter.
7. `src/mcp_caretaker/session.py:587: unused variable 'tb' (100% confidence)` — false positive; `__aexit__` requires this parameter.
8. `tests/conftest.py:8: unused function 'anyio_backend' (60% confidence)` — false positive; pytest discovers this fixture.
9. `tests/test_canary_runner.py:27: unused function 'fixed_canary' (60% confidence)` — false positive; pytest discovers this autouse fixture.

Reused helpers: `redact_values`, `visible_text`, `finalize_run_result`, `replay_line`, `_error_text`, `remove_temp_area`, `collect_tools_pages`, `_BridgeTap.inspect_line`, `clean_tool`, `tool_result`, `serve`, `tools_list_replay`, `error_evidence`, and `compare_lists`. No new runtime dependency, development dependency, CI step, helper script, or output file was added for the unused-code review.

## T8 mutation proof

Local mutations were applied one at a time to committed files. Each ran the named pytest node or nodes, saw a red result, restored the exact original text, saw a green result, and left `git diff --quiet` empty. No mutation helper script or output file was stored in the repository.

| ID | Changed file and mutation | Named pytest node or nodes | Red | Restored | Diff empty |
| --- | --- | --- | --- | --- | --- |
| M1 | `runner.py`: no planted environment values | `test_bad_canary_leaks_modes[result-text-fails-canary-001]` | `1 failed in 0.63s` | `1 passed in 0.68s` | YES |
| M2 | `canary.py`: skip standard base64 form | `test_bad_canary_leaks_modes[base64-result-fails-canary-001]` | `1 failed in 0.67s` | `1 passed in 0.67s` | YES |
| M3 | `canary.py`: CANARY-001 ignores `MCPError` | `test_bad_canary_leaks_modes[rpc-error-fails-canary-001]` | `1 failed in 1.30s` | `1 passed in 1.27s` | YES |
| M4 | `canary.py`: CANARY-003 uses `FAIL` instead of `WARN` | `test_bad_canary_leaks_modes[stderr-warns-canary-003]` | `1 failed in 0.81s` | `1 passed in 0.72s` | YES |
| M5 | `runner.py`: second session uses a fresh temp folder | `test_bad_rug_pull_modes[reconnect-description-fails-stab-001]` | `1 failed in 0.72s` | `1 passed in 0.79s` | YES |
| M6 | `stability.py`: ignore annotations | `test_bad_rug_pull_modes[after-calls-annotation-fails-stab-002]` | `1 failed in 0.70s` | `1 passed in 0.71s` | YES |
| M7 | `canary.py`: leak evidence skips redaction | `test_bad_canary_leaks_modes[result-text-fails-canary-001]` | `1 failed in 0.65s` | `1 passed in 0.67s` | YES |
| M8 | `stability.py`: added or removed tools count as PASS | `added-tool-warns-stab-002`, `removed-tool-warns-stab-002` | `2 failed in 0.82s` | `2 passed in 0.80s` | YES |

M5 remote proof used the throwaway branch `mutation/pr4-m5-windows`, mutation commit `af7f36eefb7ea3cb4a2eae993366e31ead9523c9`, parent commit `1bd6fda7ddcb25afd8a3e2646a862e3fec263994`, and `workflow_dispatch` run `https://github.com/sarooo43/mcp-caretaker/actions/runs/45510363563`. The run conclusion was `failure`. Per-job results were: ubuntu 3.11 job `138856236610` `failure`; windows 3.11 job `138856236863` `failure`; windows 3.13 job `138856237091` `failure`; ubuntu 3.13 job `138856237264` `failure`. The Windows 3.11 signed log showed `2 failed, 129 passed in 52.37s`, including CT-STAB-001 returning PASS when fresh folders hid the reconnect change. The branch was deleted and no pull request was opened from it.

The mutation commit differs from the final head in `docs/decisions/0005-canary-and-stability.md` and `src/mcp_caretaker/runner.py`. The final head includes this proof text and the restored shared-folder code; the mutation commit contains the fresh-folder code and lacks the appended proof text. No canary value, base64 form, helper script, or output file was stored for the mutation proof.
