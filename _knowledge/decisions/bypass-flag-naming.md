---
name: bypass-flag-naming
type: decision
title: Name the escape hatch --bypass, because --no-quarantine already means Gatekeeper
area: cli
tags: [naming, cli, gatekeeper]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session
---

# "Quarantine" is overloaded in Homebrew, so the bypass flag avoids the word

Homebrew already has `--quarantine` and `--no-quarantine`. They control the macOS Gatekeeper `com.apple.quarantine` extended attribute on downloaded applications and have nothing to do with release timing. Both are being deprecated upstream.

The tool is named `brew-quarantine` because that is what users ask for and because the name gives free `brew quarantine …` dispatch via Homebrew's external-command mechanism. But reusing `--no-quarantine` as the bypass flag would have created a genuinely dangerous ambiguity: a user reaching for the familiar Gatekeeper flag would silently disable the supply-chain gate instead.

Hence `--bypass`, and an explicit note at the top of both the `--help` text and the README stating that this is a release cooldown, not Gatekeeper quarantine.
