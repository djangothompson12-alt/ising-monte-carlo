"""Contract checks for the user-facing, expert-mask resolution audit."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

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
            self.assertEqual(float(rows[0]["length_change_percent"]), 0)
            self.assertEqual(float(rows[0]["phase_fraction_change"]), 0)
            self.assertGreater(float(rows[0]["direction_ratio_x_over_y"]), 0)
            self.assertIn(rows[0]["three_pixel_warning"], ("flag", "no flag"))
            self.assertGreater(float(rows[0]["minimum_pixels_per_length"]), 0)
            self.assertEqual(rows[0]["decision_status"], "native reference")
            self.assertEqual(rows[1]["decision_status"],
                             "not classified: no owner tolerance")
            self.assertTrue(all(row["specimen_id"] == "one synthetic specimen" for row in rows))
            self.assertEqual(rows[0]["length_unit"], "um")
            html = report.read_text()
            self.assertIn("Repeated slices from one", html)
            self.assertIn("non-square pixels need a", html)
            self.assertIn("not generally the alloy's conserved chemical composition", html)
            self.assertIn("Do not use this report as a chemical mass-balance test", html)
            self.assertIn("<th>Mask authority</th>", html)
            self.assertIn("<td>synthetic known mask</td>", html)
            self.assertIn("<th>ROI</th>", html)
            self.assertIn("<td>[8, 56, 8, 56]</td>", html)
            self.assertIn("<th>Pixel spacing</th>", html)
            self.assertIn("<th>X length</th>", html)
            self.assertIn("<th>Y length</th>", html)
            self.assertIn("<th>Fraction change</th>", html)
            self.assertIn("<th>X/Y geometry ratio</th>", html)
            self.assertIn("<th>Min pixels/length</th>", html)
            self.assertIn("not a universal accuracy threshold", html)
            self.assertIn("Materials context not declared", html)
            self.assertIn("not a mechanical-property anisotropy", html)
            self.assertIn("No owner-defined tolerance was declared", html)
            self.assertIn("<td>0.06</td>", html)
            self.assertIn("<th>Unit</th>", html)
            self.assertIn("<td>um</td>", html)
            self.assertIn("<td>15 min</td>", html)
            self.assertNotIn("data:image", html)
            self.assertNotIn("expert_mask.npy", html)
            provenance = json.loads((folder / "audit" / "manifest.json").read_text())
            self.assertEqual(len(provenance["mask_sha256"]["first"]), 64)
            self.assertEqual(len(provenance["output_sha256"]["measurements.csv"]), 64)
            self.assertEqual(len(provenance["output_sha256"]["report.html"]), 64)
            self.assertIn("created_utc", provenance)
            self.assertIsNone(provenance["materials_context"])
            self.assertIsNone(provenance["decision_tolerance_fraction"])
            self.assertEqual(provenance["input_settings"][0]["roi"], [8, 56, 8, 56])
            self.assertEqual(provenance["input_settings"][0]["pixel_size"], .06)
            self.assertIn("not a chemical-composition mass balance",
                          provenance["interpretation"])
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

    def test_multiframe_tiff_requires_an_explicit_single_plane(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            frame = Image.fromarray(np.zeros((64, 64), dtype=np.uint8))
            stack_path = folder / "stack.tif"
            frame.save(stack_path, save_all=True, append_images=[frame.copy()])
            document["records"][0]["mask_path"] = stack_path.name
            document["records"][0]["foreground_value"] = 1
            document["records"][0]["background_value"] = 0
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, "multi-frame images are not accepted"):
                audit(manifest, folder / "bad_stack")
            self.assertFalse((folder / "bad_stack").exists())

    def test_html_escapes_declared_source(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["source"] = '<script>alert("x")</script>'
            manifest.write_text(json.dumps(document))
            html = audit(manifest, folder / "audit").read_text()
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn('<script>alert("x")</script>', html)

    def test_optional_declared_hash_locks_the_input(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["records"][0]["sha256"] = "0" * 64
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, "mask changed"):
                audit(manifest, folder / "changed")
            self.assertFalse((folder / "changed").exists())

    def test_materials_context_is_complete_and_escaped(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            context = dict(
                material_system="Al-Ge <binary alloy>",
                processing_condition="aged 315 min at a declared temperature",
                imaging_method="segmented X-ray nanotomography plane",
                section_geometry="one transverse 2D plane from a 3D ROI",
                calibration_source="reconstruction metadata",
                measurement_purpose="screen resolution sensitivity of Ge-phase spacing",
            )
            document["materials_context"] = context
            manifest.write_text(json.dumps(document))
            report = audit(manifest, folder / "materials")
            html = report.read_text()
            self.assertIn("Declared materials context", html)
            self.assertIn("Al-Ge &lt;binary alloy&gt;", html)
            provenance = json.loads(
                (folder / "materials" / "manifest.json").read_text()
            )
            self.assertEqual(provenance["materials_context"], context)

            document["materials_context"].pop("calibration_source")
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError,
                                        "materials_context.calibration_source"):
                audit(manifest, folder / "incomplete")

    def test_owner_tolerance_must_be_predeclared_and_explained(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["decision_tolerance_fraction"] = 0.10
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, "decision_tolerance_reason"):
                audit(manifest, folder / "missing_reason")

            document["decision_tolerance_reason"] = (
                "A ten-percent change would alter the owner's comparison"
            )
            manifest.write_text(json.dumps(document))
            report = audit(manifest, folder / "classified")
            with (folder / "classified" / "measurements.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]["decision_status"], "native reference")
            self.assertTrue(all(row["decision_status"] in {
                "native reference", "within owner tolerance",
                "outside owner tolerance", "unresolved",
            } for row in rows))
            self.assertIn("10% relative-length tolerance", report.read_text())


if __name__ == "__main__":
    unittest.main()
