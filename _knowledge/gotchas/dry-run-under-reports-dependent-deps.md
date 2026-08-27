---
name: dry-run-under-reports-dependent-deps
type: gotcha
title: brew --dry-run omits the dependencies of packages that enter the plan as dependents — this leaked the gate in production
area: core
tags: [dependencies, dry-run, leak, regression]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 — observed on a live `brew upgrade` run; confirmed against install receipts
---

# `--dry-run` is not a complete account of what brew will install

The gate was built on the assumption that `brew <action> --dry-run` enumerates everything Homebrew will touch. It does not, and the gap let held packages through on a real run.

`brew upgrade` pulls **dependents** into the plan: upgrading a set that never mentioned `mpv` still upgraded `mpv`, and `--dry-run` correctly reported that. But it did **not** report `mpv`'s own outdated dependencies. When the real command ran, Homebrew upgraded `glib`, `ffmpeg`, `x265` and `simdjson` — all of which the gate had explicitly held as too new — because they are dependencies of `mpv`, which was in the plan. None appeared anywhere in the dry-run output, so the age check never saw them and the final verification passed on an incomplete set.

Install receipts are the ground truth that exposed it: `glib` 2.88.3 carried an install timestamp inside the run window while the report listed `glib` under HELD.

**The fix:** never treat the dry-run plan as closed. After parsing it, union in the recursive dependency closure of every plan member intersected with the currently-outdated set (`brew deps --union`, split by `--formula` / `--cask`), because `brew upgrade X` always upgrades X's outdated dependencies. `expand_with_outdated_deps()` does this on every `resolve_plan()` call, so the fixed point, the isolation fallback and the final verification all age the same complete set.

**The lesson that generalises:** verify against what the system actually did (install receipts, real state) rather than against the tool's own report. The tool's self-verification agreed with itself and was wrong. See [[verify-against-real-run-not-self-report]].

Related: [[dependency-closure-is-the-whole-problem]].
