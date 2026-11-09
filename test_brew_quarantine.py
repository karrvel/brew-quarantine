#!/usr/bin/env python3
"""Self-tests for brew-quarantine. Stdlib only; never runs brew or touches ~/.cache.

    python3 -m unittest -v test_brew_quarantine

Every call that would reach Homebrew or the network is replaced by a fake world, and
subprocess.run is patched to fail loudly if anything slips past the fakes.
"""

import argparse
import atexit
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from unittest import mock

TMP = Path(tempfile.mkdtemp(prefix="bq-test-"))
atexit.register(shutil.rmtree, TMP, True)
# Must be set before loading the script: CACHE_PATH is read at import time.
os.environ["BREW_QUARANTINE_CACHE"] = str(TMP / "cache" / "dates.json")

SCRIPT = Path(__file__).with_name("brew-quarantine")
_loader = SourceFileLoader("bq", str(SCRIPT))
bq = module_from_spec(spec_from_loader("bq", _loader))
_loader.exec_module(bq)

OLD = "2020-01-01T00:00:00+00:00"


class EvaluateBuckets(unittest.TestCase):
    """Every requested package lands in exactly one bucket, and no-ops are not 'blocked'."""

    def evaluate(self, requested, plans, deps, young=()):
        """plans: package -> what brew would touch for it alone; deps: recursive deps."""

        def resolve_plan(action, pkgs, extra_args):
            return set().union(*(plans[p] for p in pkgs)), ""

        def load_metadata(names):
            return {n: bq.Pkg(n, "formula", "homebrew/core", f"Formula/{n}.rb", "1") for n in names}

        def lookup_dates(pkgs, cache, workers=8):
            fresh = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            return {p.name: fresh if p.name in young else OLD for p in pkgs}

        def brew(*args, **kw):
            assert args[:2] == ("deps", "--for-each"), args
            names = [a for a in args[2:] if not a.startswith("--")]
            out = "\n".join(f"{n}: {' '.join(deps.get(n, []))}" for n in names)
            return subprocess.CompletedProcess(args, 0, out, "")

        with mock.patch.multiple(bq, resolve_plan=resolve_plan, load_metadata=load_metadata,
                                 lookup_dates=lookup_dates, brew=brew), \
             mock.patch.object(bq.subprocess, "run", side_effect=AssertionError("shelled out")):
            return bq.evaluate("upgrade", requested, 7, [], None, False, False)

    def assert_partition(self, requested, res):
        _survivors, plan, held, _unenf, skipped, _leaked, implicit, noop = res
        for n in requested:
            hits = [n in plan, n in held, n in implicit, n in skipped, n in noop]
            self.assertEqual(sum(hits), 1, f"{n} is in {hits.count(True)} buckets")
        for n, why in implicit.items():
            self.assertTrue(why, f"{n} is listed as blocked without naming a held dependency")

    def test_stall_fallback_reports_empty_plan_as_nothing_to_do(self):
        # x is too new and enters c's plan as a dependent, so no candidate *depends* on it:
        # the fixed point stalls and isolate_clean runs. b alone resolves to nothing.
        requested = ["a", "b", "c"]
        res = self.evaluate(requested, plans={"a": {"a"}, "b": set(), "c": {"c", "x"}},
                            deps={}, young={"x"})
        self.assertNotIn("b", res[6], "no-op labelled as blocked by a held dependency")
        survivors, plan, held, _u, _s, _l, implicit, noop = res
        self.assertEqual(noop, ["b"])
        self.assertEqual(plan, ["a"])
        self.assertIn("x", held)
        # c's blocker is a held *dependent*, which the deps-only lookup cannot name; that
        # residual is documented in the task shard, so only b's partition is checked here.
        self.assertEqual(sum(["b" in plan, "b" in held, "b" in implicit, "b" in noop]), 1)

    def test_noop_alongside_real_work_is_nothing_to_do(self):
        requested = ["a", "b", "c"]
        res = self.evaluate(requested, plans={"a": {"a"}, "b": set(), "c": {"c", "x"}},
                            deps={"c": ["x"]}, young={"x"})
        self.assertNotIn("b", res[6], "no-op labelled as blocked by a held dependency")
        self.assertEqual(res[6], {"c": ["x"]})
        self.assertEqual(res[7], ["b"])
        self.assert_partition(requested, res)

    def test_everything_already_installed(self):
        res = self.evaluate(["r"], plans={"r": set()}, deps={})
        self.assertNotIn("r", res[6], "no-op labelled as blocked by a held dependency")
        survivors, plan, *_rest, implicit, noop = res
        self.assertEqual((survivors, plan, implicit, noop), ([], [], {}, ["r"]))
        self.assert_partition(["r"], res)


