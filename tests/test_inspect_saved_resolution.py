import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.inspect_saved_resolution import coverage, inspect_archive


class SavedResolutionTests(unittest.TestCase):
    def test_no_silent_replica_drop_or_partial_direction(self):
        first = dict(config={"L": 128}, times=[1000, 2000, 5000, 10000],
                     native_directional_lengths=[[12, 12], [13, 13], [14, 14], [20, 20]])
        second = dict(first, native_directional_lengths=[[11, 12], [13, np.nan], [14, 14], [20, 20]])
        result = coverage([first, second], 4)
        self.assertEqual(result["native_three_pixel_proxy"]["times"], [5000, 10000])
        self.assertEqual(result["proxy_and_directional_size_screen"]["times"], [5000])
        with self.assertRaises(ValueError):
            coverage([first, dict(second, times=[1, 2, 3, 4])], 4)

    def test_archive_read_does_not_modify_and_rejects_incomplete(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "example.npz"
            y, x = np.indices((16, 16))
            spin = (2 * ((x // 4 + y // 4) % 2) - 1).astype(np.int8)
            snapshots = np.stack([spin] * 3)
            config = {"L": 16, "max_sweeps": 5000}
            np.savez(path, t=[1, 1000, 5000], snapshots=snapshots,
                     config=json.dumps(config))
            original = path.read_bytes()
            result = inspect_archive(path)
            self.assertEqual(result["times"], [1000, 5000])
            self.assertEqual(result["saved_snapshots"], 3)
            self.assertEqual(len(result["sha256"]), 64)
            self.assertEqual(original, path.read_bytes())
            config["max_sweeps"] = 10000
            np.savez(path, t=[1, 1000, 5000], snapshots=snapshots,
                     config=json.dumps(config))
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                inspect_archive(path)


if __name__ == "__main__":
    unittest.main()
