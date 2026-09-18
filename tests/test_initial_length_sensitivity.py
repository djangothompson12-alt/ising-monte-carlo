import unittest

import numpy as np

from research.initial_length_sensitivity import paired_slopes


class InitialLengthSensitivityTests(unittest.TestCase):
    def test_fixed_measured_offset_recovers_synthetic_one_third(self):
        times = np.array([18, 22, 1_000, 5_000, 20_000, 100_000, 200_000])
        amplitudes = np.array([0.8, 0.9, 1.0, 1.1, 1.2])[:, None]
        lengths = 3.6 + amplitudes * (times - 18) ** (1 / 3)
        result = paired_slopes(times, lengths, initial_index=0,
                               lower=1_000, upper=200_000, draws=30)
        self.assertEqual(result["points"], 5)
        self.assertAlmostEqual(result["shifted"], 1 / 3, places=12)
        self.assertLess(result["raw"], result["shifted"])

    def test_unresolved_trajectory_drops_checkpoint_from_both_fits(self):
        times = np.array([18, 22, 1_000, 5_000, 20_000, 100_000, 200_000])
        amplitudes = np.array([0.8, 1.0, 1.2])[:, None]
        lengths = 3.6 + amplitudes * (times - 18) ** (1 / 3)
        lengths[1, 4] = np.nan
        result = paired_slopes(times, lengths, initial_index=0,
                               lower=1_000, upper=200_000, draws=30)
        self.assertEqual(result["points"], 4)
        self.assertEqual(result["used_t_min"], 1_000)
        self.assertEqual(result["used_t_max"], 200_000)
        self.assertTrue(np.isfinite(result["raw"]))


if __name__ == "__main__":
    unittest.main()
