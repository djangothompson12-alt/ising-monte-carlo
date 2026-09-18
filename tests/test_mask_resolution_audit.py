"""Contract checks for the user-facing, expert-mask resolution audit."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.mask_resolution_audit import audit, load_mask, measure
from research.metaldam_reference_mask_scale import measure_factor


class MaskResolutionAuditTests(unittest.TestCase):
    def fixture(self, folder: Path) -> tuple[Path, dict]:
        y, x = np.indices((64, 64))
        mask = (((y // 8 + x // 8) % 2) * 255).astype(np.uint8)
        np.save(folder / "expert_mask.npy", mask)
        document = dict(
            source="synthetic test", license="synthetic only",
            phase_definition="checkerboard foreground", tie_rule="background",
            records=[dict(
                id="first", specimen_id="one synthetic specimen",
                mask_path="expert_mask.npy", foreground_value=255,
                background_value=0, mask_authority="synthetic known mask",
                roi=[8, 56, 8, 56], roi_reason="fixed interior field",
                pixel_size=0.06, length_unit="um", time=15, time_unit="min",
            )],
        )
        path = folder / "input.json"
        path.write_text(json.dumps(document))
        return path, document

    def test_report_keeps_native_and_coarse_measurements_in_physical_units(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, _ = self.fixture(folder)
            original = np.load(folder / "expert_mask.npy").copy()
            report = audit(manifest, folder / "audit")
            self.assertTrue(report.is_file())
            with (folder / "audit" / "measurements.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([int(row["factor"]) for row in rows], [1, 2, 4])
            self.assertEqual([float(row["pixel_size"]) for row in rows], [.06, .12, .24])
            self.assertEqual(float(rows[0]["length_ratio"]), 1)
            self.assertTrue(all(row["specimen_id"] == "one synthetic specimen" for row in rows))
            self.assertEqual(rows[0]["length_unit"], "um")
            html = report.read_text()
            self.assertIn("Repeated slices from one", html)
            self.assertIn("<th>Unit</th>", html)
            self.assertIn("<td>um</td>", html)
            self.assertIn("<td>15 min</td>", html)
            self.assertNotIn("data:image", html)
            self.assertNotIn("expert_mask.npy", html)
            provenance = json.loads((folder / "audit" / "manifest.json").read_text())
            self.assertEqual(len(provenance["mask_sha256"]["first"]), 64)
            self.assertEqual(provenance["input_settings"][0]["roi"], [8, 56, 8, 56])
            self.assertEqual(provenance["input_settings"][0]["pixel_size"], .06)
            self.assertNotIn("mask_path", provenance["input_settings"][0])
            self.assertTrue(np.array_equal(np.load(folder / "expert_mask.npy"), original))
            with self.assertRaises(FileExistsError):
                audit(manifest, folder / "audit")

    def test_unresolved_and_half_block_tie_rule_are_explicit(self):
        mask = np.zeros((16, 16), dtype=bool)
        self.assertEqual(measure(mask, 4, .05, True)["status"], "unresolved crossing")
        mask[::2, :] = True  # Every 2×2 block has a 50:50 tie.
        foreground = measure(mask, 2, .05, True)
        background = measure(mask, 2, .05, False)
        self.assertEqual(foreground["tie_block_fraction"], 1)
        self.assertEqual(foreground["phase_fraction"], 1)
        self.assertEqual(background["phase_fraction"], 0)

    def test_matches_the_existing_public_mask_measurement_kernel(self):
        y, x = np.indices((64, 64))
        mask = ((y // 8 + x // 8) % 2).astype(bool)
        for factor in (2, 4):
            public = measure_factor(mask, factor, tie_to_class_one=False)
            reusable = measure(mask, factor, 1.0, ties_to_foreground=False)
            self.assertAlmostEqual(reusable["length"], public["coarse_length_original_px"])
            self.assertAlmostEqual(reusable["phase_fraction"], public["coarse_fraction"])
            self.assertAlmostEqual(reusable["tie_block_fraction"], public["tie_block_fraction"])

    def test_undeclared_labels_and_nondivisible_roi_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            changed = np.load(folder / "expert_mask.npy")
            changed[0, 0] = 127
            np.save(folder / "expert_mask.npy", changed)
            with self.assertRaisesRegex(ValueError, "undeclared label"):
                load_mask(folder / "expert_mask.npy", 255, 0)
            with self.assertRaisesRegex(ValueError, "undeclared label"):
                audit(manifest, folder / "bad_mask")
            self.assertFalse((folder / "bad_mask").exists())
            changed[0, 0] = 0
            np.save(folder / "expert_mask.npy", changed)
            document["records"][0]["roi"] = [8, 55, 8, 56]
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, "divide exactly by 4"):
                audit(manifest, folder / "bad_roi")
            self.assertFalse((folder / "bad_roi").exists())

    def test_html_escapes_declared_source(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["source"] = '<script>alert("x")</script>'
            manifest.write_text(json.dumps(document))
            html = audit(manifest, folder / "audit").read_text()
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn('<script>alert("x")</script>', html)


if __name__ == "__main__":
    unittest.main()
