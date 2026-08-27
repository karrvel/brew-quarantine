---
name: tap-trust-hides-third-party-taps
type: gotcha
title: Homebrew 6 tap trust makes untrusted taps invisible — their packages cannot be aged or upgraded
area: integration
tags: [homebrew-6, tap-trust]
status: active
updated: 2026-08-27
volatility: decays-with-code
provenance: 2026-08-27 build session — observed on Homebrew 6.0.20
---

# Untrusted taps are ignored by brew, so they stall a naive fixed point

Homebrew 6 introduced tap trust: packages from third-party taps are ignored until explicitly trusted via `brew trust`. On a machine with a dozen taps this silently removes their formulae and casks from `brew upgrade` entirely, and the warning is a wall of prose on stderr (which is its own parsing hazard — see [[dry-run-parse-stdout-only]]).

For the gate this creates a specific failure. Such packages appear in `brew outdated` but `brew info` cannot resolve them, so they have no metadata and no age. As violators they can never be dropped by the fixed-point loop — nothing in the candidate set depends on them — so the loop cannot shrink and stalls, holding everything.

The handling is to detect unresolvable packages **before** the loop starts and set them aside as *skipped*, with a note pointing at `brew trust`. That is honest about coverage without pretending they were protected, and it avoids granting trust as a side effect, which is a decision for the operator rather than for a tool.

Marked decays-with-code: tap trust is new and its behaviour and messaging are likely to change.
