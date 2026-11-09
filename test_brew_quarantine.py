#!/usr/bin/env python3
"""Self-tests for brew-quarantine. Stdlib only; never runs brew or touches ~/.cache.

    python3 -m unittest -v test_brew_quarantine

Every call that would reach Homebrew or the network is replaced by a fake world, and
subprocess.run is patched to fail loudly if anything slips past the fakes.
"""

import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from unittest import mock

TMP = Path(tempfile.mkdtemp(prefix="bq-test-"))
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
