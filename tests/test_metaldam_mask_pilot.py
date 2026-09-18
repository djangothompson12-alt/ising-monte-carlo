from io import BytesIO
import unittest
from zipfile import ZipFile

import numpy as np
from PIL import Image

from research.metaldam_mask_pilot import _read_pair, dice_curve, otsu_threshold


class MetalDamPilotTests(unittest.TestCase):
    def test_dice_curve_matches_explicit_masks(self):
        gray = np.array([[0, 1, 2], [2, 1, 0]], dtype=np.uint8)
        truth = np.array([[False, False, True], [True, False, False]])
        bright, dark = dice_curve(gray, truth)
        for threshold in range(4):
            for curve, mask in ((bright, gray >= threshold), (dark, gray < threshold)):
                expected = 2 * np.count_nonzero(mask & truth) / (mask.sum() + truth.sum())
                self.assertAlmostEqual(curve[threshold], expected)

    def test_otsu_separates_two_intensity_groups(self):
        gray = np.array([[10] * 8, [10] * 8, [200] * 8, [200] * 8], dtype=np.uint8)
        threshold = otsu_threshold(gray)
        self.assertTrue(10 < threshold <= 200)
        self.assertEqual(int((gray >= threshold).sum()), 16)

    def test_explicit_rgb_label_exception_and_66_row_band(self):
        image = np.full((70, 4, 3), 25, dtype=np.uint8)
        label = np.ones((4, 4, 3), dtype=np.uint8)
        def encoded(array, fmt):
            stream = BytesIO()
            Image.fromarray(array).save(stream, format=fmt)
            return stream.getvalue()
        stream = BytesIO()
        with ZipFile(stream, "w") as archive:
            archive.writestr("MetalDAM/images/micrograph26.jpg", encoded(image, "JPEG"))
            archive.writestr("MetalDAM/labels/micrograph26.png", encoded(label, "PNG"))
        stream.seek(0)
        with ZipFile(stream) as archive:
            gray, labels, band_rows = _read_pair(archive, 26)
        self.assertEqual(band_rows, 66)
        self.assertEqual(gray.shape, (4, 4))
        self.assertTrue(np.all(labels == 1))


if __name__ == "__main__":
    unittest.main()
