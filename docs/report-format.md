# Report format

The JSON report is the source of truth. Markdown and the terminal summary are
rendered from the same JSON-ready dict in `src/mcp_caretaker/report.py`.
Server text is untrusted input: it is only quoted, never executed, used as a
path, or sent to a network.

## JSON fields

The file is UTF-8, indented by 2 spaces, with non-ASCII escaped, keys in the
order below, and one trailing newline. There is no timestamp, no random value,
and no per-run value: two runs against an unchanged server give byte-identical
JSON. This was verified with two real runs against `clean_server.py`.

| Field | Meaning |
| --- | --- |
| `schema_version` | Always `1`. |
| `tool.name` | Always `mcp-caretaker`. |
| `tool.version` | The package version from `mcp_caretaker.__version__`. |
| `server.program` | File name only of the server program. Directory parts are removed for both slash styles. |
| `server.argument_count` | Number of server arguments after the program. Server arguments themselves are never written. |
| `protocol_version` | Negotiated protocol version string, or `null` when the handshake did not complete. |
| `counts.pass` | Number of results with verdict `pass`. |
| `counts.warn` | Number of results with verdict `warn`. |
| `counts.fail` | Number of results with verdict `fail`. |
| `counts.not_tested` | Number of results with verdict `not_tested`. |
| `results` | All 25 result dicts from `RunResult.to_dict()`, in registry order. Each has `check_id`, `title`, `verdict`, `summary`, `evidence`, and `reason`. Each evidence item has `subject`, `detail`, and `replay`. |

Verdict words are exactly `pass`, `warn`, `fail`, and `not_tested`. A
`not_tested` result always has a reason and is never counted or displayed as
pass.

## Exit codes

- `0`: no result failed, and no result warned when `--fail-on warn` is given.
- `1`: at least one result failed, or at least one warned with `--fail-on warn`.
- `2`: usage error, unwritable output location, or unexpected internal error.

`not_tested` never changes the exit code. A server that does not start is a
normal run: `CT-START-001` is `fail`, the other 24 results are `not_tested`,
and the exit code is `1`.

## Markdown rules

Markdown is rendered from the same dict. The title and header facts come
first, then a table with one row per check holding only the check ID, title,
and verdict. Titles and verdicts are constant strings. Totals and the safety
sentence follow. The Details section has one block per non-pass result.

Every server-derived string (summary, reason, and evidence subject, detail,
and replay) appears only inside a fenced code block. The fence is longer than
the longest backtick run inside the block, with a minimum of 3 backticks, so
server text cannot close the fence early. Nothing server-derived appears
outside a fence.

## Terminal rules

The terminal summary is printable ASCII only. Every string that can contain
server text (summaries, reasons, evidence, tool names, paths) passes through
one escape function that escapes every character outside printable ASCII,
including escape and control characters. Output does not depend on the
console code page. The summary shows the header facts, all 25 check lines in
registry order, summary and evidence subject and detail for every non-pass
(no replay), the four totals, the safety sentence, and the paths of written
files.

A pass is not a safety guarantee. Running a server executes its code; this
tool is not a sandbox.
