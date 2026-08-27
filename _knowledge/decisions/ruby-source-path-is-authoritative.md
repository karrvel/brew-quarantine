---
name: ruby-source-path-is-authoritative
type: decision
title: Take the tap file path from ruby_source_path, do not reconstruct it from the package name
area: core
tags: [api, paths]
status: active
updated: 2026-08-27
volatility: durable
provenance: 2026-08-27 build session — verified for both a formula and a cask
---

# `ruby_source_path` already knows where the file lives

Aging a package requires the exact path of its `.rb` file inside its tap. The tempting shortcut is to build it from the name — `Formula/<first-letter>/<name>.rb` — but that sharding rule has enough exceptions to be a slow source of wrong answers: names beginning with a digit, versioned formulae carrying `@`, and cask subtrees that do not follow the single-letter scheme.

`brew info --json=v2` already reports the answer as `ruby_source_path`, for formulae and casks alike (`Formula/w/wget.rb`, `Casks/g/google-chrome.rb`). Reading it costs nothing extra because the same call supplies the tap, version, and the cask fields needed to detect unpinnable payloads.

The path then routes the lookup: `homebrew/core` and `homebrew/cask` are not local clones under Homebrew's JSON API and must go through the GitHub API, while third-party taps are real clones where `git log -1 --format=%cI -- <path>` answers offline and instantly.

Related: [[age-signal-formula-commit-date]].
