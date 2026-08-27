---
name: verify-against-real-run-not-self-report
type: task
title: Add a post-run receipt audit that compares what was installed against what was cleared
area: testing
tags: [testing, verification, leak]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 — the dependent-dependency leak was found this way, by hand
---

# The gate needs a check it cannot pass by agreeing with itself

The dependent-dependency leak ([[dry-run-under-reports-dependent-deps]]) survived every test the tool ran on itself. The fixed point converged, the buckets were disjoint and summed correctly, and the built-in final verification reported no violation — all while four held packages were being installed. Every one of those checks was derived from the same `--dry-run` output that was itself incomplete, so they agreed with each other and were all wrong together.

What actually caught it was external evidence: Homebrew's `INSTALL_RECEIPT.json` files carry an install timestamp, and `glib` had one inside the run window while the report listed it as held.

**The work:** a `--audit` mode that, after a real run, walks `/opt/homebrew/Cellar/*/*/INSTALL_RECEIPT.json`, collects every keg installed since the run started, and diffs that against the cleared set. Anything installed but not cleared is a leak and should exit non-zero. Acceptance: deliberately reintroduce the pre-fix behaviour (drop `expand_with_outdated_deps`) and confirm the audit fails.

This is the highest-value remaining work, because it is the only proposed check whose evidence is independent of the tool's own model of what brew will do.
