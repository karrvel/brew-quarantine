<div align="center">

# brew-quarantine

**A release cooldown for Homebrew.** Refuses to install or upgrade any package whose definition landed less than *N* days ago — dependencies included.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://brew.sh)
[![Homebrew 4+](https://img.shields.io/badge/homebrew-4%2B-orange.svg)](https://brew.sh)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB.svg)](https://www.python.org/)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none-success.svg)](#requirements)

</div>

---

> [!IMPORTANT]
> This is a **supply-chain release cooldown**, not macOS Gatekeeper quarantine. Homebrew's own `--quarantine` / `--no-quarantine` flags control the `com.apple.quarantine` attribute on downloaded apps and are unrelated to this tool. The bypass flag here is deliberately named `--bypass` to keep the two apart.

## Why

When a package repository is compromised, the malicious release is usually caught and yanked within days. A cooldown converts that detection window into protection: wait *N* days before adopting any new version, and you skip the window in which most attacks live. npm, pnpm, Dependabot, and Renovate all ship some form of this. Homebrew does not — see [Upstream's position](#upstream-position).

## The part that is easy to get wrong

Gating only the packages you *name* is decorative, because Homebrew installs more than you ask for:

```console
$ brew upgrade --dry-run ffmpeg
==> Would upgrade 3 dependencies for ffmpeg:
mpg123  1.33.6 -> 1.33.7
sdl3    3.4.12 -> 3.4.14
x265    4.2    -> 4.3
==> Would upgrade 2 outdated packages
ffmpeg  8.1.2_1  -> 9.0.1_1
mpv     0.41.0_6 -> 0.41.0_8
```

You asked for one package and got six, any of which could be the fresh one. `brew-quarantine` asks Homebrew for the **full would-touch set**, ages every member, drops the violators *and everything that depends on them*, and repeats until the plan is clean — then re-verifies before executing.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/karrvel/brew-quarantine/main/brew-quarantine \
  -o ~/.local/bin/brew-quarantine
chmod +x ~/.local/bin/brew-quarantine
```

Because the file is named `brew-quarantine` and sits on `PATH`, Homebrew picks it up as an external command — `brew quarantine …` works with no further setup.

To gate `brew install` and `brew upgrade` automatically, add a thin wrapper to `~/.zshrc`:

```zsh
export BREW_QUARANTINE_DAYS=7
brew() {
  if [[ "$1" == "install" || "$1" == "upgrade" ]] && [[ -x "$HOME/.local/bin/brew-quarantine" ]]; then
    local sub="$1"; shift
    "$HOME/.local/bin/brew-quarantine" "$sub" "$@"
  else
    command brew "$@"
  fi
}
```

The wrapper is a *caller*, not a `PATH` shadow — `command brew …` always reaches the real Homebrew.

## Usage

```bash
brew-quarantine upgrade                  # upgrade only what has cleared the cooldown
brew-quarantine install ripgrep          # install only if it and its deps have cleared
brew-quarantine status                   # what is held, and when each clears
brew-quarantine --days 14 upgrade        # stricter window for one run
brew-quarantine upgrade --dry-run        # report only; never touches the system
brew-quarantine --json upgrade           # machine-readable, for scripting
brew-quarantine --audit                  # after a real run: did brew install anything uncleared?
```

| Flag | Effect |
|---|---|
| `--days N` | Cooldown window. Default `7`, or `$BREW_QUARANTINE_DAYS`. |
| `--dry-run` | Report the decision; do not run `brew`. |
| `--bypass` | Skip the gate entirely and run `brew` directly. |
| `--no-update` | Skip the initial `brew update`. |
| `--allow-unknown` | Let packages whose age cannot be determined pass. Default is to hold them. |
| `--json` | Emit JSON on stdout; progress goes to stderr. |
| `--brew-arg X` | Pass `X` through to `brew` (repeatable). |
| `--audit` | Check the last real run against Homebrew's install receipts. Takes no subcommand. See [below](#checking-a-real-run---audit). |

Global flags (all but `--audit`) work on either side of the subcommand, so `brew upgrade --dry-run` behaves the way you would expect.

## What it looks like

```console
$ brew-quarantine upgrade

Homebrew quarantine — 7-day cooldown (upgrade)
  age = last commit to the package's .rb file in its tap

HELD (3)  — too new, or age could not be established
  cmake       1.1d  formula  too new    clears 2026-01-08 10:47 UTC
  fzf         2.2d  formula  too new    clears 2026-01-09 09:47 UTC
  glib        2.2d  formula  too new    clears 2026-01-09 09:47 UTC

HELD TRANSITIVELY (2)  — themselves old enough, but depend on something inside the cooldown
  graphviz    blocked by: glib
  pango       blocked by: glib

CANNOT FULLY ENFORCE (1)  — cask file is old enough, but the payload isn't pinned
  some-app  (app self-updates)
  These fetch whatever the vendor serves now, regardless of the cask file's age.

CLEARED (4)  — will be installed/upgraded
  jq  pandoc  ripgrep  sqlite
```

Every requested package lands in exactly one bucket. The buckets are disjoint and sum to the request — nothing is silently dropped.

## How it works

1. **Resolve.** Run `brew <action> --dry-run` and parse the full set Homebrew would touch, dependencies included.
2. **Age.** For each package, find the last commit that changed its own `.rb` file in its tap.
3. **Shrink.** Drop anything inside the cooldown, plus every candidate that depends on it. Repeat to a fixed point. If it stalls, fall back to per-candidate isolation.
4. **Verify.** Re-resolve the surviving set and assert nothing in the final plan is inside the cooldown. Exit code `2` if that check ever fails.
5. **Execute.** Hand the survivors to `brew`, with `HOMEBREW_NO_AUTO_UPDATE=1` so the version that was aged is the version that gets installed.

### Checking a real run: `--audit`

Step 4 reads the same `--dry-run` output the gate decided from, so it cannot notice when that output is incomplete — and it has been: a live upgrade installed four held packages while every self-check passed. `--audit` checks against evidence the gate did not produce. Each real run records its start and end time and the set it cleared in `~/.cache/brew-quarantine/last-run.json`. `--audit` then reads `$(brew --cellar)/*/*/INSTALL_RECEIPT.json`, takes every keg whose receipt `time` falls inside that window, and lists any the run did not clear:

```console
$ brew-quarantine --audit
Audit of the upgrade run at 2026-01-08 10:47 UTC  (/opt/homebrew/Cellar)
LEAKED (1)  — installed during the run but never cleared by the gate
  glib 2.88.3
```

It exits `0` when everything installed was cleared, `2` on a leak, and `1` when there is nothing to audit (no run recorded yet, or no Cellar). `BREW_QUARANTINE_CELLAR` overrides the Cellar path. Only the most recent run is kept, and only formulae are audited — casks are not. Anything else that installs a keg inside the window, such as `brew` in another terminal, shows up as a leak.

### Age signal: commit date, not bottle timestamp

The age of a package is the **last commit date of its `.rb` file** — via the GitHub API for `homebrew/core` and `homebrew/cask` (which are not local git clones under Homebrew's JSON API), and via local `git log` for third-party taps.

The obvious alternative — the bottle's OCI `org.opencontainers.image.created` annotation — is **not usable**, and it is worth being concrete about why:

```console
$ # wget 1.25.0's bottle index, as published:
$ #   org.opencontainers.image.created: 2024-11-11T00:21:29Z
$ # but the formula file's last commit:
$ #   2026-06-26  "wget: update 1.25.0 bottle."
```

The annotation does not move when a bottle is rebuilt, so a bottle rebuilt *today* can report an age of two years. Any tool aging core formulae that way will wave through exactly the change it is supposed to catch. The commit date fails in the safe direction instead: a docs-only touch causes a spurious hold, which costs a few days of patience rather than the whole guarantee.

## What it cannot enforce

Honesty about coverage matters more than a clean-looking report.

- **Casks with `version :latest`, `sha256 :no_check`, or a built-in updater.** The cask file can be a year old while the URL behind it serves today's build. These are reported under *cannot fully enforce* rather than counted as protected.
- **Anything that does not go through the wrapper.** A `zsh` function covers interactive shells only. `brew bundle`, cron jobs, CI, and scripts calling `brew` directly all bypass it. The standalone script exists so those paths have something to call.
- **Packages Homebrew itself cannot resolve** — for example a tap left untrusted under Homebrew 6's tap-trust gate. They are listed as *skipped*, because `brew` would not act on them either way.
- **The cooldown is not a vulnerability scanner.** It delays adoption; it does not know whether a release is malicious.

## Upstream position

Homebrew has considered and declined a user-facing minimum-age feature: [Homebrew/brew#21421](https://github.com/Homebrew/brew/issues/21421) is closed as *not planned*, and the [security documentation](https://docs.brew.sh/Homebrew-Security-and-Supply-Chain) argues that a blanket cooldown "would trade a small, speculative reduction in supply-chain risk for a real, across-the-board delay in shipping critical fixes," since every version bump already passes human review. Homebrew's own cooldown is one day and applies only to maintainers resolving npm/PyPI/cargo resources at build time.

That argument is worth taking seriously, and this tool does not pretend to refute it — it makes the trade deliberately, for people who would rather be a week behind. When a fix genuinely needs to land now, `command brew upgrade <pkg>` is the fast path.

Related discussion: [#21129](https://github.com/Homebrew/brew/issues/21129) (dependency cooldown), [#22000](https://github.com/Homebrew/brew/issues/22000) (cooldown window for `brew outdated`).

## Prior art

[`sharkyger/homebrew-safe-upgrade`](https://github.com/sharkyger/homebrew-safe-upgrade) combines CVE-gating across three vulnerability databases with a `--min-age` window, and is worth a look if scanning matters more to you than the age gate. It resolves the age of core formulae from the bottle's container-image creation timestamp — see [above](#age-signal-commit-date-not-bottle-timestamp) for why this tool does not.

## Requirements

- macOS with Homebrew 4 or newer
- Python 3.9+ (the system `python3` is fine) — **no third-party packages**
- Optional: an authenticated [`gh`](https://cli.github.com), or `$GITHUB_TOKEN` / `$HOMEBREW_GITHUB_API_TOKEN`. Unauthenticated GitHub API access is limited to 60 requests/hour, which a large upgrade will exhaust; authenticated raises it to 5,000. Resolved dates are cached under `~/.cache/brew-quarantine/`.

## Notes on the cache

Only the *date* a revision landed is cached, keyed by `(tap, path, version)` — never the pass/fail verdict. Caching a verdict would let a "blocked" decision outlive its own cooldown window and hold a package forever.

## Repository layout

```
brew-quarantine          the tool — a single dependency-free Python file
test_brew_quarantine.py  self-tests — stdlib only, never runs brew
_knowledge/              project knowledge vault (design decisions, gotchas, open work)
```

Run the self-tests with `python3 -m unittest -v test_brew_quarantine`. Every Homebrew and network call is replaced by a fake, so they are safe on a machine you care about.

The `_knowledge/` vault holds the durable reasoning behind the implementation: why the age signal is what it is, which parsing traps bit during development, and what is still open. Start at [`_knowledge/INDEX.md`](_knowledge/INDEX.md).

## License

[MIT](LICENSE)
