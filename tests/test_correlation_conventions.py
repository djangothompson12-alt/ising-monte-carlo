"""Protect the intentional Model A/raw versus Model B/connected asymmetry."""

import unittest

import numpy as np

from model_a.ising_engine import _axis_correlation as model_a_correlation
from model_b.kawasaki_engine import _axis_correlation_xy as model_b_correlations


class CorrelationConventionTests(unittest.TestCase):
    def test_biased_lattice_keeps_raw_model_a_signal(self):
        lattice = np.ones((8, 8), dtype=np.int8)
        lattice[:4, :4] = -1
        magnetisation = float(lattice.mean())
        raw_mean = model_a_correlation(lattice, 4)
        connected_x, connected_y = model_b_correlations(lattice, 4)
        for separation in range(5):
            horizontal = float(np.mean(lattice * np.roll(lattice, -separation, axis=1)))
            vertical = float(np.mean(lattice * np.roll(lattice, -separation, axis=0)))
            self.assertAlmostEqual(raw_mean[separation], (horizontal + vertical) / 2)
            self.assertAlmostEqual(connected_x[separation],
                                   (horizontal - magnetisation ** 2) / (1 - magnetisation ** 2))
            self.assertAlmostEqual(connected_y[separation],
                                   (vertical - magnetisation ** 2) / (1 - magnetisation ** 2))
        self.assertGreater(abs(raw_mean[2] - (connected_x[2] + connected_y[2]) / 2), 0.1)


if __name__ == "__main__":
    unittest.main()
