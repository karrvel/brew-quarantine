---
name: cannot-enforce-unpinned-casks
type: security
title: Casks with :latest, :no_check or a self-updater cannot be quarantined — report them, do not count them as protected
area: casks
tags: [casks, coverage, honesty]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session
---

# Some packages are outside the gate's reach, and the report must say so

The cooldown reasons about the age of a cask *definition*. For a large class of casks that says nothing about the age of the *payload*:

- `version :latest` — the definition never changes, so it is always old enough.
- `sha256 :no_check` — the artifact is not pinned, so the URL may serve anything.
- `auto_updates true` — the application replaces itself after installation regardless.

Any of these means the cask file can be a year old while the download is today's build. These are surfaced in a distinct **cannot fully enforce** section rather than being counted as cleared, because a report that silently folds them into the protected set overstates what the gate delivers — which is the failure mode that matters most for a security tool.

The detection is mechanical, from `brew info --json=v2`: `version == "latest"`, `sha256 == "no_check"`, `auto_updates`. Widely-used casks such as browsers and editors land here by design and there is no fix available from this side; the honest move is disclosure.

Related: [[wrapper-coverage-holes]].
