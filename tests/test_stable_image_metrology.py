import unittest
from unittest.mock import patch

import numpy as np

from research.audit_fresh_measurements import direct_measures
from research.imaging import finite_correlations
from research.stable_image_metrology import refined_correlations, refined_measures


class StableImageTests(unittest.TestCase):
    def test_exact_zero_followed_by_positive_lobe(self):
        # Actual frozen c0/rep000, t=20000, factor8, origin0, tie211 mask.
        rows = ('0010111101001011', '1000000001110111', '0111111110011100',
                '0110000011100010', '1010000010010011', '0000101110011011',
                '0110100001111011', '0111101001000000', '1111101101011111',
                '0001110111000001', '1000011010101111', '1111001001100011',
                '1011011011000000', '1000110011101110', '1110110011010000',
                '1110000000001000')
        field = np.array([[int(x) for x in row] for row in rows])
        fft = finite_correlations(field)
        # Inject representative roundoff explicitly: FFT libraries may differ.
        fft[0,4] = 2.7755575615628914e-17
        with patch('research.stable_image_metrology.finite_correlations', return_value=fft.copy()):
            self.assertEqual(refined_correlations(field)[0,4], 0.)
        result = refined_measures(field, 8)
        self.assertAlmostEqual(result['lobe'], 5.06843562941124)
        for key, expected in direct_measures(field,8).items():
            self.assertAlmostEqual(result[key], expected)

    def test_matches_direct_for_random_binary_and_gray(self):
        rng = np.random.default_rng(33)
        for shape in ((16,16),(20,24)):
            for field in (rng.integers(0,2,size=shape),rng.random(shape)):
                actual, expected = refined_measures(field),direct_measures(field)
                for key in actual:
                    np.testing.assert_allclose(actual[key],expected[key],atol=1e-12,equal_nan=True)

    def test_tolerance_selects_recomputation_not_snapping(self):
        rng = np.random.default_rng(98)
        field = rng.random((12,12))
        original = finite_correlations(field)
        # A large tolerance forces every value to be independently recomputed.
        np.testing.assert_allclose(refined_correlations(field,2),original,atol=1e-14)
        self.assertTrue(np.isnan(refined_measures(np.ones((8,8)))['half']))
        with self.assertRaises(ValueError): refined_correlations(field,-1)


if __name__ == '__main__': unittest.main()
