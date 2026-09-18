import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from research.analyse_main_extension import analyse, matched_size_ratios
from research.audit_main_extension import audit
from research.render_extension_appendix import check_inputs, write_appendix


class MatchedSizeComparisonTests(unittest.TestCase):
    def test_constant_ratio_and_missing_direction(self):
        times = np.array([1, 10, 100])
        smaller = np.full((4, 3, 2), 4.0)
        reference = np.full((4, 3, 2), 5.0)
        rows = matched_size_ratios(times, smaller, reference,
                                   composition=0.5, smaller_L=32, draws=30)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["status"], "resolved")
            self.assertAlmostEqual(row["ratio"], 0.8)
            self.assertAlmostEqual(row["ratio_low"], 0.8)
            self.assertAlmostEqual(row["ratio_high"], 0.8)
            self.assertAlmostEqual(row["difference_sites"], -1.0)

        smaller[0, 2, 1] = np.nan
        rows = matched_size_ratios(times, smaller, reference,
                                   composition=0.5, smaller_L=32, draws=30)
        self.assertEqual(rows[-1]["status"], "unresolved")
        self.assertFalse(rows[-1]["resolved_small"])
        self.assertTrue(np.isnan(rows[-1]["ratio"]))
        self.assertEqual(rows[0]["status"], "resolved")

    def test_invalid_shape_rejected(self):
        with self.assertRaises(ValueError):
            matched_size_ratios(np.array([1, 2]), np.ones((1, 2, 2)),
                                np.ones((2, 2, 2)), composition=0.5, smaller_L=32)

    def test_complete_synthetic_campaign_generates_matched_time_table(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            campaign = root / "campaign"
            campaign.mkdir()
            times = np.array([1, 100, 1000, 20000, 200000, 1000000])
            plan = {"sizes": [32, 64, 96, 128], "concentrations": [0.5, 0.15],
                    "max_sweeps": 1000000, "replicas": 16, "T_final_over_tc": 0.65}
            (campaign / "manifest.json").write_text(json.dumps({"identity": {"plan": plan}}))
            (campaign / "status.json").write_text(json.dumps({"state": "complete", "completed": 128}))
            for ci in range(2):
                for side in plan["sizes"]:
                    for replica in range(16):
                        base = 1.5 * times.astype(float) ** 0.2 * (1 + 0.002 * replica)
                        if side == 32:
                            base = np.minimum(base, 7.0)
                        lengths = np.column_stack((base, base))
                        np.savez_compressed(campaign / f"c{ci}_L{side}_rep{replica:03d}.npz",
                                            t=times, lengths=lengths)
            destination = root / "analysis"
            result = analyse(campaign, destination)
            self.assertTrue(result.is_file())
            with (destination / "matched_size_ratios.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2 * 3 * len(times))
            self.assertTrue(all(row["status"] == "resolved" for row in rows))
            l32 = [row for row in rows if row["composition"] == "0.5" and row["L"] == "32"]
            self.assertLess(float(l32[-1]["ratio"]), float(l32[0]["ratio"]))
            self.assertIn("matched_size_addendum_sha256",
                          json.loads((destination / "manifest.json").read_text()))
            independent_check = audit(campaign, destination)
            self.assertEqual(independent_check["raw_files_checked"], 128)
            self.assertEqual(independent_check["fit_rows_checked"], 80)
            self.assertEqual(independent_check["matched_size_rows_checked"], 2 * 3 * len(times))
            (destination / "independent_table_audit.json").write_text(
                json.dumps(independent_check))
            appendix = write_appendix(campaign, destination, destination / "appendix")
            self.assertTrue(appendix.is_file())
            self.assertEqual(appendix.read_text().count("| 0.50 | 32 | 1000–20000 |"), 2)
            self.assertIn("not a physical alloy ageing rate", appendix.read_text())
            raw_path = campaign / "c0_L32_rep000.npz"
            original_bytes = raw_path.read_bytes()
            raw_path.write_bytes(original_bytes + b"tampered")
            with self.assertRaisesRegex(ValueError, "Raw trajectory changed"):
                check_inputs(campaign, destination)
            raw_path.write_bytes(original_bytes)
            fit_path = destination / "fit_windows.csv"
            with fit_path.open(newline="") as stream:
                fit_rows = list(csv.DictReader(stream))
            fit_rows[0]["alpha"] = "9.0"
            with fit_path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(fit_rows[0]))
                writer.writeheader()
                writer.writerows(fit_rows)
            with self.assertRaisesRegex(ValueError, "alpha"):
                audit(campaign, destination)
            with self.assertRaisesRegex(ValueError, "changed after"):
                check_inputs(campaign, destination)


if __name__ == "__main__":
    unittest.main()
