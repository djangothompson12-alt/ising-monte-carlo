"""Checks for the independent arithmetic audit of the declared extension."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.audit_main_extension import audit, equal_number, slope, slope_interval


class AuditMainExtensionTests(unittest.TestCase):
    def test_covariance_slope_and_whole_trajectory_interval(self):
        times = np.asarray([1_000, 2_000, 5_000, 20_000, 200_000])
        lengths = 0.4 * times ** (1 / 3)
        selected = np.ones(len(times), dtype=bool)
        self.assertAlmostEqual(slope(times, lengths, selected), 1 / 3, places=12)
        runs = np.asarray([scale * lengths for scale in (0.8, 0.9, 1.0, 1.1)])
        low, high = slope_interval(times, runs, selected)
        self.assertAlmostEqual(low, 1 / 3, places=12)
        self.assertAlmostEqual(high, 1 / 3, places=12)

    def test_unresolved_fit_and_nonfinite_comparison(self):
        times = np.asarray([1_000, 2_000, 5_000, 20_000])
        self.assertTrue(np.isnan(slope(times, np.ones(4), np.asarray([1, 0, 1, 1], dtype=bool))))
        self.assertTrue(equal_number(float("nan"), float("nan")))
        self.assertFalse(equal_number(float("inf"), float("inf")))

    def test_incomplete_campaign_is_rejected_before_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            plan = dict(sizes=[32, 64, 96, 128], concentrations=[0.5, 0.15],
                        replicas=16, max_sweeps=1_000_000, T_final_over_tc=0.65)
            (folder / "manifest.json").write_text(json.dumps({"identity": {"plan": plan}}))
            (folder / "status.json").write_text(json.dumps({"state": "running", "completed": 80}))
            with self.assertRaisesRegex(ValueError, "completed"):
                audit(folder, folder / "analysis")


if __name__ == "__main__":
    unittest.main()
