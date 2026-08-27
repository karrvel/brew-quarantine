---
name: dry-run-parse-stdout-only
type: gotcha
title: Parse brew --dry-run from stdout only — the tap-trust warning on stderr parses as package names
area: parsing
tags: [parsing, homebrew-6, tap-trust]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session — caught by the negative control test
---

# Merging stderr into the plan turns prose into packages

The first parser read `proc.stdout + proc.stderr` on the theory that more output is safer. Homebrew 6's tap-trust notice is many lines of *unindented* prose on stderr, and because it contains no `==>` markers, a section opened by the last `==> Would install` header on stdout stayed open across all of it. The result: words like `the`, `taps`, `trust`, `with:` and `you` were parsed as package names and reported as held with "metadata unavailable".

Homebrew keeps the streams cleanly separated — the plan is on stdout, warnings are on stderr — so parsing `proc.stdout` alone fixes it. A second guard was added anyway: a section terminates at the first line that is not composed entirely of package-shaped tokens, so unexpected prose cannot run away again.

The same discipline applies in reverse for this tool's own output: progress chatter goes to stderr so `--json` produces parseable stdout. That was a real bug too — the first `--json` run emitted a progress line before the JSON and failed to parse.
