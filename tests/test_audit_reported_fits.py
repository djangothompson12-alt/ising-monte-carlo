import unittest

import numpy as np

from research.audit_reported_fits import _check, log_slope


class ReportedFitAuditTests(unittest.TestCase):
    def test_explicit_log_slope_recovers_known_power(self):
        times = np.array([1, 2, 4, 8, 16, 32, 64], dtype=float)
        lengths = 2.5 * times ** 0.37
        selected = times >= 2
        self.assertAlmostEqual(log_slope(times, lengths, selected), 0.37, places=12)

    def test_short_or_unresolved_fit_is_not_filled(self):
        times = np.array([1, 2, 4, 8, 16], dtype=float)
        lengths = np.array([1, 2, np.nan, 3, 4], dtype=float)
        self.assertTrue(np.isnan(log_slope(times, lengths, times >= 4)))
        with self.assertRaisesRegex(ValueError, "Slope mismatch"):
            _check("Slope", 0.2, 0.3)


if __name__ == "__main__":
    unittest.main()
