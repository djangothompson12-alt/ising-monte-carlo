"""Contract checks for the full-extension observable robustness audit."""

import unittest

import numpy as np

from research.analyse_extension_observable_robustness import (
    MEASURES, common_resolved_mask, matched_ratio, paired_fits,
)


class ObservableRobustnessTests(unittest.TestCase):
    def test_common_mask_uses_every_replica_and_estimator(self):
        values = np.ones((3, 5, len(MEASURES)))
        values[2, 3, 1] = np.nan
        np.testing.assert_array_equal(common_resolved_mask(values),
                                      [True, True, True, False, True])

    def test_paired_bootstrap_recovers_known_slopes_and_differences(self):
        times = np.geomspace(1_000, 200_000, 24)
        amplitudes = np.asarray([.9, 1.0, 1.1, 1.2])[:, None, None]
        powers = np.asarray([.2, .25, .3, .35])[None, None, :]
        values = amplitudes * times[None, :, None] ** powers
        rows = paired_fits(times, values, np.ones(len(times), dtype=bool),
                           seed=7, draws=100)
        np.testing.assert_allclose([row["alpha"] for row in rows],
                                   [.2, .25, .3, .35], atol=1e-12)
        np.testing.assert_allclose([row["delta_vs_threshold"] for row in rows],
                                   [0, .05, .1, .15], atol=1e-12)

    def test_matched_size_ratios_keep_estimators_separate(self):
        reference = np.tile([2., 4., 8., 16.], (4, 1))
        smaller = reference / 2
        rows = matched_ratio(smaller, reference, seed=8, draws=100)
        self.assertEqual([row["estimator"] for row in rows], list(MEASURES))
        np.testing.assert_allclose([row["ratio"] for row in rows], .5)
        self.assertTrue(all(row["status"] == "resolved" for row in rows))


if __name__ == "__main__":
    unittest.main()
