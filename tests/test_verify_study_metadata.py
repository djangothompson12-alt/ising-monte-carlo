"""Archived file names, seeds and configurations must agree with the plan."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from research.imaging_benchmark import sha
from research.verify_study import verify


ROOT = Path(__file__).resolve().parents[1]


class MetadataVerificationTests(unittest.TestCase):
    def test_seed_mismatch_is_rejected_even_if_unique(self):
        plan = dict(sizes=[4], concentrations=[0.5], replicas=1,
                    max_sweeps=10, time_samples=2, equilibration=0,
                    Jx=1.0, Jy=1.0, seed=2026)
        seed = int(np.random.SeedSequence([plan["seed"], 0, 0, 0]).generate_state(1)[0])
        config = dict(L=4, concentration=0.5, n_replicas=1, max_sweeps=10,
                      n_time_samples=2, eq_sweeps_initial=0, Jx=1.0,
                      Jy=1.0, seed=seed)
        lattice = np.tile(np.array([[1, -1], [-1, 1]], dtype=np.int8), (2, 2))
        sources = {name: sha(ROOT / name)
                   for name in ("model_b/kawasaki_engine.py", "research/campaign.py")}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "manifest.json").write_text(json.dumps({
                "identity": {"plan": plan, "sources": sources}}))
            path = folder / "c0_L4_rep000.npz"

            def save():
                np.savez_compressed(path, config=json.dumps(config),
                                    t=np.array([1, 10]),
                                    snapshots=np.array([lattice, lattice]),
                                    magnetization=int(lattice.sum()),
                                    realized_concentration=0.5,
                                    delta_energy=np.array([0., 0.]))

            save()
            self.assertEqual(verify(folder)["replicas"], 1)
            config["seed"] = seed + 1
            save()
            with self.assertRaisesRegex(ValueError, "config seed"):
                verify(folder)


if __name__ == "__main__":
    unittest.main()
