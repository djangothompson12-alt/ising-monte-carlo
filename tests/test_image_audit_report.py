import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from research.image_audit_report import analyse


class ImageAuditReportTests(unittest.TestCase):
    def fixture(self, folder: Path) -> tuple[Path, dict]:
        y, x = np.indices((64, 64))
        image = ((y // 8 + x // 8) % 2).astype(float) * 100.0
        np.save(folder / "image.npy", image)
        document = dict(
            source="synthetic audit fixture", license="synthetic only",
            phase_definition="bright checkerboard squares",
            records=[dict(
                id="sample", path="image.npy", roi=[8, 56, 8, 56],
                roi_reason="interior test field", thresholds=[20, 50, 80],
                threshold_reason="declared sensitivity range", foreground="above",
                preview_threshold=50, pixel_size=0.06, length_unit="um",
            )],
        )
        manifest = folder / "input.json"
        manifest.write_text(json.dumps(document))
        return manifest, document

    def test_all_thresholds_and_pixel_spacing_are_retained(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, _ = self.fixture(folder)
            original = np.load(folder / "image.npy").copy()
            output = folder / "audit"
            analyse(manifest, output, include_previews=True)
            rows = (output / "measurements.csv").read_text().strip().splitlines()
            self.assertEqual(len(rows), 10)  # Header + 3 thresholds x 3 factors.
            self.assertIn("0.24", rows[-1])  # Four original 0.06 um pixels.
            report = (output / "report.html").read_text()
            self.assertIn("all thresholds are reported below", report)
            self.assertIn("data:image/png;base64,", report)
            self.assertNotIn("growth-law exponent =", report)
            self.assertTrue(np.array_equal(np.load(folder / "image.npy"), original))
            provenance = json.loads((output / "manifest.json").read_text())
            self.assertEqual(len(provenance["image_sha256"]["sample"]), 64)
            self.assertTrue(provenance["previews_embedded"])
            with self.assertRaises(FileExistsError):
                analyse(manifest, output)

    def test_nondivisible_reduction_is_reported_not_silently_cropped(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["records"][0]["roi"] = [7, 56, 8, 56]  # 49 x 48.
            manifest.write_text(json.dumps(document))
            output = folder / "audit"
            analyse(manifest, output)
            report = (output / "report.html").read_text()
            self.assertIn("not measured", report)
            self.assertNotIn("data:image/png;base64,", report)
            self.assertEqual(len((output / "measurements.csv").read_text().splitlines()), 10)

    def test_declared_roi_and_previews_are_required(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["records"][0]["roi"] = [0, 100, 0, 64]
            manifest.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                analyse(manifest, folder / "bad_roi")
            self.assertFalse((folder / "bad_roi").exists())

            document["records"][0]["roi"] = [8, 56, 8, 56]
            document["records"][0].pop("preview_threshold")
            manifest.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                analyse(manifest, folder / "bad_preview", include_previews=True)
            self.assertFalse((folder / "bad_preview").exists())

    def test_user_text_is_escaped_in_html(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            manifest, document = self.fixture(folder)
            document["source"] = '<script>alert("test")</script>'
            manifest.write_text(json.dumps(document))
            analyse(manifest, folder / "audit")
            report = (folder / "audit" / "report.html").read_text()
            self.assertNotIn('<script>alert("test")</script>', report)
            self.assertIn("&lt;script&gt;", report)


if __name__ == "__main__":
    unittest.main()
