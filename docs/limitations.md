# Limits

This page lists what mcp-caretaker does, what it does not do, and where the
guesses are. Every statement here matches code or a decision record in this
repository.

## What this tool is and is not

It is a runtime behaviour tester for **local MCP servers started over stdio**. It
starts the server you name, completes the current SDK handshake, sends a small
fixed set of requests, and reports what it observed as facts with evidence.

It is not a source-code scanner, not a static analyser, and not a replacement
for one. It only sees what a running server does in one short session on this
machine. It complements static tools: they read code, this tool reads behaviour.

## Running a server executes its code

Starting a server runs real code on your machine with your user account. This
tool is not a sandbox, offers no isolation, and makes no security guarantee.
`--trust` exists to make that explicit before anything starts.

What the launcher does: it builds the child environment from an empty base plus a
small allow-list (`PATH`; on Windows also `SYSTEMROOT`, `COMSPEC` and `PATHEXT`;
on POSIX `LANG` and `LC_ALL`; `TEMP`, `TMP` and `TMPDIR` point at the run folder;
your `--env` values are added last), it starts the server in a fresh temporary
folder (`mcp-caretaker-*`, with the working directory under it), and on exit it
terminates the child and the process group it started.

What it does not do: it does not stop the server from reading files outside that
folder, from using the network, from spawning other processes, or from writing
anywhere your account can write. A server that wants to change the machine can.

## A pass is not a safety guarantee

A run with 25 `pass` results means the observed behaviour matched the 25 rules in
this version. It does not mean the server is safe, correct, or trustworthy. A
server can pass every check and still do something this tool never looks at.

## Read-only hints are hints

A tool that declares `readOnlyHint` as exactly JSON `true` receives a real
`tools/call` with generated valid input, and a large string is sent to it as
well. The hint is a claim by the server, not a guarantee: a server can declare it
and still write files or change state. Only test servers you trust.

## What is not checked at all

- HTTP and other non-stdio transports.
- OAuth, authentication and authorisation.
- Full protocol conformance.
- Server source code.
- Instruction-like text in descriptions.
- Side effects: files written, network used, state changed.
- LLM behaviour, prompts or model output.

## Canary limits

- Only three names are planted: `CARETAKER_CANARY_API_KEY`,
  `CARETAKER_CANARY_TOKEN` and `CARETAKER_CANARY_SECRET`.
- For each planted value, only the value itself and the standard base64 of that
  value on its own are searched for. Other encodings are not generated.
- There is no suppress option, so a deliberate environment-dumping tool is
  always reported.
- Stderr is read from the start of each session up to a per-session cap of
  `STDERR_SCAN_MAX_BYTES = 1048576` bytes. Bytes past that cap in one session are
  not scanned.
- A server can hide a planted value by splitting it, encoding it differently, or
  writing it past the cap.

## Stability limits

- Comparison uses two connections plus one listing after the probes: the first
  session's listing, a second session's listing, and the final liveness listing.
- Only `title`, `description`, `inputSchema`, `outputSchema` and `annotations`
  are compared, by tool name. Order, top-level `_meta` and icons are ignored.
- Changes triggered by time, by a call count, or by specific arguments are not
  caught unless one of those three reads happens to see them.
- Both sessions in one run share the same temporary folder, so a server can keep
  state there between them.

## Robustness limits

- The probe set is fixed: one wrong-type call, one call missing a required
  property, one call for an unknown tool name, one large string and one generated
  valid call per eligible tool, then one liveness `tools/list`.
- At most `MAX_TOOLS_PROBED = 50` tools receive probes and the probe phase stops
  at `PROBE_BUDGET_SECONDS = 120` seconds. Skipped probes are reported as
  `not_tested` or counted as skipped coverage, never as pass.
- The large string and the valid call are only sent to tools whose raw
  `readOnlyHint` is exactly `true`.
- Coverage is partial: one input shape per tool is not a thorough test.
- All thresholds in `src/mcp_caretaker/thresholds.py` are guesses, not
  measurements: `DESC_MIN_LENGTH = 10`, `DESC_MAX_LENGTH = 1000`,
  `WHITESPACE_RUN_LIMIT = 40`, `MAX_TOOLS_PAGES = 10`, `EVIDENCE_MAX_ITEMS = 20`,
  `EVIDENCE_MAX_CHARS = 300`, `SHUTDOWN_GRACE_SECONDS = 5`,
  `HUGE_STRING_LENGTH = 1048576`, `MAX_TOOLS_PROBED = 50`,
  `PROBE_BUDGET_SECONDS = 120`, `REPLAY_MAX_CHARS = 2000` and
  `STDERR_SCAN_MAX_BYTES = 1048576`.

## Reports

- Server arguments are never written to the JSON, Markdown or terminal report.
- A server can print its own arguments or any other text on stdout or stderr, and
  the report then shows that text, because it is the server's output.
- Server text is escaped for the terminal and fenced in Markdown, but it stays
  untrusted text: it is never executed and never used as a path.
- There is no score and no grade. Findings are facts with evidence, not
  statements of intent.

## Platforms and versions

- CI runs Linux and Windows on Python 3.11 and 3.13.
- macOS and other platforms are not tested.
- The MCP SDK is pinned to one exact version for now (`mcp==2.3.0`,
  `mcp-types==2.3.0`), so behaviour against other SDK versions is unknown.
- The version of this tool is a pre-release `0.0.0.dev0`.

## Exit codes

- `0`: no failing check, and no warning when `--fail-on warn` is given.
- `1`: at least one failing check, or at least one warning with `--fail-on warn`.
- `2`: usage error, output that cannot be written, or an unexpected internal
  error.
- `not_tested` never changes the exit code.
