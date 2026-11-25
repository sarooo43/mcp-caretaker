"""One place for check thresholds. These numbers are guesses; docs say so."""

# Guessed minimum description length after strip; docs say it is a guess.
DESC_MIN_LENGTH = 10
# Guessed maximum description length after strip; docs say it is a guess.
DESC_MAX_LENGTH = 1000
# Guessed horizontal whitespace run limit; docs say it is a guess.
WHITESPACE_RUN_LIMIT = 40
# Guessed cap on tools/list pages; docs say it is a guess.
MAX_TOOLS_PAGES = 10
# Guessed cap on evidence items; docs say it is a guess.
EVIDENCE_MAX_ITEMS = 20
# Guessed cap on each evidence string; docs say it is a guess.
EVIDENCE_MAX_CHARS = 300
# Guessed grace period for a child to exit after stdin closes; docs say it is a guess.
SHUTDOWN_GRACE_SECONDS = 5
# Guessed length of the one large string probe; docs say it is a guess.
HUGE_STRING_LENGTH = 1_048_576
# Guessed cap on tools that receive probes; docs say it is a guess.
MAX_TOOLS_PROBED = 50
# Guessed wall-clock budget for all probes; docs say it is a guess.
PROBE_BUDGET_SECONDS = 120
# Guessed cap on a constructed replay line; docs say it is a guess.
REPLAY_MAX_CHARS = 2000
# Guessed cap on stderr bytes scanned from the start; docs say it is a guess.
STDERR_SCAN_MAX_BYTES = 1_048_576
