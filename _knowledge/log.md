---
name: log
type: reference
title: Event log — what happened, in order
area: cross
tags: [log]
status: active
updated: 2026-08-27
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
