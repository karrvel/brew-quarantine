---
name: brew-quarantine-repo
type: repo
title: brew-quarantine — the tool, its layout and how to work on it
area: cross
tags: [repo, layout]
status: active
updated: 2026-11-09
volatility: decays-with-code
provenance: 2026-08-27 — first public release
---

# The repository

```
brew-quarantine          the entire tool — one Python file, no third-party imports
test_brew_quarantine.py  stdlib self-tests; never runs brew
README.md                user-facing documentation
_knowledge/              this vault
```

Deliberately a single file. It has to be installable with a `curl` and a `chmod`, and it has to run under whatever `python3` macOS ships, because a tool that guards installs should not itself need an install step with dependencies.

## Working on it

There is no build. `python3 -m unittest -v test_brew_quarantine` runs the stdlib self-tests, which replace every Homebrew and network call with a fake world (and patch `subprocess.run` to fail if anything slips through), so they are safe to run on a machine that matters. They cover the logic, not Homebrew's behaviour. The checks that need a real Homebrew are run by hand:

- **Positive control** — a package whose definition changed in the last few days must be held. `brew-quarantine --dry-run install <recently-bumped-cask>`.
- **Negative control** — a long-untouched package must clear.
- **Closure assertion** — the dependency closure of the cleared set, intersected with `brew outdated`, must be a subset of the cleared set. This is the check that catches leaks.
- **Bucket accounting** — cleared, held, held-transitively and skipped must be disjoint and sum to the request.

The gap in all of these is that they read the same `--dry-run` the tool reads. [[verify-against-real-run-not-self-report]] tracks the independent check that is still missing.

## Conventions

Comments explain *why*, especially where the code compensates for a Homebrew behaviour that is not obvious — those comments are load-bearing and the corresponding vault shard should be updated alongside any change to them.
