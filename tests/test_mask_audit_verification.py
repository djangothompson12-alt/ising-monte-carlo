"""Exact-reference, boundary and practical decision checks for the mask audit."""

import unittest
from unittest.mock import patch

import numpy as np

from research.mask_metrology import binary_correlations, binary_image_length
from research.mask_resolution_audit import compare_lengths, measure, tie_summary
from research.verify_mask_resolution_audit import reference_measure, synthetic_cases


class MaskAuditVerificationTests(unittest.TestCase):
    def test_reference_against_hand_calculated_checkerboards(self):
        y, x = np.indices((16, 16))
        pixel_checkerboard = (x + y) % 2 == 1
        # C(0)=1, C(1)=-1 gives an interpolated half crossing at 1/4 pixel.
        expected = reference_measure(pixel_checkerboard, 1, 1.0, False)
        self.assertEqual(expected["length_x"], .25)
        self.assertEqual(expected["length_y"], .25)
        two_pixel = (x // 2 + y // 2) % 2 == 1
        # In a finite 16-pixel row, C(1)=1/15; the crossing is 15/28.
        expected = reference_measure(two_pixel, 1, 1.0, False)
        self.assertEqual(expected["length_x"], 15 / 28)

    def test_all_synthetic_fields_match_independent_exact_reference(self):
        for name, mask in synthetic_cases().items():
            for factor in (1, 2, 4):
                for foreground in (False, True):
                    with self.subTest(case=name, factor=factor, foreground=foreground):
                        actual = measure(mask, factor, .06, foreground)
                        expected = reference_measure(mask, factor, .06, foreground)
                        for key in ("length", "length_x", "length_y", "phase_fraction", "tie_block_fraction"):
                            np.testing.assert_allclose(actual[key], expected[key],
                                                       rtol=1e-12, atol=1e-13, equal_nan=True)

    def test_exact_pair_counts_refine_half_height_without_snapping(self):
        mask = synthetic_cases()["exact_half_lag"]
        correlations, _ = binary_correlations(mask)
        self.assertEqual(correlations[0, 1], .5)
        correlations[0, 1] = .5 - 1e-13  # Explicit FFT roundoff, independent of FFT library.
        with patch("research.mask_metrology.finite_correlations", return_value=correlations):
            corrected, checks = binary_correlations(mask)
        self.assertGreater(checks, 0)
        self.assertEqual(corrected[0, 1], .5)
        # Nearby, non-boundary values must retain their actual covariance.
        random = synthetic_cases()["random_50"]
        actual, _ = binary_correlations(random)
        self.assertFalse(np.all((actual == .5) | (actual == 1)))

    def test_spacing_complement_and_transpose_preserve_defined_invariances(self):
        mask = synthetic_cases()["two_circles"]
        base = binary_image_length(mask)
        inverse, transpose = binary_image_length(~mask), binary_image_length(mask.T)
        self.assertAlmostEqual(base["length"], inverse["length"])
        self.assertAlmostEqual(base["length_x"], transpose["length_y"])
        self.assertAlmostEqual(base["length_y"], transpose["length_x"])
        self.assertAlmostEqual(binary_image_length(mask, 2.35)["length"], base["length"] * 2.35)

    def test_inclusive_tolerance_boundary_is_stable_under_unit_changes(self):
        for scale in (1e-9, 1, 1e9):
            native = dict(factor=1, length=10. * scale, length_x=10. * scale, length_y=10. * scale)
            changed = dict(factor=2, length=11. * scale, length_x=11. * scale, length_y=11. * scale)
            self.assertEqual(compare_lengths(changed, native, .1, "both_directions")["decision_status"],
                             "within owner tolerance")
            changed["length_x"] = 11.000000001 * scale
            self.assertEqual(compare_lengths(changed, native, .1, "both_directions")["decision_status"],
                             "outside owner tolerance")

    def row(self, factor, x=10., y=10., fraction=.5, warning="no flag"):
        return dict(factor=factor, length=(x + y) / 2, length_x=x, length_y=y,
                    phase_fraction=fraction, tie_block_fraction=.1,
                    three_pixel_warning=warning)

    def test_tie_dependency_and_hidden_directional_change_are_retained(self):
        native = self.row(1)
        selected, opposite = self.row(2, 10, 10), self.row(2, 12, 8)
        axes = tie_summary(selected, opposite, native, .1, "both_directions")
        self.assertEqual(axes["criterion"], "criterion depends on tie rule")
        self.assertEqual(axes["opposite_mean_change_percent"], 0.)
        self.assertAlmostEqual(axes["opposite_max_directional_change_percent"], 20.)
        mean = tie_summary(selected, opposite, native, .1, "mean_length")
        self.assertEqual(mean["criterion"], "within tolerance under both tie rules")

    def test_good_tolerance_cannot_hide_a_resolution_warning(self):
        native, selected = self.row(1), self.row(2)
        opposite = self.row(2, warning="flag")
        result = tie_summary(selected, opposite, native, .1, "both_directions")
        self.assertEqual(result["criterion"], "within tolerance under both tie rules")
        self.assertTrue(result["any_resolution_warning"])
        self.assertIn("Review image resolution", result["next_action"])
        opposite = self.row(2, x=np.nan, warning="unresolved")
        result = tie_summary(selected, opposite, native, .1, "both_directions")
        self.assertEqual(result["criterion"], "unresolved comparison")
        self.assertEqual(result["next_action"], "Review unresolved length")

    def test_no_owner_tolerance_gives_no_automatic_acceptance(self):
        result = tie_summary(self.row(2), self.row(2), self.row(1), None, "both_directions")
        self.assertEqual(result["criterion"], "no owner tolerance")
        self.assertIn("Define a useful tolerance", result["next_action"])

    def test_verification_inputs_are_bounded(self):
        for field in (np.ones((4, 4)), np.zeros((3, 3), dtype=bool)):
            with self.assertRaises(ValueError):
                binary_image_length(field)
        with self.assertRaises(ValueError):
            reference_measure(np.ones((128, 128), dtype=bool), 1, 1, False)


if __name__ == "__main__":
    unittest.main()
