---
name: gate-wrapper-not-tap-time-travel
type: decision
title: Implement the cooldown as a plan-filtering gate, not by pinning taps to an old commit
area: core
tags: [architecture, alternatives]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session
---

# A gate that filters the plan, not a tap pinned to the past

The alternative design was tap time-travel: set `HOMEBREW_NO_INSTALL_FROM_API=1`, clone `homebrew/core` and `homebrew/cask` as git taps, and after each `brew update` reset them to the newest commit at least *N* days old. Homebrew then sees the world as it was a week ago and every resolved version is old enough — complete dependency coverage, for free, with no per-package date lookups.

It was rejected on three counts. The full clones cost gigabytes on a machine where disk is not guaranteed spare. `HOMEBREW_NO_INSTALL_FROM_API=1` is the less-travelled code path, and Homebrew 6 changed how core taps are materialised (`use_worktree_source_tap` in `tap.rb`), so 4.x-era recipes no longer describe the behaviour. Most importantly it is opaque: the user sees "already up to date" with no indication anything was withheld, and no per-package override.

The gate keeps Homebrew's fast default API path, reports exactly what was held and when each item clears, and leaves `command brew …` as an unambiguous escape hatch. The cost is that dependency closure must be computed explicitly — which is the hard part, see [[dependency-closure-is-the-whole-problem]].