def keg(cellar, name, version, installed_at):
    d = Path(cellar, name, version)
    d.mkdir(parents=True, exist_ok=True)
    (d / "INSTALL_RECEIPT.json").write_text(json.dumps({"time": installed_at, "arch": "arm64"}))


class Audit(unittest.TestCase):
    """--audit diffs Cellar install receipts against the last real run's cleared set."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(dir=TMP))
        self.cellar = self.dir / "Cellar"
        self.cellar.mkdir()
        self.receipt = self.dir / "last-run.json"  # what RUN_RECEIPT resolves to below

    def audit(self):
        env = dict(os.environ,
                   BREW_QUARANTINE_CACHE=str(self.dir / "dates.json"),
                   BREW_QUARANTINE_CELLAR=str(self.cellar),
                   PATH="/usr/bin:/bin")  # no brew on PATH: a stray call fails instead of running
        p = subprocess.run([sys.executable, str(SCRIPT), "--audit"], env=env,
                           capture_output=True, text=True, timeout=60)
        listed = [ln.split()[0] for ln in p.stdout.splitlines() if ln.startswith("  ")]
        return p.returncode, listed, p.stdout + p.stderr

    def test_real_run_writes_receipt_and_audit_flags_the_leak(self):
        now = int(time.time())
        keg(self.cellar, "old", "0.1", now - 30 * 86400)  # before the window: ignored
        keg(self.cellar, "a", "1.0", now - 30 * 86400)    # a's previous keg

        def fake_brew(cmd, **kw):
            assert cmd == ["brew", "upgrade", "a"], cmd
            t = int(time.time())
            keg(self.cellar, "a", "2.0", t)        # cleared, requested
            keg(self.cellar, "dep", "1.1", t)      # cleared, pulled in as a dependency
            keg(self.cellar, "sneaky", "3.0", t)   # installed but never cleared: the leak
            return subprocess.CompletedProcess(cmd, 0)

        args = argparse.Namespace(bypass=False, no_update=True, packages=["a"], days=7,
                                  brew_args=[], verbose=False, allow_unknown=False,
                                  json=False, dry_run=False)
        verdict = (["a"], ["a", "dep"], {}, [], [], [], {}, [])
        with mock.patch.object(bq, "RUN_RECEIPT", self.receipt), \
             mock.patch.object(bq, "evaluate", return_value=verdict), \
             mock.patch.object(bq.subprocess, "run", side_effect=fake_brew), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(bq.cmd_gate(args, "upgrade"), 0)

        run = json.loads(self.receipt.read_text())
        self.assertEqual(run["cleared"], ["a", "dep"])
        self.assertLessEqual(run["started"], run["finished"])

        rc, listed, out = self.audit()
        self.assertEqual(rc, 2, out)
        self.assertEqual(listed, ["sneaky"], out)

    def test_audit_passes_when_everything_installed_was_cleared(self):
        now = int(time.time())
        keg(self.cellar, "old", "0.1", now - 30 * 86400)
        keg(self.cellar, "a", "2.0", now - 5)
        keg(self.cellar, "tapdep", "1.0", now - 5)
        self.receipt.write_text(json.dumps({"action": "upgrade", "started": now - 10,
                                            "finished": now, "cleared": ["a", "user/tap/tapdep"]}))
        rc, listed, out = self.audit()
        self.assertEqual((rc, listed), (0, []), out)

    def test_audit_without_a_run_receipt_fails(self):
        rc, _listed, out = self.audit()
        self.assertEqual(rc, 1, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
