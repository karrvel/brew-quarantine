---
name: log
type: reference
title: Event log — what happened, in order
area: cross
tags: [log]
status: active
updated: 2026-11-09
volatility: durable
provenance: appended by hand
---

# Log

## 2026-08-27 — first build and first leak

- Established that Homebrew has no user-facing cooldown. Its built-in `RELEASE_COOLDOWN_DAYS` is `1` and applies only to maintainers resolving npm/PyPI/cargo resources at build time. Upstream closed the user-facing request as *not planned* (Homebrew/brew#21421).
- Chose a plan-filtering gate over pinning taps to an old commit ([[gate-wrapper-not-tap-time-travel]]).
- Established the age signal by measurement: the OCI bottle timestamp is unusable, the formula file's commit date is not ([[age-signal-formula-commit-date]]).
- Three parsing bugs found and fixed by controls, not by inspection: stderr prose parsed as packages, bare versions parsed as packages, and the transitively-held set measured against the wrong baseline.
- **First real `brew upgrade` through the gate leaked.** 40 packages cleared, 34 passed to `brew`, and Homebrew additionally installed `glib`, `ffmpeg`, `x265` and `simdjson` — all explicitly held — as dependencies of `mpv`, which entered the plan as a dependent. `--dry-run` never listed them. Found by reading `INSTALL_RECEIPT.json` timestamps, not by any check the tool ran. Fixed by unioning the outdated dependency closure into every resolved plan ([[dry-run-under-reports-dependent-deps]]).
- Post-fix, the independent closure assertion holds and the cleared set is correctly far more conservative.

## 2026-11-09 — no-op bucket and the receipt audit

- **No-op packages get their own bucket.** A requested package whose own plan is empty is now reported as *nothing to do* instead of *held transitively — blocked by: a held dependency*. The mislabel had three sources, not just the isolation fallback: the fixed point breaking out on an empty plan, and a no-op requested alongside real work. This also closed a fail-open path: a dry-run that parsed to an empty plan used to hand every candidate to `brew` unaged; now it runs nothing and reports them all as nothing to do, which on `upgrade` means the parser broke. Residual: a candidate blocked by a held *dependent* still gets the unattributed label ([[isolate-clean-drops-empty-plans]]).
- **`--audit` shipped.** Each real run writes `last-run.json` (window plus cleared set) next to the date cache, and `--audit` diffs Cellar `INSTALL_RECEIPT.json` times inside that window against it. Receipts measured on the development machine store `time` as integer epoch seconds ([[verify-against-real-run-not-self-report]]).
- **First test file.** `test_brew_quarantine.py` is stdlib-only and replaces every Homebrew call with a fake. The no-op tests fail on the previous release and pass now; the audit is tested against a fixture Cellar. The task's original real-run acceptance is **still owed**: one gated run by the owner, then `--audit`.
