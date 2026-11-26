# Fixture gallery and what it detects

Every fixture under `examples/servers/` is written for this project; no code was
copied from another repository. A fixture is a real local stdio server: starting
one runs code on this machine, so start it only with `--trust`, exactly like any
other server. The tool never executes fixture text and never uses it as a path.

Two tables follow. `clean_server.py` is the control server. The bad-servers table
lists, for each fixture and mode, the `warn` and `fail` results that a real run
produces. `not_tested` results are ignored by the test that checks the table, so
a row can show `none` and still have `not_tested` results.

Reproduce any row with one shell command per line, using absolute paths:

```sh
<python> -m mcp_caretaker check --trust -- <python> <repo>/examples/servers/bad_no_descriptions.py
```

For a row with an argument or an option, keep that argument after the fixture
path and put the option before the first `--`.

## Control servers

| Fixture | Arguments | Options | Expected warn/fail results | Note |
| --- | --- | --- | --- | --- |
| clean_server.py | - | - | none | Official-SDK server with two described, typed, read-only tools |

## Bad servers

| Fixture | Arguments | Options | Expected warn/fail results | Note |
| --- | --- | --- | --- | --- |
| good_server.py | - | - | CT-DESC-006:warn, CT-START-002:warn | PR 1 launcher fixture; its handshake and one property description are not clean by the current rules |
| bad_exits_immediately.py | - | - | CT-START-001:fail | Exits before the handshake |
| bad_hangs_on_startup.py | - | --startup-timeout 2 | CT-START-001:fail | Never answers `initialize`; the option keeps the run short |
| bad_empty_handshake.py | - | - | CT-START-002:warn | Empty `serverInfo.name` and `serverInfo.version` |
| bad_tools_list_error.py | - | - | CT-START-003:fail | `tools/list` returns a JSON-RPC error |
| bad_page_cap.py | - | - | CT-START-003:warn, CT-STAB-002:warn | More pages than the page cap; the listing changes between reads |
| leaky_stdout.py | - | - | CT-START-004:warn | Non-protocol stdout lines before the protocol stream |
| bad_ignores_stdin_close.py | - | - | CT-START-005:warn | Keeps running after stdin closes and has to be killed |
| bad_no_descriptions.py | - | - | CT-DESC-001:warn | One tool has no description |
| bad_description_length.py | - | - | CT-DESC-002:warn | 5- and 1100-character descriptions |
| bad_duplicate_names.py | - | - | CT-DESC-003:fail | Two tools share one name |
| bad_schema_not_object.py | - | - | CT-DESC-004:fail, CT-ROB-006:fail | Missing object schema; the server also stops answering after the probes |
| bad_missing_types.py | - | - | CT-DESC-005:warn | One top-level property has no typed key |
| bad_missing_property_descriptions.py | - | - | CT-DESC-006:warn | One top-level property has no description |
| bad_hidden_characters.py | - | - | CT-DESC-007:warn | Format, control and private-use characters in scanned fields |
| bad_whitespace_run.py | - | - | CT-DESC-008:warn | An 80-space run in a description |
| bad_tool_name_format.py | - | - | CT-DESC-009:warn | A name with a space and a 129-character name |
| bad_wrong_type.py | - | - | CT-ROB-001:warn | Accepts a wrong-type value instead of rejecting it |
| bad_missing_required.py | - | - | CT-ROB-002:warn | Accepts a call that omits a required property |
| bad_unknown_tool.py | - | - | CT-ROB-003:warn | Answers a call for an unknown tool name |
| bad_huge_input.py | - | --call-timeout 2 | CT-ROB-001:warn, CT-ROB-002:warn, CT-ROB-003:warn, CT-ROB-004:warn | Delays every call; the option keeps the run short |
| bad_valid_call.py | - | - | CT-ROB-005:warn | Rejects the generated valid call |
| bad_valid_call_mixed.py | - | - | CT-ROB-005:warn | One read-only tool accepts the generated valid call and one read-only tool with no required property rejects every call |
| bad_dies_after_probes.py | - | - | CT-ROB-006:fail | Exits after the planned probes, so the liveness list fails |
| bad_rug_pull.py | reconnect_description | - | CT-ROB-004:warn, CT-ROB-005:warn, CT-STAB-001:fail | Description changes on the second connection |
| bad_rug_pull.py | after_calls_description | - | CT-ROB-004:warn, CT-ROB-005:warn, CT-STAB-002:fail | Description changes after calls; the final liveness list differs |
| bad_canary_leaks.py | result_text | - | CT-CANARY-001:fail | Planted value in a tool answer |
| bad_canary_leaks.py | server_name | - | CT-CANARY-002:fail | Planted value in the handshake `serverInfo` |
| bad_canary_leaks.py | stderr | - | CT-CANARY-003:warn | Planted value on stderr |
| bad_canary_leaks.py | stdout | - | CT-START-004:warn, CT-CANARY-003:warn | Planted value on stray stdout with a long prefix |
| bad_hostile_text.py | - | - | CT-DESC-007:warn, CT-START-004:warn | Backticks, a link, an HTML tag, an escape character and a non-ASCII letter |
| bad_instruction_text.py | - | - | none | Visible instruction-like text in two descriptions is not detected |
| only_writers_server.py | - | - | none | Writer tools only; the large-string and valid-call probes are `not_tested` |

## Not in the table

Some variants need a test-only environment variable, so they are not rows:

- `bad_tools_list_error.py` zero-tools variant: `CARETAKER_TEST_ZERO_TOOLS=1`.
- `bad_dies_after_probes.py` other stop points: `CARETAKER_TEST_MODE=call` or `list`.
- `bad_rug_pull.py` second-start failure: `CARETAKER_TEST_SECOND_START_FAIL=1`.
- `bad_valid_call_mixed.py` reject-all variant: `CARETAKER_TEST_MODE=reject_all` makes the accepting tool reject the generated valid call as well.
- `bad_ignores_stdin_close.py` pid record: `CARETAKER_TEST_PIDFILE`.
- `recording_server.py` call log: `CARETAKER_TEST_CALLLOG`.

Those variants, and the non-bad fixtures `probe_server.py`, `spawns_grandchild.py`,
`paginated_server.py` and `complex_schema_server.py`, are exercised by direct
tests in `tests/` rather than by a table row.

## What the table does not show

A row whose expected results are `none` is a case this tool does **not** detect.
`bad_instruction_text.py` is the clear example: both descriptions read like
instructions to an assistant, and the tool reports nothing about them.
`only_writers_server.py` shows the same for coverage: with no read-only tool the
large-string and valid-call probes are `not_tested`, which is not a finding.

## Three description risks in plain words

- Hidden or disguised text. `CT-DESC-007` reports characters in Unicode
  categories `Cf`, `Co` and `Cs` plus control characters in the scanned fields,
  and `CT-DESC-008` reports long horizontal runs. Text that is fully visible but
  misleading, translated, split across fields, or encoded in plain letters is not
  reported. Nothing is decoded and no meaning is inferred.
- One tool's text steering the use of another tool. This is not detected.
  `bad_instruction_text.py` contains exactly that pattern and the table shows
  `none`. Checks look at lengths, characters, naming and schema shape, never at
  what a sentence asks a reader to do.
- A tool list that changes after trust. `CT-STAB-001` compares the first listing
  with a second session's listing, and `CT-STAB-002` compares the first listing
  with the listing read again after the probes. The comparison covers `title`,
  `description`, `inputSchema`, `outputSchema` and `annotations` by name. Changes
  triggered by time, by a call count, or by specific arguments are not caught,
  and tools added or removed are only caught when one of those two reads sees it.
