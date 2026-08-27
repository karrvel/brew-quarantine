---
name: readme
type: schema
title: How this knowledge vault works
area: cross
tags: [schema, discipline]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27
---

# `_knowledge` — the project knowledge vault

Plain-markdown, git-tracked, Obsidian-compatible knowledge distilled from building this tool. It exists so that the expensive parts — the measurements, the dead ends, the behaviours of Homebrew that are not documented anywhere — do not have to be rediscovered.

Start at [[INDEX]]. Open only the pages you need.

## What belongs here

Facts that cost something to learn and are not visible in the code:

- **gotcha** — a non-obvious trap, its symptom, and the fix.
- **decision** — context, what was decided, why that and not the alternative, consequences.
- **security** — a rule to follow, or an open finding and how to verify it.
- **task** — concrete remaining work with acceptance criteria.
- **repo** — one page per component: layout and how to work on it.
- **architecture** — the system model.
- **reference** — raw source material worth keeping verbatim.

What does not belong: anything the code already says plainly, and generic best practice. Prefer zero shards over noise.

## Frontmatter schema

Every shard carries the same block:

```yaml
---
name: <short-kebab-case-slug>        # unique; the target of [[links]]
type: gotcha|decision|security|task|repo|architecture|reference
title: <one-line human title>
area: <core|parsing|cli|casks|integration|testing|reporting|cross>
tags: [<free tags>]
status: active|superseded|resolved
updated: YYYY-MM-DD
volatility: durable|decays-with-code|one-shot
provenance: <where this came from — a date, a measurement, a code path>
---
```

## Volatility — read this before trusting a shard

- **durable** — true regardless of the state of the code. Trust it.
- **decays-with-code** ⚠️ — accurate only as of `updated:`. Re-verify against the code before acting on it.
- **one-shot** — a closed record, kept for history.

The distinction matters most for anything describing Homebrew's output formats or its tap-trust behaviour, which move between releases.

## Discipline

Link related shards with `[[slug]]` — the graph is how a reader finds the second thing they needed. When a shard's claim is a measurement, record the measured value, not the conclusion alone: "the OCI annotation said 2024-11-11 while the commit said 2026-06-26" survives re-reading in a way that "the annotation is unreliable" does not.

Append notable events to [[log]] as they happen.
