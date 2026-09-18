import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.plot_archived_morphology import selected_states


class ArchivedMorphologyTests(unittest.TestCase):
    def test_exact_times_and_conservation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.npz"
            state = np.ones((128, 128), dtype=np.int8)
            np.savez(source, t=np.array([1069, 200000]), snapshots=np.stack([state, state]),
                     magnetization=state.sum(), config=json.dumps(dict(L=128)))
            _, states = selected_states(source)
            self.assertEqual(len(states), 2)
            self.assertEqual(int(states[0].sum()), 128 * 128)
            np.savez(source, t=np.array([1069, 10000]), snapshots=np.stack([state, state]),
                     magnetization=state.sum(), config=json.dumps(dict(L=128)))
            with self.assertRaisesRegex(ValueError, "Missing or duplicate"):
                selected_states(source)


if __name__ == "__main__":
    unittest.main()
