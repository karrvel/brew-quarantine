---
name: dependency-closure-is-the-whole-problem
type: gotcha
title: Gating only the named packages is decorative — brew upgrade pulls in deps and dependents
area: core
tags: [dependencies, dry-run, fixed-point]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session — measured with `brew upgrade --dry-run ffmpeg`
---

# A cooldown that only ages what you typed protects nothing

`brew upgrade ffmpeg` does not upgrade ffmpeg. Measured output: three dependencies (`mpg123`, `sdl3`, `x265`) plus **two** outdated packages — `ffmpeg` and `mpv`, which was never mentioned. Six packages touched from a one-package request. Any of the five you did not name could be the freshly published one, so a gate that checks only the named package leaks by design.

The fix is to treat `brew <action> --dry-run` as the authority on what will be touched, age every member of that set, then shrink to a fixed point: drop violators, drop every candidate whose dependency closure contains a violator, re-resolve, repeat. Dependents must be computed per kind — `brew deps --for-each --formula` errors out if a cask token is in the list, and a silent failure there returns an empty dependent set and stalls the loop.

The loop is backstopped two ways: per-candidate isolation if it stalls (see [[isolate-clean-drops-empty-plans]]), and a final re-resolve that asserts nothing in the surviving plan is inside the cooldown, exiting `2` if it is. That final assertion is the check that actually catches a leak — a unit test of the date lookup cannot.

Related: [[transitive-hold-measured-against-plan]].
