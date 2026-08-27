---
name: hold-unknown-ages-by-default
type: decision
title: Hold packages whose age cannot be established, rather than letting them through
area: core
tags: [fail-closed, api]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session
---

# Unknown age is a hold, not a pass

A date lookup can fail for dull reasons — GitHub rate limiting, a renamed formula file, a tap that is not a git clone, transient network failure. The gate treats every one of these as a hold, labelled "age unknown" or "metadata unavailable" so the cause is visible, with `--allow-unknown` to invert it for a run.

Failing open would be worse than having no gate at all, because it would be silently conditional: the tool would report protection while a rate-limited lookup quietly waved packages through. A visible over-hold is recoverable in one command; an invisible under-hold is not recoverable at all.

The cost is real and worth naming. Unauthenticated GitHub API access allows 60 requests an hour, which a large upgrade exhausts, at which point everything reads as unknown and everything is held. This is why an authenticated token is documented as strongly recommended rather than optional.

One class is deliberately exempt: packages Homebrew itself cannot resolve, most often a tap left untrusted under Homebrew 6 tap trust. They are set aside as *skipped* before the fixed point runs, since `brew` would not act on them either way — and because as unresolvable entries they can never be dropped by the loop, they previously caused it to stall. See [[tap-trust-hides-third-party-taps]].
