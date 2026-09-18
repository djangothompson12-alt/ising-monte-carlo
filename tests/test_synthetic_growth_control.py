import unittest

import numpy as np

from research.synthetic_growth_control import calculate, prescribed_pattern, slope


class SyntheticGrowthControlTests(unittest.TestCase):
    def test_known_geometry_and_phase_fraction(self):
        field = prescribed_pattern(384, 12)
        self.assertEqual(field.shape, (384, 384))
        self.assertEqual(set(np.unique(field)), {-1, 1})
        self.assertEqual(float((field > 0).mean()), 0.5)
        self.assertTrue(np.all(field[:24, :24] == -1))
        self.assertTrue(np.all(field[:24, 24:48] == 1))

    def test_invalid_noninteger_repeat_field(self):
        with self.assertRaises(ValueError):
            prescribed_pattern(380, 12)

    def test_prescribed_growth_exact_and_all_conditions_retained(self):
        rows, fits = calculate()
        self.assertEqual(len(rows), 54)
        self.assertEqual(len(fits), 9)
        self.assertTrue(all(row["resolved"] for row in rows))
        self.assertTrue(all(abs(fit["prescribed_slope"] - 1 / 3) < 1e-12 for fit in fits))
        self.assertTrue(all(np.isfinite(fit["measured_slope"]) for fit in fits))
        native = {fit["field_width_sites"]: fit["measured_slope"] for fit in fits if fit["operator"] == "native"}
        self.assertGreater(native[384], native[768])
        self.assertGreater(native[768], native[1536])

    def test_slope_rejects_unresolved(self):
        with self.assertRaises(ValueError):
            slope(np.arange(1, 5), np.array([1.0, 2.0, np.nan, 4.0]))


if __name__ == "__main__":
    unittest.main()
