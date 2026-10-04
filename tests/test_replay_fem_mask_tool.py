"""Checks for the independent FeM public-data replay."""

import unittest

import numpy as np

from research.mask_resolution_audit import measure
from research.replay_fem_mask_tool import (
    EXPECTED_SHAPE,
    PIXEL_SIZE_UM,
    ROI,
    _direct_length,
)


class FeMReplayTests(unittest.TestCase):
    def test_direct_real_space_check_matches_main_estimator(self):
        y, x = np.indices(EXPECTED_SHAPE)
        synthetic_ore = (
            ((x - 250) ** 2 + (y - 230) ** 2 < 95 ** 2)
            | ((x - 690) ** 2 + (y - 480) ** 2 < 135 ** 2)
        )
        mask = np.where(synthetic_ore, 0, 255).astype(np.uint8)
        y0, y1, x0, x1 = ROI
        field = mask[y0:y1, x0:x1] == 0
        for factor in (1, 2, 4):
            fraction, length_x, length_y = _direct_length(mask, factor)
            result = measure(
                field, factor, PIXEL_SIZE_UM, ties_to_foreground=False
            )
            self.assertAlmostEqual(fraction, result["phase_fraction"], places=12)
            self.assertAlmostEqual(length_x, result["length_x"], places=10)
            self.assertAlmostEqual(length_y, result["length_y"], places=10)


if __name__ == "__main__":
    unittest.main()
