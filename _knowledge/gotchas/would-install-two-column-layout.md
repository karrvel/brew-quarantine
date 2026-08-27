---
name: would-install-two-column-layout
type: gotcha
title: "\"Would install N dependencies\" uses a two-column name/version layout with no arrow"
area: parsing
tags: [parsing, dry-run]
status: active
updated: 2026-08-27
volatility: decays-with-code
provenance: 2026-08-27 build session — verified against Homebrew 6 output
---

# Three different line shapes hide inside the dry-run plan

`brew --dry-run` prints plan members in at least three layouts, and only one of them is obvious:

```
==> Would install 12 dependencies for awscli:
aws-c-common        0.14.5          <- two columns, NO arrow
==> Would upgrade 4 outdated packages
abseil    20260107.1 -> 20260817.0 (1.9MB)   <- arrow form
==> Would install 1 formula:
tealdeer                              <- lone token
```

A parser that splits on whitespace and keeps every token reads `0.14.5` as a package name. That produced ghost entries like `0.10.5` and `1.7.8` in the held list, and worse, those ghosts could never be dropped by the fixed point — nothing depends on them and they are not candidates — so the loop stalled and held the entire plan.

The rule that handles all three: a lone token on a line is always a name; on multi-token lines, drop tokens that look like bare versions (`^\d[\d.]*(?:[._+-][A-Za-z0-9.]+)*$`). That pattern deliberately does not match names that merely start with a digit, such as `7zip`, because those need a separator before any letters.

Marked decays-with-code: this is Homebrew's presentation layer and can change between releases.
