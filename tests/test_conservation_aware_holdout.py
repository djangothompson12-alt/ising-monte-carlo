import numpy as np
import unittest

from research.analyse_conservation_aware_holdout import measure_snapshot, shared_resolved


class ConservationAwareHoldoutTests(unittest.TestCase):
    def test_block_integration_preserves_fraction_but_segmentation_need_not(self):
        # Every 4x4 block has nine + sites and seven - sites. Its mean preserves
        # the native fraction, while thresholding labels the whole block +1.
        pattern = np.array([1] * 9 + [-1] * 7, dtype=np.int8).reshape(4, 4)
        snapshot = np.tile(pattern, (32, 32))
        measured = measure_snapshot(snapshot)
        self.assertEqual(measured["native_fraction"], 9 / 16)
        self.assertEqual(measured["integrated_fraction"], measured["native_fraction"])
        self.assertEqual(measured["segmented_fraction"], 1.0)


    def test_shared_mask_requires_every_axis_operator_and_replica(self):
        values = {name: np.ones((2, 4, 2), dtype=float)
                  for name in ("native", "integrated", "segmented")}
        values["integrated"][0, 1, 0] = np.nan
        values["segmented"][1, 3, 1] = 0
        np.testing.assert_array_equal(shared_resolved(values), [True, False, True, False])


if __name__ == "__main__":
    unittest.main()
