---
name: isolate-clean-drops-empty-plans
type: task
title: isolate_clean() silently drops candidates that resolve to an empty plan, mislabelling them as blocked
area: reporting
tags: [reporting, bug, cosmetic]
status: active
updated: 2026-08-27
volatility: decays-with-code
provenance: 2026-08-27 build session — known at time of first release
---

# A no-op candidate is reported as "blocked by a held dependency"

In the stall fallback, `isolate_clean()` skips any candidate whose own `--dry-run` resolves to an empty plan (`if not plan: continue`). Those candidates never enter the survivor set, so the reporting step — which classifies anything requested but not in the final plan and not directly held as *held transitively* — labels them "blocked by: a held dependency". Nothing blocked them; there was simply nothing to do.

The gate's decisions are unaffected: a package with an empty plan would be a no-op for `brew` either way, and the bucket accounting still balances because the buckets are computed by set difference. Only the label is wrong, which makes this cosmetic rather than a correctness issue — but a misleading label in a security tool's report is worth removing.

**The work:** track empty-plan candidates in their own set and report them as *nothing to do* rather than folding them into the transitively-held bucket. Acceptance: no package appears under a "blocked by" line without at least one genuine held dependency named.

Related: [[transitive-hold-measured-against-plan]].
