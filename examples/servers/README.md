# Fixture gallery

These are local stdio servers used by the tests. They are test fixtures, not
templates. Tests start them as real subprocesses with absolute script paths;
mocks of the subprocess or SDK do not count as behaviour evidence. Relative paths
in `argv` are not rewritten by the launcher, so use absolute paths.

**From this version, tools that declare readOnlyHint receive real calls with generated input. A server can lie about that hint. Only test servers you trust.**

`_raw_tools.py` is a standard-library-only helper. It writes line-delimited
JSON-RPC on stdout and lets a fixture choose raw `tools/list` pages. This keeps
wire text available to the bounded bridge tap even when the SDK's own objects
would drop or reject it. It also supports an optional `on_call` handler. When
`CARETAKER_TEST_CALLLOG` is set, it appends JSON lines containing only
`{tool,args:{key:{type,length}}}`; argument values are never written. No server
text is executed, used as a path, or sent to a network. Fake text values passed
through `extra_env` are obvious test strings, never real secrets.

| Fixture | Source | What it exercises |
| --- | --- | --- |
| `clean_server.py` | official SDK | Clean handshake, two read-only tools, described and typed top-level properties |
| `bad_no_descriptions.py` | raw helper | One tool with no description |
| `bad_description_length.py` | raw helper | 5- and 1100-character descriptions |
| `bad_schema_not_object.py` | raw helper | One missing `inputSchema` and one string `inputSchema` |
| `bad_missing_types.py` | raw helper | One untyped top-level property |
| `bad_missing_property_descriptions.py` | raw helper | One undocumented top-level property |
| `bad_whitespace_run.py` | raw helper | 80 spaces plus harmless filler |
| `bad_tool_name_format.py` | raw helper | A name with a space and a 129-character name |
| `bad_duplicate_names.py` | raw helper | Two tools with the same name |
| `bad_hidden_characters.py` | raw helper | Format, control and private-use characters in scanned fields |
| `paginated_server.py` | raw helper | Two `tools/list` pages; page two has a tool with no description |
| `bad_page_cap.py` | raw helper | More pages than `MAX_TOOLS_PAGES`; the last page is not read |
| `bad_tools_list_error.py` | raw helper | JSON-RPC error for `tools/list`; zero-tools mode with `CARETAKER_TEST_ZERO_TOOLS` |
| `bad_dies_after_probes.py` | raw helper | Exits during a call, after `tools/list`, or after the planned probes |
| `bad_wrong_type.py` | raw helper | Accepts, delays, or exits during a wrong-type call |
| `bad_missing_required.py` | raw helper | Accepts or exits during a missing-required call |
| `bad_unknown_tool.py` | raw helper | Accepts or exits during the unknown-tool call |
| `bad_huge_input.py` | raw helper | Delays or exits during the large-string call |
| `bad_valid_call.py` | raw helper | Rejects or exits during the generated valid call |
| `recording_server.py` | raw helper | Records call shapes for one writer and one read-only tool |
| `only_writers_server.py` | raw helper | Writer tools only; large and valid calls are not tested |
| `complex_schema_server.py` | raw helper | Read-only tool with a pattern constraint |
| `bad_empty_handshake.py` | raw helper | Empty `serverInfo.name` and `serverInfo.version` |
| `leaky_stdout.py` | raw helper | Non-protocol stdout lines with fake text and a control character |
| `bad_ignores_stdin_close.py` | raw helper | Keeps running after stdin EOF; records its pid for cleanup tests |
| `good_server.py` | official SDK | PR 1 launcher fixture, still used by existing tests |
| `probe_server.py` | official SDK | PR 1 environment and stderr fixture, still used by existing tests |
| `spawns_grandchild.py` | official SDK | PR 1 process-tree fixture, still used by existing tests |
| `bad_exits_immediately.py` | standard library | PR 1 startup fixture reused for CT-START-001 |
| `bad_hangs_on_startup.py` | standard library | PR 1 startup fixture reused for CT-START-001 |

The check results are returned only as library objects. There is no report file,
no score, no grade, and no command line check command yet. See `docs/checks/`.
