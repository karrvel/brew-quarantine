---
name: kb-sync-bakes-absolute-home-path
type: gotcha
title: kb-sync writes an absolute /Users path into INDEX.md — scrub it before every push of a public vault
area: tooling
tags: [kb, pii, generated-files]
status: active
updated: 2026-08-27
volatility: decays-with-code
provenance: 2026-08-27 — caught by a PII grep before the first public push
---

# Regenerating the index reintroduces a home-path leak

`kb-sync.py` writes the location of the always-loaded memory tier into the generated `INDEX.md` as an **absolute path**, of the form `/Users/<name>/.claude/projects/<key>/memory/MEMORY.md`. The project key embeds the home directory a second time. In a private vault this is merely ugly; in a vault that ships in a public repository it is a username disclosure, and it is exactly the pattern the `home-path-users` rule in `pii-scan.py` exists to block.

Because `INDEX.md` is generated, the leak returns every time the sync step runs. Fixing it once by hand is not a fix.

**The working rule for this repo:** after any `kb-sync.py` run, rewrite that line to `~/.claude/projects/<project-memory-key>/memory/MEMORY.md`, then run `pii-scan.py` before committing. Treat a clean scan, not a clean lint, as the release gate.

The durable fix belongs upstream in the kit — emit a `~`-relative path, or make the memory-tier pointer configurable — at which point this shard becomes historical.
