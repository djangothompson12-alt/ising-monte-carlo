import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.confirm_image_operator_extension import (
    measure_snapshot, primary_directional_verdict, render_report,
    shared_resolved, validate_complete,
)
from research.imaging import observe


class ImageHoldoutTests(unittest.TestCase):
    def test_partial_campaign_rejected_before_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            plan = dict(sizes=[32, 64, 96, 128], concentrations=[0.5, 0.15],
                        replicas=16, max_sweeps=1_000_000, Jx=1.0, Jy=1.0,
                        T_final_over_tc=0.65)
            (folder / "manifest.json").write_text(json.dumps({"identity": {"plan": plan}}))
            (folder / "status.json").write_text(json.dumps(
                {"state": "running", "completed": 26, "total": 128}))
            with self.assertRaisesRegex(ValueError, "forbidden until"):
                validate_complete(folder)
            (folder / "status.json").write_text(json.dumps(
                {"state": "complete", "completed": 128, "total": 128}))
            with self.assertRaisesRegex(ValueError, "Missing or unexpected"):
                validate_complete(folder)

    def test_common_mask_requires_both_directions_in_every_run(self):
        native = np.ones((2, 3, 2), dtype=float)
        binned = np.ones_like(native)
        native[1, 1, 0] = np.nan
        binned[0, 2, 1] = np.nan
        np.testing.assert_array_equal(shared_resolved(native, binned),
                                      [True, False, False])

    def test_fixed_binning_tie_and_site_spacing(self):
        snapshot = np.tile(np.kron(np.array([[1, -1], [-1, 1]]),
                                   np.ones((16, 16), dtype=np.int8)), (4, 4))
        native, binned, native_fraction, binned_fraction = measure_snapshot(snapshot)
        expected_image = observe(snapshot, factor=4, threshold=0.0)
        self.assertEqual(snapshot.shape, (128, 128))
        self.assertEqual(expected_image.shape, (32, 32))
        self.assertEqual(native_fraction, 0.5)
        self.assertEqual(binned_fraction, float(np.mean(expected_image == 1)))
        self.assertIn("length_x", native)
        self.assertIn("length_y", binned)
        tie = np.full((128, 128), -1, dtype=np.int8)
        tie[:4, :4] = np.array([[1, 1, -1, -1]] * 4)
        self.assertEqual(observe(tie, factor=4, threshold=0.0)[0, 0], 1)

    def test_predeclared_primary_sign_rule_ignores_secondary_window(self):
        rows = [dict(composition=c, nominal_t_min=1000, nominal_t_max=20000,
                     status="fit resolved", delta_alpha=shift)
                for c, shift in ((0.5, -0.05), (0.15, -0.07))]
        rows.append(dict(composition=0.5, nominal_t_min=1000, nominal_t_max=200000,
                         status="fit resolved", delta_alpha=0.2))
        self.assertIn("consistent in direction", primary_directional_verdict(rows))
        rows[1]["delta_alpha"] = 0.0
        self.assertIn("failed", primary_directional_verdict(rows))
        rows[1]["status"] = "fit unresolved"
        self.assertIn("unresolved", primary_directional_verdict(rows))
        with self.assertRaisesRegex(ValueError, "both"):
            primary_directional_verdict(rows[:1])

    def test_readable_report_shows_interval_and_phase_fraction_caveats(self):
        def row(composition, upper, delta, low, high):
            return dict(composition=composition, nominal_t_min=1000,
                        nominal_t_max=upper, actual_t_min=1069,
                        actual_t_max=upper, retained_points=10,
                        native_alpha=.25, binned_alpha=.25+delta,
                        delta_alpha=delta, delta_low=low, delta_high=high,
                        mean_native_fraction=.5,
                        mean_binned_fraction=.52,
                        status="fit resolved")
        rows = [row(.5, 20000, -.05, -.08, .01),
                row(.5, 200000, .02, -.01, .04),
                row(.15, 20000, -.07, -.09, -.02),
                row(.15, 200000, -.01, -.03, .01)]
        report = render_report(rows)
        self.assertIn("consistent in direction", report)
        self.assertIn("Interval crosses zero?", report)
        self.assertIn("| yes | 0.5000 | 0.5200 | +0.0200 |", report)
        self.assertIn("| no | 0.5000 | 0.5200 | +0.0200 |", report)
        self.assertIn("secondary window cannot rescue", report)


if __name__ == "__main__":
    unittest.main()
