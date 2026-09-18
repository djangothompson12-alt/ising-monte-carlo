import unittest

import numpy as np

from research.paired_window_sensitivity import paired_window_fit


class PairedWindowSensitivityTests(unittest.TestCase):
    def test_identical_power_law_has_zero_window_shift(self):
        times = np.asarray([2, 5, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000, 200000])
        trajectories = np.asarray([1.1 * times ** .25, 1.2 * times ** .25,
                                   1.3 * times ** .25, 1.4 * times ** .25])
        result = paired_window_fit(times, trajectories, 128, draws=100, seed=9)
        self.assertEqual(len(result), 2)
        for row in result:
            self.assertAlmostEqual(row["early_alpha"], .25)
            self.assertAlmostEqual(row["late_alpha"], .25)
            self.assertAlmostEqual(row["delta_late_minus_early"], 0)
            self.assertAlmostEqual(row["delta_low"], 0)
            self.assertAlmostEqual(row["delta_high"], 0)
            self.assertEqual(row["valid_bootstrap_draws"], 100)

    def test_rejects_checkpoint_as_replica(self):
        with self.assertRaisesRegex(ValueError, "two complete trajectories"):
            paired_window_fit(np.array([1, 2, 3]), np.ones((1, 3)), 128)


if __name__ == "__main__":
    unittest.main()
