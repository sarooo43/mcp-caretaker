# 0002 - The child environment

The launcher starts from an EMPTY environment and adds only an allow-list. Nothing
else from the parent is inherited. `extra_env` is added last and may override any
allow-listed name.

## Allow-list

- `PATH` on every platform (copied from the parent).
- On Windows only: `SYSTEMROOT`, `COMSPEC`, `PATHEXT` (copied from the parent).
- `TEMP`, `TMP`, and on POSIX `TMPDIR`: set to our own temp folder, never copied
  from the parent.
- On POSIX only: `LANG` and `LC_ALL`, but only if they are present in the parent.
- No `HOME`, no `USERPROFILE`, no `APPDATA`, no `LOCALAPPDATA`, no `USER`, no
  `SHELL`, no `LOGNAME`, and no arbitrary parent variables.

`build_child_env()` in `src/mcp_caretaker/launch.py` is the whole implementation.

## Real minimum found by experiment

- VERIFIED (ran `fallback_experiment.py` in `docs/decisions/0001-evidence/` on
  Debian 12, CPython 3.11.2): a plain `python <fixture_server.py>` MCP server
  started, completed the MCP handshake and answered `tools/list` with ONLY
  `PATH`, `TEMP`, `TMP`, `TMPDIR` (plus `LANG` / `LC_ALL` when present in the
  parent). No extra parent variable was needed, so **no additional variable was
  added "just in case"**.
- The child's `env_names()` also shows `LC_CTYPE` on this OS. That name is not in
  our allow-list: CPython adds it itself at interpreter startup (locale coercion)
  when the parent locale variables are absent. It is not inherited from the
  parent and contains no parent value.
- Windows env stripping and Windows process-tree kill are NOT VERIFIED locally;
  CI on `windows-latest` (Python 3.11 and 3.13) is the evidence for those. The
  Windows allow-list entries are the ones the official SDK uses to start Python,
  restricted to the names above.

## Working directory

A fresh temp area is created per session. Inside it, `cwd/` is an empty folder and
is the child's working directory; `stderr.log` lives in the temp area, not in
`cwd/`. That keeps the child's cwd genuinely empty while it runs, and lets tests
assert it. The temp area (including `cwd/`) is removed on exit. Relative script
paths in `argv` are NOT rewritten, so use absolute paths for scripts.

## `extra_env` values are secrets by default

- `LaunchSpec.__repr__` / `__str__` show only the NAMES of `extra_env`.
- `redact_values()` replaces every occurrence of each value with
  `[REDACTED:NAME]` in captured stderr, in `ServerExited.stderr_tail` and in our
  error messages. Longer values are replaced first so overlapping values cannot
  leave a partial value behind.
- **Limit:** values shorter than 4 characters are NOT replaced (a one- or
  two-character value would redact ordinary text such as "1" or "/"). Callers
  must not put short secrets in `extra_env`. This is deliberate and documented in
  `launch.py`.
- Because the stderr cap keeps only the last 64 KiB, a very long value that is
  split by that cut cannot be fully matched. The fixture server writes large
  non-secret padding *before* the secret so the tail still contains the whole
  value and redaction applies to it.
