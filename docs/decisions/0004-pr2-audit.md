# 0004 - PR 2 test and fixture audit

This audit was written before the robustness product code. A name is marked
`YES` only when the exact test name existed at audit time. An equivalent name is
shown with the assertion it already covered; the action column records the exact
name change or new test that was applied. Every new behaviour test uses a real
subprocess under `examples/servers/`. All rows in the table are now implemented.

The brief says 32 required names and then enumerates 33. I treated all 33 names
as required. The consolidated `bad_descriptions.py` fixture and its one
consolidated runner test were replaced by focused fixtures and exact-name tests.

| Required test name | Found? (file::test) | Action |
| --- | --- | --- |
| `test_registry_lists_all_14_check_ids_in_order` | equivalent: `tests/test_model.py::test_check_registry_has_14_unique_ids_in_order` | Keep the PR 2 prefix assertion under this exact name; T8 updates the full registry test to 20. |
| `test_every_check_has_docs_page_with_required_headings` | equivalent: `tests/test_docs.py::test_every_check_has_docs_page_with_exact_headings` | Rename to exact name. |
| `test_every_docs_page_matches_a_registered_check` | no | Add exact-name docs test. |
| `test_titles_and_summaries_avoid_banned_words` | no | Add exact-name registry and summary test. |
| `test_desc_002_length_boundaries` | YES `tests/test_checks_pure.py::test_desc_002_length_boundaries` | Keep. |
| `test_desc_005_typed_equivalents` | equivalent: `tests/test_checks_pure.py::test_desc_005_typed_equivalents_and_untyped_property` | Rename to exact name. |
| `test_desc_007_flags_zero_width_and_bidi_but_not_newline_or_tab` | equivalent: `tests/test_checks_pure.py::test_desc_007_hidden_categories_and_allowed_marks` | Rename to exact name. |
| `test_desc_008_run_length_boundary` | YES `tests/test_checks_pure.py::test_desc_008_run_length_boundary` | Keep. |
| `test_desc_009_name_rule_boundaries` | YES `tests/test_checks_pure.py::test_desc_009_name_rule_boundaries` | Keep. |
| `test_evidence_is_capped_and_escaped` | equivalent: `tests/test_model.py::test_evidence_is_redacted_escaped_capped_and_omits_extra_items` | Rename to exact name. |
| `test_result_to_dict_is_json_serialisable_with_stable_keys` | equivalent: `tests/test_model.py::test_run_result_to_dict_is_json_serialisable_and_has_no_score` | Rename and update the forced evidence key set for `replay`. |
| `test_sdk_windows_helper_is_importable` | YES `tests/test_sdk_windows_helper.py::test_sdk_windows_helper_is_importable` | Keep. |
| `test_unconfirmed_run_raises_before_spawn` | equivalent: `tests/test_runner.py::test_confirmation_required_propagates_before_spawn` | Rename to exact name. |
| `test_clean_server_passes_all_checks` | equivalent: `tests/test_runner.py::test_clean_server_passes_all_14_checks` | Rename and update the forced count to all 20 checks. |
| `test_startup_exit_fails_start_001_and_everything_else_is_not_tested` | YES `tests/test_runner.py::test_startup_exit_fails_start_001_and_everything_else_is_not_tested` | Keep and update the forced count of other results. |
| `test_startup_hang_fails_start_001` | equivalent: `tests/test_runner.py::test_startup_hang_fails_start_001_and_everything_else_is_not_tested` | Rename to exact name; keep stronger assertions. |
| `test_no_server_info_warns_start_002` | equivalent: `tests/test_runner.py::test_empty_handshake_warns_start_002_and_keeps_protocol_version` | Rename to exact name. |
| `test_zero_tools_warns_start_003` | no real-subprocess test | Add exact-name real-subprocess test using a zero-tools mode of an existing fixture. |
| `test_tools_list_error_fails_start_003_and_desc_checks_not_tested` | equivalent: `tests/test_runner.py::test_tools_list_error_fails_start_003_and_desc_checks_are_not_tested` | Renamed to exact name; robustness checks are included as not tested. |
| `test_stdout_noise_start_004` | equivalent: `tests/test_runner.py::test_leaky_stdout_warns_start_004_and_cap_is_bounded` | Rename to exact name. |
| `test_server_that_ignores_stdin_close_warns_start_005_and_is_killed` | YES `tests/test_runner.py::test_server_that_ignores_stdin_close_warns_start_005_and_is_killed` | Keep. |
| `test_pagination_collects_all_pages_and_flags_page_two_tool` | equivalent: `tests/test_runner.py::test_paginated_tools_are_collected_and_flag_page_two_tool` | Rename to exact name. |
| `test_bad_no_descriptions_warns_desc_001` | no | Add `bad_no_descriptions.py` and exact-name real-subprocess test. |
| `test_bad_description_length_warns_desc_002` | no | Add `bad_description_length.py` with 5- and 1100-character descriptions and exact-name test. |
| `test_bad_duplicate_names_fails_desc_003` | YES `tests/test_runner.py::test_bad_duplicate_names_fails_desc_003` | Keep existing fixture. |
| `test_bad_schema_fails_desc_004` | no | Add `bad_schema_not_object.py` with one missing and one string `inputSchema`, and exact-name test. |
| `test_bad_missing_types_warns_desc_005` | no | Add `bad_missing_types.py` and exact-name test. |
| `test_bad_missing_property_descriptions_warns_desc_006` | no | Add `bad_missing_property_descriptions.py` and exact-name test. |
| `test_bad_hidden_characters_warns_desc_007` | YES `tests/test_runner.py::test_bad_hidden_characters_warns_desc_007` | Keep existing fixture. |
| `test_bad_whitespace_run_warns_desc_008` | no | Add `bad_whitespace_run.py` with 80 spaces plus harmless filler and exact-name test. |
| `test_bad_tool_name_format_warns_desc_009` | no | Add `bad_tool_name_format.py` with a space and a 129-character name, and exact-name test. |
| `test_evidence_redacts_extra_env_value` | YES `tests/test_runner.py::test_evidence_redacts_extra_env_value` | Keep. |
| `test_crashing_check_becomes_not_tested_and_others_still_run` | equivalent: `tests/test_runner.py::test_crashing_check_is_not_tested_with_reason_and_others_still_run` | Rename to exact name. |

The exact-name tools/list error test now asserts that every `CT-DESC-*` and
`CT-ROB-*` result is `not_tested` with reason `tools/list failed`.

## Fixture split

`bad_descriptions.py` and `test_bad_descriptions_warn_or_fail_expected_description_checks`
were removed. Each replacement fixture has a standard docstring, one deliberate
description/schema problem, and one exact-name real-subprocess test. The fixture
gallery was updated with the focused files.

## Decisions I made

- Equivalent names are renamed where the assertion already matches; no duplicate alias functions are left behind.
- The zero-tools case uses a mode on `bad_tools_list_error.py` so no extra startup fixture is introduced.
- The brief's 32/33 count difference is resolved by requiring every enumerated name.
