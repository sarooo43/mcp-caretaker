# mcp-caretaker report

Tool: mcp-caretaker 0.0.0.dev0
Program:
```
mcp-server-time
```
Arguments: 0
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
| CT-DESC-006 | Every top-level property has a description | pass |
| CT-DESC-007 | No hidden characters in scanned text | pass |
| CT-DESC-008 | No long horizontal whitespace runs | pass |
| CT-DESC-009 | Tool names match the spec name rule | pass |
| CT-ROB-001 | Wrong-type input is rejected | not_tested |
| CT-ROB-002 | Missing required input is rejected | not_tested |
| CT-ROB-003 | Unknown tool name is rejected | pass |
| CT-ROB-004 | Large string input is handled | pass |
| CT-ROB-005 | Valid read-only call succeeds | warn |
| CT-ROB-006 | Server remains responsive after probes | pass |
| CT-CANARY-001 | Canary values are absent from tool answers | not_tested |
| CT-CANARY-002 | Canary values are absent from handshake and tool listings | pass |
| CT-CANARY-003 | Canary values are absent from stderr and stray stdout | pass |
| CT-STAB-001 | Tool listings are stable across a second session | pass |
| CT-STAB-002 | Tool listing is stable after probes | pass |

## Totals

- pass: 21
- warn: 1
- fail: 0
- not_tested: 3

A pass is not a safety guarantee. Running a server executes its code; this tool is not a sandbox.

## Details

### CT-ROB-001 Wrong-type input is rejected [NOT_TESTED]

```
summary: 1 tested, 2 skipped; at least one planned probe was skipped.
reason: no required property was available for wrong-type input
evidence 1 subject: probe CT-ROB-001 tool[0] get_current_time wrong_type
evidence 1 detail: {"tool":"get_current_time","phase":"wrong_type","outcome":"skipped","reason":"no required property was available for wrong-type input"}
evidence 2 subject: probe CT-ROB-001 tool[1] convert_time wrong_type
evidence 2 detail: {"tool":"convert_time","phase":"wrong_type","args":{"time":{"type":"dict","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool convert_time: 1 validation error for convert_timeArguments\ntime\n  Input should be a valid string [t"}}
evidence 3 subject: probe CT-ROB-001 tool[2] get_time_ago wrong_type
evidence 3 detail: {"tool":"get_time_ago","phase":"wrong_type","outcome":"skipped","reason":"no required property was available for wrong-type input"}
evidence 4 subject: coverage
evidence 4 detail: 1 tested, 2 skipped
```

### CT-ROB-002 Missing required input is rejected [NOT_TESTED]

```
summary: 1 tested, 2 skipped; at least one planned probe was skipped.
reason: no required property was available for missing-required input
evidence 1 subject: probe CT-ROB-002 tool[0] get_current_time missing_required
evidence 1 detail: {"tool":"get_current_time","phase":"missing_required","outcome":"skipped","reason":"no required property was available for missing-required input"}
evidence 2 subject: probe CT-ROB-002 tool[1] convert_time missing_required
evidence 2 detail: {"tool":"convert_time","phase":"missing_required","args":{},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool convert_time: 1 validation error for convert_timeArguments\ntime\n  Field required [type=missing, inp"}}
evidence 3 subject: probe CT-ROB-002 tool[2] get_time_ago missing_required
evidence 3 detail: {"tool":"get_time_ago","phase":"missing_required","outcome":"skipped","reason":"no required property was available for missing-required input"}
evidence 4 subject: coverage
evidence 4 detail: 1 tested, 2 skipped
```

### CT-ROB-005 Valid read-only call succeeds [WARN]

```
summary: 2 tested, 1 skipped; 1 answer differed from the expected answer. The server rejected a generated placeholder value; this can be correct when the tool has format rules its schema does not state.
evidence 1 subject: probe CT-ROB-005 tool[0] get_current_time valid_call
evidence 1 detail: {"tool":"get_current_time","phase":"valid_call","args":{},"outcome":"success","answer":{"is_error":false,"text":"{\n  \"timezone\": \"Etc/UTC\",\n  \"datetime\": \"2026-11-28T01:05:26+00:00\",\n  \"day_of_week\": \"Saturday\",\n  \"is_dst\": false\n}"}}
evidence 2 subject: probe CT-ROB-005 tool[1] convert_time valid_call
evidence 2 detail: {"tool":"convert_time","phase":"valid_call","args":{"time":{"type":"str","length":1}},"outcome":"error_result","answer":{"is_error":true,"text":"Error executing tool convert_time: Invalid time format. Expected HH:MM [24-hour format]"}}
evidence 3 subject: replay CT-ROB-005 tool[1] convert_time
evidence 3 detail: constructed one-line JSON-RPC tools/call; not byte-exact; needs initialize handshake first
evidence 3 replay: {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"convert_time","arguments":{"time":"A"}}}
evidence 4 subject: probe CT-ROB-005 tool[2] get_time_ago valid_call
evidence 4 detail: {"tool":"get_time_ago","phase":"valid_call","outcome":"skipped","reason":"valid input could not be generated for this tool"}
evidence 5 subject: coverage
evidence 5 detail: 2 tested, 1 skipped
```

### CT-CANARY-001 Canary values are absent from tool answers [NOT_TESTED]

```
summary: Check was not tested.
reason: robustness checks: 0 failed, 2 not tested; tools/call answers scanned: 6
```
