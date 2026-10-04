"""Known-answer and direct-count checks for finite foreground chords."""

import unittest

import numpy as np

from research.chord_observation import foreground_chords, majority_observation


def direct_runs(mask, axis):
    """Independent scalar count of maximal foreground runs along one axis."""
    rows = mask if axis == 1 else mask.T
    retained, censored = [], 0
    for row in rows:
        cursor = 0
        while cursor < len(row):
            if row[cursor] == 0:
                cursor += 1
                continue
            start = cursor
            while cursor < len(row) and row[cursor] == 1:
                cursor += 1
            if start == 0 or cursor == len(row):
                censored += 1
            else:
                retained.append(cursor - start)
    return retained, censored


class ForegroundChordTests(unittest.TestCase):
    def test_analytic_tiled_checkerboards(self):
        for width in (1, 2, 4):
            size = 8 * width
            yy, xx = np.indices((size, size))
            mask = ((xx // width + yy // width) % 2).astype(np.uint8)
            result = foreground_chords(mask)
            self.assertEqual(result["status"], "resolved")
            self.assertEqual(result["chord"], width)
            self.assertEqual(result["chord_x"], width)
            self.assertEqual(result["chord_y"], width)
            self.assertEqual(result["complete_x"], 3 * size)
            self.assertEqual(result["complete_y"], 3 * size)
            self.assertEqual(result["censored_x"], size)
            self.assertEqual(result["censored_y"], size)
            self.assertEqual(result["censored_fraction"], 0.25)

    def test_physical_spacing_and_input_immutability(self):
        mask = np.zeros((8, 10), dtype=np.uint8)
        mask[2:6, 2:8] = 1
        original = mask.copy()
        raw, scaled = foreground_chords(mask), foreground_chords(mask, 0.3)
        for key in ("chord", "chord_x", "chord_y"):
            self.assertAlmostEqual(scaled[key], 0.3 * raw[key])
        self.assertEqual(raw["chord_x"], 6)
        self.assertEqual(raw["chord_y"], 4)
        # Four x-runs and six y-runs: number weighting is not (6+4)/2.
        self.assertEqual(raw["chord"], 4.8)
        self.assertEqual(raw["complete_chords"], 10)
        np.testing.assert_array_equal(mask, original)

    def test_transpose_and_mirror(self):
        mask = np.zeros((8, 10), dtype=np.uint8)
        mask[2:6, 2:8] = 1
        mask[0, :3] = 1
        result = foreground_chords(mask)
        transposed = foreground_chords(mask.T)
        self.assertEqual(result["chord"], transposed["chord"])
        for stem in ("chord_", "complete_", "censored_"):
            self.assertEqual(result[stem + "x"], transposed[stem + "y"])
            self.assertEqual(result[stem + "y"], transposed[stem + "x"])
        for reflected in (mask[::-1], mask[:, ::-1], mask[::-1, ::-1]):
            self.assertEqual(result, foreground_chords(reflected))

    def test_scalar_oracle_and_explicit_complement(self):
        rng = np.random.default_rng(761)
        for shape in ((4, 4), (8, 13), (17, 6)):
            for fraction in (0.15, 0.5, 0.85):
                mask = (rng.random(shape) < fraction).astype(np.uint8)
                for sample in (mask, 1 - mask):
                    result = foreground_chords(sample)
                    xs, cx = direct_runs(sample, 1)
                    ys, cy = direct_runs(sample, 0)
                    self.assertEqual(result["complete_x"], len(xs))
                    self.assertEqual(result["complete_y"], len(ys))
                    self.assertEqual(result["censored_x"], cx)
                    self.assertEqual(result["censored_y"], cy)
                    if xs and ys:
                        self.assertAlmostEqual(result["chord"], np.mean(xs + ys))
                    else:
                        self.assertTrue(np.isnan(result["chord"]))
        # The complement of a bounded foreground square has only censored
        # foreground runs here. Complement invariance is not a valid demand.
        square = np.zeros((8, 8), dtype=np.uint8)
        square[2:6, 2:6] = 1
        self.assertEqual(foreground_chords(square)["chord"], 4)
        self.assertTrue(np.isnan(foreground_chords(1 - square)["chord"]))

    def test_border_slab_retains_censoring_and_is_unresolved(self):
        slab = np.zeros((8, 8), dtype=np.uint8)
        slab[:, 2:5] = 1
        result = foreground_chords(slab)
        self.assertEqual(result["complete_x"], 8)
        self.assertEqual(result["chord_x"], 3)
        self.assertEqual(result["complete_y"], 0)
        self.assertEqual(result["censored_y"], 3)
        self.assertEqual(result["status"], "unresolved_no_complete_chords_y")
        self.assertTrue(np.isnan(result["chord"]))
        self.assertAlmostEqual(result["censored_fraction"], 3 / 11)
        # A corner component is border-censored in both directions, and may
        # not be wrapped around to manufacture complete foreground chords.
        corner = np.zeros((8, 8), dtype=np.uint8)
        corner[:3, :2] = 1
        result = foreground_chords(corner)
        self.assertEqual(result["complete_chords"], 0)
        self.assertEqual(result["censored_foreground_runs"], 5)
        self.assertTrue(np.isnan(result["chord"]))

    def test_constant_empty_and_full(self):
        empty = foreground_chords(np.zeros((4, 7), dtype=bool))
        full = foreground_chords(np.ones((4, 7), dtype=bool))
        for result in (empty, full):
            self.assertTrue(np.isnan(result["chord"]))
            self.assertEqual(result["complete_chords"], 0)
            self.assertEqual(result["status"], "unresolved_no_complete_chords_both")
        self.assertEqual(empty["censored_foreground_runs"], 0)
        self.assertTrue(np.isnan(empty["censored_fraction"]))
        self.assertEqual(full["censored_foreground_runs"], 11)
        self.assertEqual(full["censored_fraction"], 1)

    def test_invalid_inputs(self):
        invalid = (
            np.zeros((3, 4)), np.zeros(16), np.zeros((4, 4, 4)),
            np.full((4, 4), 0.5), np.full((4, 4), -1),
            np.full((4, 4), np.nan), np.full((4, 4), np.inf),
            np.ones((4, 4), dtype=complex), np.full((4, 4), "1"),
        )
        for sample in invalid:
            with self.subTest(shape=sample.shape, dtype=sample.dtype):
                with self.assertRaises(ValueError):
                    foreground_chords(sample)
                with self.assertRaises(ValueError):
                    majority_observation(sample)
        for spacing in (0, -1, float("nan"), float("inf"), [1, 2], 1j, "1", True):
            with self.subTest(spacing=spacing):
                with self.assertRaises(ValueError):
                    foreground_chords(np.zeros((4, 4)), spacing)


class MajorityObservationTests(unittest.TestCase):
    def test_isolated_spike_removed_without_mutation(self):
        mask = np.zeros((8, 8), dtype=np.uint8)
        mask[3, 3] = 1
        original = mask.copy()
        filtered = majority_observation(mask)
        self.assertEqual(filtered.dtype, np.uint8)
        self.assertEqual(filtered.shape, mask.shape)
        self.assertEqual(filtered.sum(), 0)
        np.testing.assert_array_equal(mask, original)
        self.assertFalse(np.shares_memory(filtered, mask))

    def test_periodic_neighbours_and_direct_rule(self):
        mask = np.zeros((6, 8), dtype=np.uint8)
        mask[0, 0] = mask[0, -1] = mask[-1, 0] = 1
        result = majority_observation(mask)
        self.assertEqual(result[0, 0], 1)
        expected = np.zeros_like(mask)
        for y in range(mask.shape[0]):
            for x in range(mask.shape[1]):
                total = sum(int(mask[yy % mask.shape[0], xx % mask.shape[1]])
                            for yy, xx in ((y, x), (y - 1, x), (y + 1, x),
                                           (y, x - 1), (y, x + 1)))
                expected[y, x] = total >= 3
        np.testing.assert_array_equal(result, expected)

    def test_simultaneous_checkerboard_flip_and_constants(self):
        yy, xx = np.indices((8, 10))
        mask = ((yy + xx) % 2).astype(np.uint8)
        np.testing.assert_array_equal(majority_observation(mask), 1 - mask)
        for value in (0, 1):
            constant = np.full((4, 4), value, dtype=np.uint8)
            np.testing.assert_array_equal(majority_observation(constant), constant)


if __name__ == "__main__":
    unittest.main()
