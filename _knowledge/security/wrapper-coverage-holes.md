---
name: wrapper-coverage-holes
type: security
title: A zsh wrapper covers interactive shells only — brew bundle, cron and CI bypass the gate
area: integration
tags: [coverage, shell, honesty]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session
---

# The gate is opt-in per call site, and most call sites are not the shell

The shell function that routes `brew install` / `brew upgrade` through the gate only exists inside an interactive `zsh`. Everything else reaches Homebrew directly: `brew bundle`, wrapper tools that shell out to the real `brew`, cron jobs, CI, scripts, and any editor or agent invoking `brew` non-interactively.

Two design consequences follow. The logic ships as a **standalone executable** rather than living inside the shell function, so non-interactive call sites have something they can call. And the wrapper is a *caller*, not a `PATH` shadow — shadowing `brew` with a script of the same name invites recursion and breaks `command brew` as a predictable escape hatch.

Anyone treating this as a control rather than a convenience should verify which paths on their machine actually route through it, and consider invoking `brew-quarantine` directly from automation.

Related: [[cannot-enforce-unpinned-casks]], [[tap-trust-hides-third-party-taps]].
