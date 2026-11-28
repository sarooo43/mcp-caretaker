# mcp-caretaker report

Tool: mcp-caretaker 0.0.0.dev0
Program:
```
mcp-server-git
```
Arguments: 2
Protocol version:
```
2025-11-25
```

## Results

| ID | Title | Verdict |
| --- | --- | --- |
| CT-START-001 | Server starts and completes handshake | pass |
| CT-START-002 | Handshake reports server name and version | pass |
| CT-START-003 | tools/list works | pass |
| CT-START-004 | No non-protocol text on stdout | pass |
| CT-START-005 | Server exits after input is closed | pass |
| CT-DESC-001 | Every tool has a description | pass |
| CT-DESC-002 | Description length is within limits | pass |
| CT-DESC-003 | Tool names are unique | pass |
| CT-DESC-004 | Every tool has an object inputSchema | pass |
| CT-DESC-005 | Every top-level property is typed | pass |
| CT-DESC-006 | Every top-level property has a description | warn |
| CT-DESC-007 | No hidden characters in scanned text | pass |
| CT-DESC-008 | No long horizontal whitespace runs | pass |
| CT-DESC-009 | Tool names match the spec name rule | pass |
| CT-ROB-001 | Wrong-type input is rejected | pass |
| CT-ROB-002 | Missing required input is rejected | pass |
| CT-ROB-003 | Unknown tool name is rejected | pass |
| CT-ROB-004 | Large string input is handled | pass |
| CT-ROB-005 | Valid read-only call succeeds | warn |
| CT-ROB-006 | Server remains responsive after probes | pass |
| CT-CANARY-001 | Canary values are absent from tool answers | pass |
| CT-CANARY-002 | Canary values are absent from handshake and tool listings | pass |
| CT-CANARY-003 | Canary values are absent from stderr and stray stdout | pass |
| CT-STAB-001 | Tool listings are stable across a second session | pass |
| CT-STAB-002 | Tool listing is stable after probes | pass |

## Totals

- pass: 23
- warn: 2
- fail: 0
- not_tested: 0

A pass is not a safety guarantee. Running a server executes its code; this tool is not a sandbox.

## Details

### CT-DESC-006 Every top-level property has a description [WARN]

```
summary: 21 top-level properties have no description.
evidence 1 subject: tool[0] git_status properties[repo_path]
evidence 1 detail: no description
evidence 2 subject: tool[1] git_diff_unstaged properties[repo_path]
evidence 2 detail: no description
evidence 3 subject: tool[1] git_diff_unstaged properties[context_lines]
evidence 3 detail: no description
evidence 4 subject: tool[2] git_diff_staged properties[repo_path]
evidence 4 detail: no description
evidence 5 subject: tool[2] git_diff_staged properties[context_lines]
evidence 5 detail: no description
evidence 6 subject: tool[3] git_diff properties[repo_path]
evidence 6 detail: no description
evidence 7 subject: tool[3] git_diff properties[target]
evidence 7 detail: no description
evidence 8 subject: tool[3] git_diff properties[context_lines]
evidence 8 detail: no description
evidence 9 subject: tool[4] git_commit properties[repo_path]
evidence 9 detail: no description
evidence 10 subject: tool[4] git_commit properties[message]
evidence 10 detail: no description
evidence 11 subject: tool[5] git_add properties[repo_path]
evidence 11 detail: no description
evidence 12 subject: tool[5] git_add properties[files]
evidence 12 detail: no description
evidence 13 subject: tool[6] git_reset properties[repo_path]
evidence 13 detail: no description
evidence 14 subject: tool[7] git_log properties[repo_path]
evidence 14 detail: no description
evidence 15 subject: tool[8] git_create_branch properties[repo_path]
evidence 15 detail: no description
evidence 16 subject: tool[8] git_create_branch properties[branch_name]
evidence 16 detail: no description
evidence 17 subject: tool[9] git_checkout properties[repo_path]
evidence 17 detail: no description
evidence 18 subject: tool[9] git_checkout properties[branch_name]
evidence 18 detail: no description
evidence 19 subject: tool[10] git_merge properties[repo_path]
evidence 19 detail: no description
evidence 20 subject: tool[11] git_show properties[repo_path]
evidence 20 detail: no description
evidence 21 subject: evidence
evidence 21 detail: 1 more not shown
```

