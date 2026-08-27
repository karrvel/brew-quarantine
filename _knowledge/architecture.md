---
name: architecture
type: architecture
title: How brew-quarantine decides what may be installed
area: cross
tags: [architecture, overview]
status: active
updated: 2026-08-27
volatility: decays-with-code
provenance: 2026-08-27 — describes `brew-quarantine` at first public release
---

# System model

`brew-quarantine` is a single dependency-free Python executable that sits in front of `brew install` and `brew upgrade`. It answers one question — *is everything this command would install at least N days old?* — and re-runs `brew` with a reduced package list if the answer is no.

## The pipeline

```
requested ──▶ resolve ──▶ age ──▶ shrink (fixed point) ──▶ verify ──▶ execute
                 ▲                      │
                 └──────────────────────┘
```

1. **Resolve** — `brew <action> --dry-run` gives the packages Homebrew would touch. Its output is parsed from stdout only, then **expanded** with the outdated recursive dependency closure of every plan member, because the dry-run omits the dependencies of packages that enter the plan as dependents ([[dry-run-under-reports-dependent-deps]]).
2. **Age** — each package's `.rb` file path comes from `ruby_source_path`; its last commit date comes from the GitHub API for official taps and from `git log` for local ones ([[age-signal-formula-commit-date]]).
3. **Shrink** — drop violators plus every candidate whose dependency closure contains one, re-resolve, repeat. Per-candidate isolation is the fallback if it stalls.
4. **Verify** — re-resolve the survivors and assert the final plan contains nothing inside the cooldown. Exit `2` if it does.
5. **Execute** — hand the survivors to `brew` with `HOMEBREW_NO_AUTO_UPDATE=1`, so the version that was aged is the version installed.

## Output contract

Every requested package lands in exactly one of four buckets — **cleared**, **held**, **held transitively**, **skipped** — which are pairwise disjoint and sum to the request. A fifth annotation, *cannot fully enforce*, marks cleared casks whose payload is not pinned ([[cannot-enforce-unpinned-casks]]). The disjointness invariant is load-bearing: it is what caught a real reporting bug ([[transitive-hold-measured-against-plan]]).

## Trust boundaries

The tool trusts Homebrew's metadata and the GitHub API for dates. It does **not** trust `--dry-run` to be a complete account of what will be installed — that assumption caused a production leak and is now compensated for explicitly. It makes no judgement about whether a release is malicious; it only delays adoption.

## Integration

A thin `zsh` function routes the two gated subcommands to the executable and leaves everything else to `command brew`. Because the file is named `brew-quarantine` on `PATH`, Homebrew also dispatches `brew quarantine …` natively. Coverage limits are documented in [[wrapper-coverage-holes]].
