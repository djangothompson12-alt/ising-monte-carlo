"""Deterministic limits of the paper-like observation path, not a paper replication."""

import unittest

import numpy as np

from research.reference_measurements import (
    majority_filter_once, periodic_chord_lengths, reference_measurements,
)


class TestReferenceMeasurementsContract(unittest.TestCase):
    def test_periodic_stripe_has_half_box_chords(self) -> None:
        lattice = np.ones((8, 8), dtype=np.int8)
        lattice[:, 4:] = -1
        np.testing.assert_array_equal(majority_filter_once(lattice), lattice)
        x_chords = periodic_chord_lengths(lattice, axis=1)
        y_chords = periodic_chord_lengths(lattice, axis=0)
        np.testing.assert_array_equal(x_chords, np.full(16, 4.0))
        self.assertEqual(len(y_chords), 0)  # Uniform lines have no interfaces.
        measured = reference_measurements(lattice)
        self.assertEqual(measured["mean_chord_length"], 4.0)
        self.assertTrue(np.isnan(measured["first_zero_correlation"]))

    def test_periodic_seam_does_not_split_one_chord(self) -> None:
        lattice = np.ones((8, 8), dtype=np.int8)
        lattice[:, 2:5] = -1
        # Each row crosses the periodic seam inside the 5-site +1 chord.
        lengths = periodic_chord_lengths(lattice, axis=1)
        self.assertEqual(len(lengths), 16)
        np.testing.assert_array_equal(np.sort(lengths), np.r_[np.full(8, 3.0), np.full(8, 5.0)])

    def test_majority_filter_is_observation_only_and_can_change_composition(self) -> None:
        lattice = np.ones((8, 8), dtype=np.int8)
        lattice[3, 4] = -1
        before = lattice.copy()
        filtered = majority_filter_once(lattice)
        np.testing.assert_array_equal(lattice, before)
        self.assertEqual(int(filtered.sum()), 64)
        self.assertNotEqual(int(before.sum()), int(filtered.sum()))


if __name__ == "__main__":
    unittest.main()
