"""Finite-marginal bridge and honest boundaries of the validation companion."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.check_mask_covariance_conventions import (
    direct_conventions, direct_crossing, direct_reduce, run,
)
from research.mask_metrology import binary_correlations


class MaskConventionTests(unittest.TestCase):
    def test_hand_counted_edge_column(self):
        mask = np.zeros((4, 4), dtype=bool)
        mask[:, 0] = True
        result = direct_conventions(mask)
        self.assertEqual(result["phase_fraction"], .25)
        self.assertEqual(result["probability"][0, 1], 0.)
        self.assertAlmostEqual(result["centred"][0, 1], -1 / 9)
        self.assertAlmostEqual(result["homogeneous"][0, 1], -1 / 3)
        self.assertAlmostEqual(result["correction"][0, 1], 2 / 9)

    def test_complement_and_transpose(self):
        mask = np.random.default_rng(12).random((16, 20)) < .25
        original = direct_conventions(mask)["centred"]
        np.testing.assert_allclose(original, direct_conventions(~mask)["centred"])
        np.testing.assert_allclose(original[::-1], direct_conventions(mask.T)["centred"])
        np.testing.assert_allclose(original, binary_correlations(mask)[0], atol=1e-12)

    def test_constant_fields_remain_unresolved(self):
        for value in (False, True):
            result = direct_conventions(np.full((8, 8), value))
            self.assertTrue(np.all(np.isnan(result["centred"])))
            self.assertTrue(np.isnan(direct_crossing(result["centred"][0])))

    def test_half_height_plateau_and_missing_crossing(self):
        self.assertEqual(direct_crossing(np.array([1., .5, .5, .25])), 2.)
        self.assertTrue(np.isnan(direct_crossing(np.array([1., .8, .6]))))

    def test_direct_ties_and_invalid_factor(self):
        y, x = np.indices((16, 16))
        mask = (x + y) % 2 == 0
        self.assertFalse(np.any(direct_reduce(mask, 2, False)))
        self.assertTrue(np.all(direct_reduce(mask, 2, True)))
        for factor in (True, 3, 8):
            with self.assertRaises(ValueError):
                direct_reduce(mask, factor, False)

    def test_all_case_report_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "check"
            summary = run(output)
            self.assertEqual(summary["directional_checks"], 432)
            self.assertEqual(summary["mask_comparisons"], 216)
            self.assertLess(summary["maximum_absolute_kernel_error"], 1e-12)
            with (output / "all_cases.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 432)
            self.assertTrue(any(row["centred_crossing_status"] == "unresolved" for row in rows))
            self.assertIn("not physical validation", summary["interpretation"])
            self.assertIn("production_changed", json.loads((output / "summary.json").read_text()))
            self.assertIn("not a new algorithm", (output / "report.html").read_text())
            with self.assertRaises(FileExistsError):
                run(output)


if __name__ == "__main__":
    unittest.main()
