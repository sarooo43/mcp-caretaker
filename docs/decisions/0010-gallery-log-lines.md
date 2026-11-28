# 0010 - One log line per gallery case

PR 8c adds one printed line per gallery case plus two documentation changes. It
changes no `src/` file, no verdict, no probe selection, no threshold, no check ID,
no workflow file and no dependency, and the test count stays 211.

`pytest -q` printed one dot per gallery case, so a reader of the CI log could see
that the runs passed but not which fixture produced which result. The owner asked
for the expected result and the actual result of every gallery case to be visible
in that log.

## T0 findings (before any change)

- Repo state VERIFIED: the checkout's local base was a one-file stub commit, so
  the branch base was aligned to `origin/main` (`3847d93`, "Merge pull request
  #8") with a hard reset before any edit. `git status --porcelain` was then
  empty.
- Test count VERIFIED: `pytest --collect-only -q` reported `211 tests collected`.
- Gallery size VERIFIED: the `## Bad servers` table in `docs/gallery.md` has 33
  data rows, which is the number of cases the parametrized test builds.
- CI output VERIFIED: `.github/workflows/ci.yml` runs `pytest -q` in the `test`
  job with no capture flag, and `capsys.disabled()` writes to the real stdout, so
  the printed lines reach the job log without a workflow change. A local
  `pytest -q tests/test_gallery.py` run showed all 33 lines between the dots.

## D1 to D4 - what the line is

- One line per row of the existing parametrized test, printed before the verdict
  assertion, inside `capsys.disabled()`.
- Shape: `gallery: <fixture> | expected <ID> <verdict> | got <ID> <verdict> | OK`,
  and `MISMATCH` in place of `OK` when the two sides differ. A row with several
  expected checks lists them comma separated, sorted by check ID.
- The expected side is `_expected(row)`, the same data the assertion compares, so
  there is no second data source.
- Only the fixture file name, the check IDs and the verdicts are printed: no
  evidence text, no paths, no environment values and no argv.
- The text is ASCII only, with no tick marks or emoji, because a Windows console
  code page mangled non-ASCII output in an earlier PR.
- The assertions are unchanged and the test count is unchanged.

## Mutation proof

- Wrong expected verdict: the `bad_no_descriptions.py` row of `docs/gallery.md`
  was changed from `CT-DESC-001:warn` to `CT-DESC-001:fail`, and
  `pytest -q tests/test_gallery.py -k bad_no_descriptions` went red with
  `1 failed, 35 deselected`. Its printed line was
  `gallery: bad_no_descriptions.py | expected CT-DESC-001 fail | got CT-DESC-001 warn | MISMATCH`,
  so the line shows the mismatch and is written before the assertion fires.
- Restore: the row was put back and the same selection went green with
  `1 passed, 35 deselected` and the line ending in `| OK`.
- Missing print: the print block was removed and
  `pytest -q tests/test_gallery.py` printed 36 dots and `36 passed in 41.98s`
  with zero `gallery:` lines in the output. The block was restored afterwards.
