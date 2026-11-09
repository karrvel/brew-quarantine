---
name: isolate-clean-drops-empty-plans
type: task
title: isolate_clean() silently drops candidates that resolve to an empty plan, mislabelling them as blocked
area: reporting
tags: [reporting, bug, cosmetic]
status: resolved
updated: 2026-11-09
volatility: one-shot
provenance: 2026-08-27 build session — known at time of first release
---

# A no-op candidate is reported as "blocked by a held dependency"

In the stall fallback, `isolate_clean()` skips any candidate whose own `--dry-run` resolves to an empty plan (`if not plan: continue`). Those candidates never enter the survivor set, so the reporting step — which classifies anything requested but not in the final plan and not directly held as *held transitively* — labels them "blocked by: a held dependency". Nothing blocked them; there was simply nothing to do.

The gate's decisions are unaffected: a package with an empty plan would be a no-op for `brew` either way, and the bucket accounting still balances because the buckets are computed by set difference. Only the label is wrong, which makes this cosmetic rather than a correctness issue — but a misleading label in a security tool's report is worth removing.

**The work:** track empty-plan candidates in their own set and report them as *nothing to do* rather than folding them into the transitively-held bucket. Acceptance: no package appears under a "blocked by" line without at least one genuine held dependency named.

Related: [[transitive-hold-measured-against-plan]].

## Resolution (2026-11-09)

No-op candidates now have their own bucket, `noop`, reported as **NOTHING TO DO** (`nothing_to_do` in `--json`). Three paths feed it, because the same mislabel had three sources:

- `isolate_clean()` returns `(kept, noop)` — the empty-plan branch records the candidate instead of dropping it silently.
- The main fixed-point loop: when the remaining candidates resolve to an empty plan (`install` of something already installed), they all move to `noop` and the candidate set is emptied, so `brew` is no longer invoked on a no-op list.
- After final verification, any surviving candidate absent from the final plan (a no-op requested alongside real work) is a no-op too.

`pending` (the held-transitively input) now excludes `noop`, and the plan is compared by short name in case the dry-run tap-qualifies a name. `test_brew_quarantine.py` covers all three paths and asserts the five-bucket partition; all three tests fail on the pre-fix script (`6cd0608`) and pass after.

**Residual — the fallback label is not gone.** `implicit[n]` is built from `brew deps --for-each`, which lists dependencies only. A candidate dropped because a held *dependent* enters its plan (the mpv pattern in [[dry-run-under-reports-dependent-deps]]) — which is exactly what makes the fixed point stall — still prints `blocked by: a held dependency` with nothing named. So do candidates dropped when the gate fails to converge, when final verification fails, or when the `brew deps` call errors. The block itself is genuine in each case; only the attribution is missing. Fixing it means having `isolate_clean()` return each dropped candidate's own violators.
