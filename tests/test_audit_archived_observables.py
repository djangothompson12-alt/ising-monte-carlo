import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from research.audit_archived_observables import (
    _threshold_rounding_ambiguity, audit_campaign,
    correlations_from_snapshot, half_height_length,
)


class ArchivedObservableAuditTests(unittest.TestCase):
    def test_fft_correlations_match_direct_pairs_at_every_separation(self):
        rng = np.random.default_rng(12)
        snapshot = rng.choice(np.array([-1, 1], dtype=np.int8), size=(10, 10))
        observed = correlations_from_snapshot(snapshot)
        mean = float(snapshot.mean())
        variance = 1.0 - mean * mean
        for row, axis in ((0, 1), (1, 0)):
            for separation in range(6):
                raw = float(np.mean(snapshot * np.roll(snapshot, -separation, axis=axis)))
                expected = (raw - mean * mean) / variance
                self.assertAlmostEqual(observed[row, separation], expected, places=12)

    def test_half_height_crossing_and_unresolved(self):
        self.assertAlmostEqual(half_height_length([1.0, 0.75, 0.25]), 1.5)
        self.assertTrue(np.isnan(half_height_length([1.0, 0.8, 0.6])))
        self.assertTrue(np.isnan(half_height_length([1.0, np.nan, 0.2])))

    def test_strict_half_height_boundary_can_flip_under_fft_roundoff(self):
        fresh = np.array([1.0, 0.7, 0.4999999999999999])
        archived = np.array([1.0, 0.7, 0.5000000000000001])
        self.assertTrue(np.isfinite(half_height_length(fresh)))
        self.assertTrue(np.isnan(half_height_length(archived)))
        self.assertTrue(_threshold_rounding_ambiguity(fresh, archived))
        self.assertFalse(_threshold_rounding_ambiguity(
            np.array([1.0, 0.7, 0.4]), np.array([1.0, 0.7, 0.4])
        ))

    def test_archive_audit_detects_corrupt_length(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            rng = np.random.default_rng(3)
            snapshots = rng.choice(np.array([-1, 1], dtype=np.int8), size=(2, 8, 8))
            correlations = np.stack([correlations_from_snapshot(item) for item in snapshots])
            lengths = np.asarray([
                [half_height_length(row) for row in pair] for pair in correlations
            ])
            interfaces = np.asarray([
                sum(np.count_nonzero(item != np.roll(item, 1, axis=axis)) for axis in (0, 1))
                / (2 * item.size) for item in snapshots
            ])
            plan = {"replicas": 1, "concentrations": [0.5], "sizes": [8]}
            (folder / "manifest.json").write_text(json.dumps({"identity": {"plan": plan}}))
            (folder / "status.json").write_text(json.dumps({"state": "complete", "completed": 1}))
            path = folder / "c0_L8_rep000.npz"
            np.savez_compressed(path, snapshots=snapshots, correlations=correlations,
                                lengths=lengths, interfaces=interfaces)
            result = audit_campaign(folder)
            self.assertEqual(result["snapshots_checked"], 2)
            self.assertEqual(result["directional_lengths_checked"], 4)
            changed = lengths.copy()
            changed[0, 0] = 10.0
            np.savez_compressed(path, snapshots=snapshots, correlations=correlations,
                                lengths=changed, interfaces=interfaces)
            with self.assertRaisesRegex(ValueError, "Length mismatch"):
                audit_campaign(folder)


if __name__ == "__main__":
    unittest.main()