### CT-ROB-005 Valid read-only call succeeds [WARN]

```
summary: 6 tested, 2 skipped; 6 answers differed from the expected answer. The server rejected a generated placeholder value; this can be correct when the tool has format rules its schema does not state.
evidence 1 subject: probe CT-ROB-005 tool[0] git_status valid_call
evidence 1 detail: {"tool":"git_status","phase":"valid_call","args":{"repo_path":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool git_status: Repository path 'A' is outside the allowed repository '/tmp/ct8b/repo'"}}
evidence 2 subject: replay CT-ROB-005 tool[0] git_status
evidence 2 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 2 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_status","arguments":{"repo_path":"A"}}}
evidence 3 subject: probe CT-ROB-005 tool[1] git_diff_unstaged valid_call
evidence 3 detail: {"tool":"git_diff_unstaged","phase":"valid_call","args":{"repo_path":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool git_diff_unstaged: Repository path 'A' is outside the allowed repository '/tmp/ct8b/repo'"}}
evidence 4 subject: replay CT-ROB-005 tool[1] git_diff_unstaged
evidence 4 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 4 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_diff_unstaged","arguments":{"repo_path":"A"}}}
evidence 5 subject: probe CT-ROB-005 tool[2] git_diff_staged valid_call
evidence 5 detail: {"tool":"git_diff_staged","phase":"valid_call","args":{"repo_path":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool git_diff_staged: Repository path 'A' is outside the allowed repository '/tmp/ct8b/repo'"}}
evidence 6 subject: replay CT-ROB-005 tool[2] git_diff_staged
evidence 6 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 6 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_diff_staged","arguments":{"repo_path":"A"}}}
evidence 7 subject: probe CT-ROB-005 tool[3] git_diff valid_call
evidence 7 detail: {"tool":"git_diff","phase":"valid_call","args":{"repo_path":{"type":"str","length":1},"target":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool git_diff: Repository path 'A' is outside the allowed repository '/tmp/ct8b/repo'"}}
evidence 8 subject: replay CT-ROB-005 tool[3] git_diff
evidence 8 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 8 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_diff","arguments":{"repo_path":"A","target":"A"}}}
evidence 9 subject: probe CT-ROB-005 tool[7] git_log valid_call
evidence 9 detail: {"tool":"git_log","phase":"valid_call","outcome":"skipped","reason":"valid input could not be generated for this tool"}
evidence 10 subject: probe CT-ROB-005 tool[11] git_show valid_call
evidence 10 detail: {"tool":"git_show","phase":"valid_call","args":{"repo_path":{"type":"str","length":1},"revision":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool git_show: Repository path 'A' is outside the allowed repository '/tmp/ct8b/repo'"}}
evidence 11 subject: replay CT-ROB-005 tool[11] git_show
evidence 11 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 11 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_show","arguments":{"repo_path":"A","revision":"A"}}}
evidence 12 subject: probe CT-ROB-005 tool[12] git_branch valid_call
evidence 12 detail: {"tool":"git_branch","phase":"valid_call","outcome":"skipped","reason":"valid input could not be generated for this tool"}
evidence 13 subject: probe CT-ROB-005 tool[13] git_remote valid_call
evidence 13 detail: {"tool":"git_remote","phase":"valid_call","args":{"repo_path":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool git_remote: Repository path 'A' is outside the allowed repository '/tmp/ct8b/repo'"}}
evidence 14 subject: replay CT-ROB-005 tool[13] git_remote
evidence 14 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 14 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_remote","arguments":{"repo_path":"A"}}}
evidence 15 subject: coverage
evidence 15 detail: 6 tested, 2 skipped
```
