# mcp-caretaker report

Tool: mcp-caretaker 0.0.0.dev0
Program:
```
mcp-server-fetch
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
| CT-ROB-001 | Wrong-type input is rejected | pass |
| CT-ROB-002 | Missing required input is rejected | pass |
| CT-ROB-003 | Unknown tool name is rejected | pass |
| CT-ROB-004 | Large string input is handled | not_tested |
| CT-ROB-005 | Valid read-only call succeeds | not_tested |
| CT-ROB-006 | Server remains responsive after probes | pass |
| CT-CANARY-001 | Canary values are absent from tool answers | not_tested |
| CT-CANARY-002 | Canary values are absent from handshake and tool listings | pass |
| CT-CANARY-003 | Canary values are absent from stderr and stray stdout | pass |
| CT-STAB-001 | Tool listings are stable across a second session | pass |
| CT-STAB-002 | Tool listing is stable after probes | pass |

## Totals

- pass: 22
- warn: 0
- fail: 0
- not_tested: 3

A pass is not a safety guarantee. Running a server executes its code; this tool is not a sandbox.

## Details

### CT-ROB-004 Large string input is handled [NOT_TESTED]

```
summary: 0 tested, 1 skipped; at least one planned probe was skipped.
reason: valid input could not be generated for a huge string
evidence 1 subject: probe CT-ROB-004 tool[-1] tools/list huge_string
evidence 1 detail: {"tool":"tools/list","phase":"huge_string","outcome":"skipped","reason":"valid input could not be generated for a huge string"}
evidence 2 subject: coverage
evidence 2 detail: 0 tested, 1 skipped
```

### CT-ROB-005 Valid read-only call succeeds [NOT_TESTED]

```
summary: 0 tested, 1 skipped; at least one planned probe was skipped.
reason: valid input could not be generated for this tool
evidence 1 subject: probe CT-ROB-005 tool[0] fetch valid_call
evidence 1 detail: {"tool":"fetch","phase":"valid_call","outcome":"skipped","reason":"valid input could not be generated for this tool"}
evidence 2 subject: coverage
evidence 2 detail: 0 tested, 1 skipped
```

### CT-CANARY-001 Canary values are absent from tool answers [NOT_TESTED]

```
summary: Check was not tested.
reason: robustness checks: 0 failed, 2 not tested; tools/call answers scanned: 3
```
