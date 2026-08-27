---
name: age-signal-formula-commit-date
type: decision
title: Age a package by its .rb file's last commit date, never by the bottle's OCI created timestamp
area: core
tags: [supply-chain, age, ghcr, github-api]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session — verified directly against ghcr.io and the GitHub API
---

# Package age comes from the formula file's commit date

The cooldown needs one number per package: how long ago did *what I am about to install* come into existence. Two signals were available — the bottle's OCI `org.opencontainers.image.created` annotation on ghcr.io, and the last commit touching the package's own `.rb` file in its tap.

**The OCI annotation is unusable.** Measured on `wget` 1.25.0: the ghcr index reports `created: 2024-11-11T00:21:29Z`, while the formula file's last commit is `2026-06-26 "wget: update 1.25.0 bottle."` The annotation does not move when a bottle is rebuilt, so a bottle rebuilt today can report an age of two years — waving through precisely the change the gate exists to catch.

**The commit date fails safe.** Any change to what gets installed — version bump, URL change, sha256 change, bottle rebuild — must land as a commit to that file. Its failure mode is the opposite one: a docs-only touch resets the clock and causes a spurious hold, costing patience rather than the guarantee.

Sources differ by tap: `homebrew/core` and `homebrew/cask` are not local git clones under Homebrew's JSON API, so their dates come from the GitHub API; third-party taps are real clones, so `git log` answers offline. The exact path comes from `ruby_source_path` in `brew info --json=v2` rather than being reconstructed from the package name — see [[ruby-source-path-is-authoritative]].

Related: [[hold-unknown-ages-by-default]], [[cache-dates-never-verdicts]].
