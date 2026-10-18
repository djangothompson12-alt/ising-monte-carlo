"""Independent regression and sharp box-bound checks; not physical validation."""

import itertools
import unittest

import numpy as np

from research.kinetic_error_budget import (log_time_weights, paired_budget,
    ratio_envelope_bound, required_static_tolerance, static_tolerance_bound)


class KineticErrorBudgetTests(unittest.TestCase):
    def test_exact_power_and_constant_multiplicative_error(self):
        times = np.geomspace(100, 20000, 24)
        native = 3 * times ** (1 / 3)
        result = paired_budget(times, native, 1.1 * native)
        self.assertAlmostEqual(result["native_alpha"], 1 / 3)
        self.assertAlmostEqual(result["delta"], 0.)
        self.assertAlmostEqual(result["observed_ratio_envelope_bound"], 0.)

    def test_known_time_dependent_ratio_and_independent_least_squares(self):
        times = np.array([7, 9, 25, 80, 100, 500], dtype=float)
        native = 2 * times ** .31
        processed = native * 1.2 * times ** -.045
        result = paired_budget(times, native, processed)
        self.assertAlmostEqual(result["delta"], -.045)
        design = np.column_stack([np.ones(times.size), np.log(times)])
        a = np.linalg.lstsq(design, np.log(native), rcond=None)[0][1]
        b = np.linalg.lstsq(design, np.log(processed), rcond=None)[0][1]
        self.assertAlmostEqual(result["delta"], b - a)

    def test_two_endpoint_bound_has_the_expected_closed_form(self):
        times = [10, 1000]
        expected = np.log(1.1 / .9) / np.log(100)
        self.assertAlmostEqual(static_tolerance_bound(times, .1), expected)

    def test_sharp_bound_is_attained_and_covers_every_box_corner(self):
        times = np.array([1., 2., 8., 13., 40.])
        weights = log_time_weights(times)
        lower, upper = .94, 1.06
        bound = ratio_envelope_bound(times, lower, upper)
        all_slopes = [float(weights @ np.log(q))
                      for q in itertools.product((lower, upper), repeat=len(times))]
        self.assertAlmostEqual(max(all_slopes), bound)
        self.assertAlmostEqual(min(all_slopes), -bound)
        sharp = np.where(weights >= 0, upper, lower)
        self.assertAlmostEqual(float(weights @ np.log(sharp)), bound)

    def test_small_static_error_can_still_exceed_an_exponent_budget(self):
        times = np.geomspace(1000, 20000, 24)
        weights = log_time_weights(times)
        native = times ** (1 / 3)
        q = np.where(weights >= 0, 1.05, .95)
        result = paired_budget(times, native, native * q)
        self.assertLessEqual(result["max_relative_length_change"], .05 + 1e-14)
        self.assertGreater(abs(result["delta"]), .02)
        self.assertAlmostEqual(abs(result["delta"]), static_tolerance_bound(times, .05))

    def test_inverse_tolerance_is_sufficient_and_not_claimed_necessary(self):
        times = np.array([2., 3., 7., 50., 900.])
        epsilon = required_static_tolerance(times, .02)
        self.assertAlmostEqual(static_tolerance_bound(times, epsilon), .02)
        self.assertEqual(required_static_tolerance(times, 0), 0.)
        self.assertEqual(static_tolerance_bound(times, 0), 0.)

    def test_time_units_and_uniform_length_units_do_not_change_budget(self):
        times = np.geomspace(10, 10000, 20)
        native = times ** .27
        processed = native * times ** -.02
        base = paired_budget(times, native, processed)
        changed = paired_budget(times * 60, native * 1e-6, processed * 1e-6)
        for name in ("native_alpha", "processed_alpha", "delta", "observed_ratio_envelope_bound"):
            self.assertAlmostEqual(base[name], changed[name])
        self.assertAlmostEqual(static_tolerance_bound(times, .1),
                               static_tolerance_bound(times * 60, .1))

    def test_invalid_grids_and_unresolved_lengths_are_not_silently_dropped(self):
        for times in ([0, 2], [2, 2], [3, 2], [1, np.nan], [1], [[1, 2]]):
            with self.assertRaises(ValueError):
                log_time_weights(times)
        for values in ([1, np.nan], [1, 0], [1], [1, np.inf]):
            with self.assertRaises(ValueError):
                paired_budget([1, 2], [1, 2], values)
        for epsilon in (-.1, 1, np.inf, np.nan, True):
            with self.assertRaises(ValueError):
                static_tolerance_bound([1, 2], epsilon)
        for lower, upper in ((0, 1), (1, .9), (1, np.inf)):
            with self.assertRaises(ValueError):
                ratio_envelope_bound([1, 2], lower, upper)


if __name__ == "__main__":
    unittest.main()
