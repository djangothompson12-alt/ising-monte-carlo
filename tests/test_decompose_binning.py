import unittest

import numpy as np

from research.decompose_binning import threshold_block


class BinningDecompositionTests(unittest.TestCase):
    def test_exact_zero_ties_are_the_only_mask_difference(self):
        block = np.array([[0.0, 0.5, -0.5], [0.25, 0.0, -0.25]])
        plus = threshold_block(block, ties_plus=True)
        minus = threshold_block(block, ties_plus=False)
        self.assertTrue(np.array_equal(plus[block != 0], minus[block != 0]))
        self.assertTrue(np.all(plus[block == 0] == 1))
        self.assertTrue(np.all(minus[block == 0] == -1))
        self.assertAlmostEqual(np.mean(plus > 0) - np.mean(minus > 0), np.mean(block == 0))

    def test_rejects_invalid_block(self):
        with self.assertRaises(ValueError):
            threshold_block(np.array([0.0, 1.0]), ties_plus=True)
        with self.assertRaises(ValueError):
            threshold_block(np.array([[np.nan]]), ties_plus=False)


if __name__ == "__main__":
    unittest.main()
