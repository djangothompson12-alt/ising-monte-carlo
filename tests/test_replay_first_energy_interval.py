"""The first heat interval is checked against the seeded prepared state."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from model_b import kawasaki_engine as engine
from research.replay_first_energy_interval import energy, replay_file


class FirstIntervalReplayTests(unittest.TestCase):
    def test_correct_interval_and_corruption(self):
        config = engine.KawasakiConfig(L=8, concentration=0.25, seed=817,
                                       eq_sweeps_initial=2, max_sweeps=10)
        prepared = engine._seed_and_init_lattice(config.L, config.seed,
                                                 config.concentration)
        engine._run_n_sweeps(prepared, 1 / config.T_initial, config.Jx,
                             config.Jy, config.eq_sweeps_initial)
        first = prepared.copy()
        delta = engine._run_n_sweeps_with_heat(first, 1 / config.T_final,
                                               config.Jx, config.Jy, 2)
        self.assertAlmostEqual(delta, energy(first, config.Jx, config.Jy)
                               - energy(prepared, config.Jx, config.Jy))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.npz"
            values = dict(config=json.dumps(config.__dict__),
                          snapshots=np.array([first]), delta_energy=np.array([delta]))
            np.savez_compressed(path, **values)
            computed, reported = replay_file(path)
            self.assertEqual(computed, reported)
            values["delta_energy"] = np.array([delta + 1])
            np.savez_compressed(path, **values)
            with self.assertRaisesRegex(ValueError, "First heat interval disagrees"):
                replay_file(path)
            corrupt = first.copy()
            corrupt[0, 0] = -corrupt[0, 0]
            values["snapshots"] = np.array([corrupt])
            values["delta_energy"] = np.array([delta])
            np.savez_compressed(path, **values)
            with self.assertRaisesRegex(ValueError, "conserved spin count"):
                replay_file(path)


if __name__ == "__main__":
    unittest.main()
