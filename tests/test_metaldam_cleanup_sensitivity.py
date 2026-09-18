import unittest

import numpy as np

from research.metaldam_cleanup_sensitivity import _summarise, cleanup, dice


class MetalDamCleanupSensitivityTests(unittest.TestCase):
    def test_dice_and_shape_validation(self):
        reference = np.array([[True, True], [False, False]])
        mask = np.array([[True, False], [True, False]])
        self.assertAlmostEqual(dice(mask, reference), 0.5)
        with self.assertRaises(ValueError):
            dice(mask.astype(int), reference)
        with self.assertRaises(ValueError):
            dice(mask, reference[:1])

    def test_median_removes_isolated_pixel_without_changing_input(self):
        mask = np.zeros((7, 7), dtype=bool)
        mask[3, 3] = True
        original = mask.copy()
        self.assertFalse(cleanup(mask, 3).any())
        self.assertTrue(np.array_equal(cleanup(mask, 1), original))
        self.assertTrue(np.array_equal(mask, original))
        with self.assertRaises(ValueError):
            cleanup(mask, 4)

    def test_paired_summary_counts_improvement_and_worsening(self):
        rows = []
        for image_id, raw_error, filtered_error in (("a", 0.8, 0.2), ("b", 0.1, 0.3)):
            for width, error in ((1, raw_error), (3, filtered_error), (5, filtered_error)):
                rows.append({
                    "image_id": image_id, "median_width": width, "dice": 0.8,
                    "mask_fraction": 0.5, "abs_phase_fraction_error": 0.1,
                    "length_ratio": float(np.exp(-error)),
                    "abs_log_length_error": error,
                })
        result = _summarise(rows)
        self.assertEqual(result["n_images"], 2)
        self.assertEqual(result["n_mask_measurements"], 6)
        self.assertEqual(result["by_width"]["1"]["resolved"], 2)
        self.assertEqual(result["paired_vs_raw"]["3"]["length_error_improved"], 1)
        self.assertEqual(result["paired_vs_raw"]["3"]["length_error_worsened"], 1)
        self.assertEqual(result["paired_vs_raw"]["3"]["jointly_resolved"], 2)


if __name__ == "__main__":
    unittest.main()
