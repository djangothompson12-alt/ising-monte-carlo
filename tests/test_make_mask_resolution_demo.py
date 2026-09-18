"""A reviewer should be able to create and inspect the synthetic audit."""

import csv
from pathlib import Path
import tempfile
import unittest

from research.make_mask_resolution_demo import make


class MaskAuditDemoTests(unittest.TestCase):
    def test_demo_is_self_contained_and_clearly_synthetic(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "demo"
            report = make(folder)
            self.assertTrue(report.is_file())
            self.assertIn("not materials data", report.read_text())
            self.assertTrue((folder / "input_plan.json").is_file())
            self.assertTrue((folder / "synthetic_mask.npy").is_file())
            self.assertTrue((folder / "empty_mask.npy").is_file())
            with (folder / "audit" / "measurements.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([int(row["factor"]) for row in rows], [1, 2, 4, 1, 2, 4])
            self.assertTrue(all(row["length_unit"] == "arbitrary pixel units"
                                for row in rows))
            self.assertEqual([row["status"] for row in rows[3:]],
                             ["unresolved crossing"] * 3)
            with self.assertRaises(FileExistsError):
                make(folder)


if __name__ == "__main__":
    unittest.main()
