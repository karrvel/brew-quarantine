---
name: verify-against-real-run-not-self-report
type: task
title: Add a post-run receipt audit that compares what was installed against what was cleared
area: testing
tags: [testing, verification, leak]
status: resolved
updated: 2026-11-09
volatility: durable
provenance: 2026-08-27 — the dependent-dependency leak was found this way, by hand
---

# The gate needs a check it cannot pass by agreeing with itself

The dependent-dependency leak ([[dry-run-under-reports-dependent-deps]]) survived every test the tool ran on itself. The fixed point converged, the buckets were disjoint and summed correctly, and the built-in final verification reported no violation — all while four held packages were being installed. Every one of those checks was derived from the same `--dry-run` output that was itself incomplete, so they agreed with each other and were all wrong together.

What actually caught it was external evidence: Homebrew's `INSTALL_RECEIPT.json` files carry an install timestamp, and `glib` had one inside the run window while the report listed it as held.

**The work:** a `--audit` mode that, after a real run, walks `/opt/homebrew/Cellar/*/*/INSTALL_RECEIPT.json`, collects every keg installed since the run started, and diffs that against the cleared set. Anything installed but not cleared is a leak and should exit non-zero. Acceptance: deliberately reintroduce the pre-fix behaviour (drop `expand_with_outdated_deps`) and confirm the audit fails.

This is the highest-value remaining work, because it is the only proposed check whose evidence is independent of the tool's own model of what brew will do.

## Resolution (2026-11-09)

**Design.** The tool already persisted one thing, the date cache beside `dates.json`, so the run receipt goes next to it: `cmd_gate` writes `last-run.json` (`action`, `started`, `finished`, `cleared`) in a `finally` around the real `brew` call, so an interrupted run is still recorded. `started` is taken just before `brew` executes, because the gate installs nothing earlier. `finished` is rounded up a second because install receipts store whole epoch seconds. `cleared` is the full aged plan, dependencies included, not just the survivors handed to `brew`. `brew-quarantine --audit` (main parser only; no subcommand) reads it, walks `<cellar>/*/*/INSTALL_RECEIPT.json`, keeps kegs whose `time` is inside `[started, finished]`, and diffs their names against `cleared`, comparing short names because the dry-run may tap-qualify them. Exit `2` on a leak (the same meaning as the gate's own verification failure), `1` when there is nothing to audit, `0` clean. The Cellar defaults to `brew --cellar` and `BREW_QUARANTINE_CELLAR` overrides it. `--dry-run`, `--json` and `--bypass` runs never execute through the gate, so they write no receipt.

**Receipt format, measured 2026-11-09** on this tool's development machine (read-only, Homebrew 6.0.x): all 323 Cellar receipts carry `time` as an integer of epoch seconds (e.g. `1793119329`); `source_modified_time` is a different field and is not the install time. A synthetic run window placed over a real install on 2026-11-08 made `--audit` report exactly that keg against the real Cellar.

**Acceptance was replaced.** The original acceptance, to drop `expand_with_outdated_deps` again and confirm the audit fails on a real run, would mean installing software on purpose, which is the owner's decision and not a test. It was replaced by fixture tests in `test_brew_quarantine.py`: a synthetic Cellar where a keg installed inside the window and cleared passes, one installed inside the window and not cleared fails with exit 2, and one installed before the window is ignored. The leak case goes through `cmd_gate` with a fake `brew` that writes receipts, so the round trip from run to receipt to audit is covered. Removing the time-window check makes two of those tests fail. **Still needed: one real gated run by the owner, followed by `brew-quarantine --audit`.**

**Known limits, for that real run to confirm or correct:**
- Casks are not audited. `Caskroom/<token>/.metadata/INSTALL_RECEIPT.json` carries the same integer `time` field, so adding them is one more glob, but it is outside this task.
- Only the most recent run is recorded; each real run overwrites `last-run.json`.
- Any other keg installed inside the window (another terminal, a scheduled job) is reported as a leak. That is the safe direction to be wrong in.
- Not verified: whether Homebrew's post-upgrade reinstall of broken dependents writes fresh receipts. If it does, those kegs will be flagged even though they were not new releases. The first real run will show it.
- An unreadable receipt is skipped rather than flagged (marked `shortcut:` in the code).
