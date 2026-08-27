---
name: transitive-hold-measured-against-plan
type: gotcha
title: Compute the transitively-held set against the final plan, not the candidate set
area: reporting
tags: [reporting, accounting]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session — caught by a disjointness check on the output buckets
---

# A package can be upgraded without ever having been a candidate

Requested packages that are neither cleared nor directly held were dropped because they depend on something inside the cooldown, and reporting them matters — otherwise they vanish and the run looks like it covered more than it did.

The first implementation computed that set as `requested - candidates - held`. Wrong: Homebrew pulls **dependents** of a candidate into the plan, so a package can be upgraded without having been a candidate. Six packages were consequently listed as "held transitively — blocked by a held dependency" while simultaneously appearing in the cleared list and being upgraded.

Measuring against the final plan instead — `requested - plan - held` — fixes it. The invariant worth asserting in any future change: **cleared, held, held-transitively and skipped must be pairwise disjoint and must sum to the number of packages requested.** That check is what surfaced the bug; the report looked entirely plausible without it.

Related: [[dependency-closure-is-the-whole-problem]].
