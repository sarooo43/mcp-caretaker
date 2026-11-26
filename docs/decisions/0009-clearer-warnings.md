# 0009 - Clearer warnings and documented limits

PR 8a changes three texts and adds documentation. It changes no verdict, no
probe selection, no threshold and no check ID, and it adds no dependency, option
or version bump. The private dry run that motivated it found 0 failing results on
three official servers and four problems in our own reporting: a warn count that
included a success, a warn sentence that read like a server defect, a `not_tested`
reason that did not say why, and a refused-key rule that no page described.

## T0 findings (before any change)

- Base VERIFIED: the checkout's local base was a one-file stub commit, so the
  branch base was aligned to `origin/main` (`938fd2a`, "Merge pull request #7")
  with a mixed reset before any edit. `git status --short` was then empty, and
  `pytest --collect-only -q` reported `205 tests collected`.
- D1 code VERIFIED at `src/mcp_caretaker/checks/robustness.py:513` — the warn
  count was one fixed tuple for every check:

  ```python
  warn_count = sum(
      item in ("success", "error_result", "jsonrpc_error", "no_answer")
      for item in outcomes
  )
  ```

  and the sentence at `robustness.py:523` was
  `text = f"{warn_count} answers differed from the expected answer."`. The
  verdict rules that produce a warn are per check: `CT-ROB-001`, `CT-ROB-002` and
  `CT-ROB-003` warn on `success` (`robustness.py:478-484`), `CT-ROB-004` warns on
  `no_answer` (`robustness.py:486-492`), `CT-ROB-005` warns on `error_result`,
  `jsonrpc_error` or `no_answer` (`robustness.py:493-502`). The constant
  `FAILING_OUTCOMES` (`robustness.py:66-74`) already lists exactly those
  unexpected outcomes per check, and was already used at `robustness.py:271` to
  decide whether a probe gets a replay line.
- D3 code VERIFIED: `src/mcp_caretaker/runner.py:242` set
  `earlier_failure_reason = "robustness checks did not complete"` whenever any of
  the six robustness results was `fail` or `not_tested`, and
  `src/mcp_caretaker/canary.py:269-286` turned that string into the
  `CT-CANARY-001` reason. The number of scanned answers was already available in
  the same function as `tracker.answer_count` (`canary.py:282`, used by the pass
  summary at `canary.py:289`).
- Leak behaviour VERIFIED as it stands: `build_answer_result` checks findings
  first (`canary.py:274-280`) and returns `Verdict.FAIL` before the
  `earlier_failure_reason` test, so a planted value found in a scanned answer
  still fails the check while the robustness stage is incomplete.
- D4 code VERIFIED: `_required` (`robustness.py:112-118`) returns `None` for a
  missing, empty or non-string `required` list. `_wrong_arguments`
  (`robustness.py:164-177`) returns `None` when the schema is not an object, when
  `properties` is not a mapping, when `_required` is `None`, or when a required
  name has no property entry. `CT-ROB-002` skips only on `_required` returning
  `None` (`robustness.py:342-353`). The conditions are therefore not identical.
- D5 code VERIFIED: `BANNED_SCHEMA_KEYS` (`robustness.py:29-48`) holds
  `pattern`, `format`, `minLength`, `maxLength`, `minimum`, `maximum`,
  `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`, `minItems`, `maxItems`,
  `anyOf`, `oneOf`, `allOf`, `$ref`, `not` and `if`. `make_valid_arguments`
  (`robustness.py:121-161`) refuses the schema when the schema itself or any
  top-level property carries one of them, and `_huge_arguments`
  (`robustness.py:180-193`) builds on it. `make_valid_arguments` returns only
  `None`, so the key name does not exist where the `not_tested` reason is built
  and no reason text can name it without new logic. None was added.
- Text occurrences VERIFIED by grep: `answers differed from the expected answer`
  existed only at `robustness.py:523`, `robustness checks did not complete` only
  at `runner.py:242`, and no test asserted either string, so no existing
  assertion had to be rewritten.

## D1 - the warn count

Before (`robustness.py:513-516`) and after (`robustness.py:513-515`):

