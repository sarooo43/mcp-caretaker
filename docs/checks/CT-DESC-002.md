# CT-DESC-002 — Description length is within limits

## What it checks
The stripped tool-level description length. The minimum is 10 characters; this number is a guess; it lives in thresholds.py. The maximum is 1000 characters; this number is a guess; it lives in thresholds.py. Both ends are inclusive.

## Why it matters
Very short or very long descriptions can be unhelpful to a client. The boundaries are deliberately modest and easy to change in one file.

## Verdict
`pass`: all descriptions are within both limits. `warn`: one or more descriptions are outside the limits. `not_tested`: with a reason when `tools/list` or startup failed. `not_tested` is never counted or displayed as pass.

## How to fix
Write a concise description between the two limits.

## Limits
Length is measured in Unicode code points after `strip()`, not display width or rendered size. Property descriptions are not measured here.
