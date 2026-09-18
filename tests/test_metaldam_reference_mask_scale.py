"""Synthetic invariants for expert-mask resolution audit; no source pixels used."""

import unittest

import numpy as np

from research.metaldam_reference_mask_scale import dice, measure_factor, summarize


class TestReferenceMaskScale(unittest.TestCase):
    def test_tie_rules_are_declared_and_unresolved_stays_missing(self) -> None:
        mask = np.indices((32, 32)).sum(axis=0) % 2 == 0
        one = measure_factor(mask, 2, tie_to_class_one=True)
        zero = measure_factor(mask, 2, tie_to_class_one=False)
        self.assertEqual(one["tie_block_fraction"], 1.0)
        self.assertEqual(zero["tie_block_fraction"], 1.0)
        self.assertEqual(one["fraction_difference"], 0.5)
        self.assertEqual(zero["fraction_difference"], -0.5)
        self.assertFalse(one["coarse_resolved"])
        self.assertFalse(zero["coarse_resolved"])
        self.assertTrue(np.isnan(one["length_ratio"]))
        self.assertTrue(np.isnan(zero["length_ratio"]))

    def test_matched_crop_and_original_pixel_units(self) -> None:
        yy, xx = np.indices((33, 34))
        mask = ((yy // 8 + xx // 8) % 2 == 0)
        result = measure_factor(mask, 4, tie_to_class_one=True)
        self.assertEqual(result["trimmed_rows"], 1)
        self.assertEqual(result["trimmed_columns"], 2)
        self.assertAlmostEqual(result["reference_fraction"], 0.5)
        self.assertEqual(result["coarse_fraction"], 0.5)
        self.assertAlmostEqual(result["dice_after_expansion"], 1.0)
        self.assertEqual(result["tie_block_fraction"], 0.0)
        self.assertTrue(result["reference_resolved"])
        self.assertTrue(result["coarse_resolved"])
        self.assertGreater(result["reference_length_px"], 1.0)
        self.assertGreater(result["coarse_length_original_px"], 1.0)

    def test_dice_and_summary_do_not_turn_missing_into_zero(self) -> None:
        a = np.zeros((8, 8), dtype=bool)
        self.assertEqual(dice(a, a), 1.0)
        with self.assertRaises(ValueError):
            dice(a, np.zeros((7, 8), dtype=bool))
        rows = []
        for factor in (2, 4, 8):
            for tie_to_class_one in (True, False):
                rows.append(dict(factor=factor, tie_to_class_one=tie_to_class_one,
                                 length_ratio=float("nan"), dice_after_expansion=0.8,
                                 fraction_difference=0.1, tie_block_fraction=0.0))
        for group in summarize(rows):
            self.assertEqual(group["resolved_ratios"], 0)
            self.assertEqual(group["unresolved_ratios"], 1)
            self.assertIsNone(group["median_length_ratio"])


if __name__ == "__main__":
    unittest.main()