```python
# before
warn_count = sum(
    item in ("success", "error_result", "jsonrpc_error", "no_answer")
    for item in outcomes
)
# after
warn_count = sum(
    item in FAILING_OUTCOMES.get(check_id, frozenset()) for item in outcomes
)
```

The reuse is exact: for `CT-ROB-001`, `CT-ROB-002` and `CT-ROB-003` the set is
`success`, `no_answer` and `exited`, and only `success` can be present when the
verdict is `warn`; for `CT-ROB-004` it is `no_answer` and `exited`; for
`CT-ROB-005` it is `error_result`, `jsonrpc_error`, `no_answer` and `exited`.
`exited` always produces `fail`, so it never reaches a warn sentence. A success
is now counted only where a success is the unexpected answer, and never for
`CT-ROB-004` or `CT-ROB-005`.

The one-word plural was added in the same place (`robustness.py:522-523`) so a
count of one reads `1 answer differed` instead of `1 answers differed`. No
threshold, verdict or probe changed.

Observed texts, same fixture, before the change and after it:

| Run | `CT-ROB-005` summary |
| --- | --- |
| before, mixed | `2 tested, 0 skipped; 2 answers differed from the expected answer.` |
| after, mixed | `2 tested, 0 skipped; 1 answer differed from the expected answer. The server rejected a generated placeholder value; this can be correct when the tool has format rules its schema does not state.` |
| before, reject all | `2 tested, 0 skipped; 2 answers differed from the expected answer.` |
| after, reject all | `2 tested, 0 skipped; 2 answers differed from the expected answer. The server rejected a generated placeholder value; this can be correct when the tool has format rules its schema does not state.` |

## D2 - the placeholder sentence

Added inside the warn branch (`robustness.py:524-530`), only for `CT-ROB-005` and
only when an `error_result` or `jsonrpc_error` caused the warn:

```python
if check_id == "CT-ROB-005" and any(
    item in ("error_result", "jsonrpc_error") for item in outcomes
):
    text += (
        " The server rejected a generated placeholder value; this can be"
        " correct when the tool has format rules its schema does not state."
    )
```

A warn caused only by `no_answer` does not get the sentence, because nothing was
rejected in that case. The verdict stays `warn` and the probe selection is
unchanged. The same meaning is on `docs/checks/CT-ROB-005.md` under "How it is
decided" and "Limits", in plain words with no judgement about the server.

## D3 - the canary reason

Before (`runner.py:237-242`): one string for every cause. After
(`runner.py:237-250`): the runner counts the six robustness results it already
holds and names both numbers.

```python
failed_count = sum(
    results_by_id[check_id].verdict is Verdict.FAIL for check_id in ROBUSTNESS_IDS
)
not_tested_count = sum(
    results_by_id[check_id].verdict is Verdict.NOT_TESTED for check_id in ROBUSTNESS_IDS
)
if failed_count or not_tested_count:
    earlier_failure_reason = (
        f"robustness checks: {failed_count} failed, {not_tested_count} not tested"
    )
```

`canary.py:281-284` appends the number of scanned answers, which the tracker
already counts:

```python
reason = earlier_failure_reason or "no tools/call answers were scanned"
if earlier_failure_reason is not None:
    reason += f"; {tracker.answer_count} tools/call answers were scanned"
```

Which situations produce `not_tested` is unchanged: zero answers, a `tools/list`
or start failure, or an incomplete robustness stage. The cause that keeps its own
text is unchanged too (`tools/list failed`, `server did not start`, an internal
error), and the count sentence is appended to it as well, which makes those
reasons more exact and no less correct.

Observed reasons for the mixed fixture, before and after:

| Check | Before | After |
| --- | --- | --- |
| `CT-CANARY-001` | `robustness checks did not complete` | `robustness checks: 0 failed, 2 not tested; 6 tools/call answers were scanned` |

For the failing variant (`bad_dies_after_probes.py`, `CT-ROB-006` fails) the
reason is `robustness checks: 1 failed, 0 not tested; 5 tools/call answers were
scanned`, so the two causes are distinguished by the numbers themselves.

