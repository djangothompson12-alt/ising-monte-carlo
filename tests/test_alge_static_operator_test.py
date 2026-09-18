import unittest

import numpy as np

from research.alge_static_operator_test import centre_roi, measure


class AlGeOperatorTests(unittest.TestCase):
    def test_roi_fails_if_air_exceeds_limit(self):
        labels = np.full((400, 400), 2, dtype=np.uint8)
        labels[180:220, 180:220] = 0
        roi, bounds, status = centre_roi(labels)
        self.assertEqual(roi.shape, (300, 300))
        self.assertIn("exceeds", status)

    def test_operator_reports_unknown_encoding(self):
        axis = np.arange(300)
        square = np.where(((axis[:, None] // 20) + (axis[None, :] // 20)) % 2,
                          2, 3).astype(np.uint8)
        square[10, 10] = 1
        result = measure(square)
        self.assertTrue(np.isfinite(result["native_length_um"]))
        self.assertTrue(np.isfinite(result["altered_length_um"]))
        self.assertTrue(np.isfinite(result["unknown_as_ge_ratio"]))


if __name__ == "__main__":
    unittest.main()
