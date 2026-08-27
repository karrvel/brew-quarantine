---
name: cache-dates-never-verdicts
type: decision
title: Cache the date a revision landed, never the pass/fail verdict
area: core
tags: [cache, correctness]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session
---

# The cache stores facts, not decisions

Resolved dates are cached under `~/.cache/brew-quarantine/dates.json`, keyed by `(tap, ruby_source_path, version)`. The key includes the version so a new revision is a cache miss and gets a fresh lookup.

What is deliberately **not** cached is the outcome of the comparison. Caching "blocked" would let a decision outlive the window that justified it: a package held at day 2 would stay held forever, or until someone thought to clear the cache. Storing only the landing date means the same cached fact yields "held" today and "cleared" next week, with no expiry logic to get wrong.

This also keeps the cache cheap to reason about — entries are immutable once written, so there is no invalidation, only accumulation.
