import csv
import tempfile
import unittest
from pathlib import Path

from research.plot_alge_static_operator import load_fixed_rows


class FixedAlGePlotInputTests(unittest.TestCase):
    def test_requires_complete_grid_and_consistent_resolution(self):
        fields = [
            "minutes", "target_z_um", "ratio_altered_to_native",
            "measurement_status"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.csv"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for stage in (15, 105, 195, 315):
                    for j in range(11):
                        writer.writerow({
                            "minutes": stage,
                            "target_z_um": round(12 + 0.6 * j, 1),
                            "ratio_altered_to_native": 1.2,
                            "measurement_status": "resolved",
                        })
            self.assertEqual(len(load_fixed_rows(path)[195]), 11)
            lines = path.read_text().splitlines()
            path.write_text("\n".join(lines[:-1]) + "\n")
            with self.assertRaisesRegex(ValueError, "11 preselected"):
                load_fixed_rows(path)


if __name__ == "__main__":
    unittest.main()
