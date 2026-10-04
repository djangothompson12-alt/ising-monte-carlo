import unittest
import numpy as np

from research.growth_reliability import paired_fit
from research.observation_sensitivity import (
    common_mask, series_arrays, contrast_definitions, fit_comparison, original_primary_check,
)


class ObservationSensitivityTests(unittest.TestCase):
    def test_one_invalid_tie_removes_time_globally(self):
        raw = np.ones((2, 8, 6, 7))
        raw[1, 3, 2, 5] = np.nan
        raw[0, 0, 4, 1] = 0
        np.testing.assert_array_equal(common_mask(raw), [True, True, False, True, False, True])
        with self.assertRaises(ValueError):
            common_mask(np.ones((2, 8, 6, 6)))

    def test_ties_average_lengths_not_slopes_and_keep_eight_runs(self):
        raw = np.ones((2, 8, 6, 7))
        raw[:, :, :, 0] = 2
        raw[:, :, :, 1] = 3
        raw[:, :, :, 2:] = np.arange(5) + 1
        result = series_arrays(raw)
        self.assertEqual(result.shape, (6, 8, 6))
        np.testing.assert_array_equal(result[0], 2)
        np.testing.assert_array_equal(result[1], 3)
        np.testing.assert_array_equal(result[2], 3)

    def test_constant_scale_preserves_exponent_and_time_bias_shifts_it(self):
        t = np.geomspace(1000, 20000, 24)
        native = np.arange(1, 9)[:, None] * t ** (1 / 3)
        values = np.stack([native, native * 1.1, native * t ** -.07,
                           native * 2, native * 2.2, native * 2 * t ** -.07])
        fits, contrasts = fit_comparison(t, values)
        np.testing.assert_allclose([r["alpha"] for r in fits],
            [1/3, 1/3, 1/3-.07, 1/3, 1/3, 1/3-.07], atol=1e-14)
        self.assertEqual(len(contrasts), 9)
        np.testing.assert_allclose([r["delta"] for r in contrasts],
            [0, -.07, 0, -.07, 0, 0, 0, 0, 0], atol=1e-14)

    def test_paired_intervals_match_existing_independent_function(self):
        t = np.geomspace(1000, 20000, 24)
        rng = np.random.default_rng(345)
        values = np.exp(rng.normal(0, .1, (6, 8, 24))) * t[None, None, :] ** .24
        _, contrasts = fit_comparison(t, values)
        for offset, base in enumerate((0, 3)):
            for op in (1, 2):
                reference = paired_fit(t, values[base], values[base + op])
                result = contrasts[offset * 2 + op - 1]
                for key in ("delta", "low", "high"):
                    self.assertAlmostEqual(result[key], reference[key], places=13)

    def test_rejects_unresolved_values_short_spans_and_pseudoreplicates(self):
        t = np.geomspace(1, 20, 5)
        values = np.ones((6, 8, 5))
        for times in (t[:3], np.arange(10, 15), np.array([1, 2, 2, 4, 20])):
            with self.assertRaises(ValueError):
                fit_comparison(times, values)
        with self.assertRaises(ValueError):
            fit_comparison(t, values[:, :1])
        values[1, 2, 3] = np.nan
        with self.assertRaises(ValueError):
            fit_comparison(t, values)

    def test_all_contrasts_are_zero_sum_and_include_both_interactions(self):
        definitions = contrast_definitions()
        self.assertEqual(len(definitions), 9)
        self.assertEqual(sum(kind == "interaction" for _, _, kind in definitions), 2)
        for _, weights, _ in definitions:
            self.assertEqual(weights.sum(), 0)

    def test_original_primary_does_not_use_new_chord_or_majority_mask(self):
        t = np.geomspace(1000, 20000, 24)
        raw = np.ones((2, 8, 24, 7)) * t[None, None, :, None] ** .25
        raw[0, :, :, 2:] *= t[None, :, None] ** -.04
        arrays = series_arrays(raw)
        reference = paired_fit(t, arrays[0], arrays[1])
        row = dict(composition="0.5", factor="4", origin="0", observable="half",
                   stage="matched", retained_points="24", **{k: str(v) for k, v in reference.items()})
        raw[1, 0, 0, 0] = np.nan
        raw[0, 0, 1, 1] = np.nan
        self.assertEqual(common_mask(raw).sum(), 22)
        result = original_primary_check(t, raw, .5, [row])
        self.assertEqual(result["points"], 24)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
