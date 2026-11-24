# Fixture gallery

These are local stdio servers used by the tests. They are test fixtures, not
templates. Tests start them as real subprocesses with absolute script paths;
mocks of the subprocess or SDK do not count as behaviour evidence. Relative paths
in `argv` are not rewritten by the launcher, so use absolute paths.

`_raw_tools.py` is a standard-library-only helper. It writes line-delimited
JSON-RPC on stdout and lets a fixture choose raw `tools/list` pages. This keeps
wire text available to the bounded bridge tap even when the SDK's own objects
would drop or reject it. No server text is executed, used as a path, or sent to a
network. Fake text values passed through `extra_env` are obvious test strings,
never real secrets.

| Fixture | Source | What it exercises |
| --- | --- | --- |
| `clean_server.py` | official SDK | Clean handshake, two tools, described and typed top-level properties |
| `bad_descriptions.py` | raw helper | One separate problem for each description/schema check |
| `bad_duplicate_names.py` | raw helper | Two tools with the same name |
| `bad_hidden_characters.py` | raw helper | Format, control and private-use characters in scanned fields |
| `paginated_server.py` | raw helper | Two `tools/list` pages; page two has a tool with no description |
| `bad_page_cap.py` | raw helper | More pages than `MAX_TOOLS_PAGES`; the last page is not read |
| `bad_tools_list_error.py` | raw helper | JSON-RPC error for `tools/list` |
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