Leak behaviour, quoted from `canary.py:274-286`: the findings branch returns
`Verdict.FAIL` before the reason branch is reached, so a planted value in a
scanned answer fails the check while robustness is incomplete. That behaviour is
unchanged and is now stated on the `CT-CANARY-001` page.

## D4 - skipped probes

`CT-ROB-001` and `CT-ROB-002` pages now say, from the quoted code above, when a
probe cannot be planned. One sentence each, added to "How it is decided":

- `CT-ROB-001`: no wrong-type value can be built when the schema is not an
  object, when `properties` is not an object, when the tool has no `required`
  list of property names, or when a required name has no property entry.
- `CT-ROB-002`: no missing-required probe can be planned when the tool has no
  `required` list of property names: the list is absent, empty, or contains an
  entry that is not a string.

Both pages already stated, and still state, that a skipped planned probe makes
the check `not_tested` and never `pass`; the new sentences repeat it next to the
condition so the reader does not have to look for it.

## D5 - refused keys

`docs/limitations.md` now lists every key of `BANNED_SCHEMA_KEYS` in one bullet
and says what happens: no valid input is generated for that tool, its
large-string and valid-call probes are skipped, its wrong-type and
missing-required probes are unaffected. The same rule, with a link to that page,
is in the "Limits" sections of `CT-ROB-004` and `CT-ROB-005`.

No reason text names the key. The refusal is a bare `return None` and the key is
not carried to the record, so naming it would be new logic, which this PR does
not add.

## D6 - drift test

`tests/test_docs.py` imports the existing constant and checks the page against
it; no new constant exists for the test:

```python
def test_limitations_lists_every_refused_schema_key() -> None:
    text = (ROOT / "docs/limitations.md").read_text(encoding="utf-8")
    missing = [key for key in BANNED_SCHEMA_KEYS if f"`{key}`" not in text]
    assert missing == []
```

## D7 - untouched

`workflow_dispatch`, the action versions, the CI permissions, the launcher, the
`--trust` requirement and `confirmed=True` are untouched. The six "Limits"
paragraphs keep their meaning: each got at most one added sentence about the
refused keys or the placeholder value.

## Changed tests

- `tests/test_robustness_runner.py`: added
  `test_valid_call_mixed_counts_only_the_rejected_answer` and
  `test_valid_call_reject_all_counts_every_answer`. No existing assertion in this
  file changed.
- `tests/test_canary_runner.py`: added
  `test_reason_counts_not_tested_robustness_checks_and_answers` and
  `test_reason_counts_failed_robustness_checks_and_answers`. No existing
  assertion changed.
- `tests/test_docs.py`: added `test_limitations_lists_every_refused_schema_key`
  and one import of the existing constant. No existing assertion changed.
- `docs/gallery.md`: one new row for `bad_valid_call_mixed.py`, which adds one
  parametrized gallery test; the reject-all variant is listed under "Not in the
  table".

All five new tests start a real subprocess except the documentation one, which is
pure.

## Mutation results

Each mutation was applied to the working tree, checked with ruff, run against the
named test, and restored; `git diff --stat` matched the pre-mutation state after
each restore.

| ID | Mutation | Named test | Result |
| --- | --- | --- | --- |
| M1 | warn count back to the old fixed tuple | `test_valid_call_mixed_counts_only_the_rejected_answer` | red: summary was `2 tested, 0 skipped; 2 answers differed...`; green after restore |
| M2 | D2 sentence removed | `test_valid_call_mixed_counts_only_the_rejected_answer` | red: summary was `2 tested, 0 skipped; 1 answer differed from the expected answer.`; green after restore |
| M3 | `CT-CANARY-001` reason back to the generic text | `test_reason_counts_not_tested_robustness_checks_and_answers` | red: reason was `robustness checks did not complete; 6 tools/call answers were scanned`; green after restore |
| M4 | `multipleOf` removed from the limitations list | `test_limitations_lists_every_refused_schema_key` | red: `assert ['multipleOf'] == []`; green after restore |
| M5 | not applicable | - | no reason text carries a key name, so there is nothing to remove |
