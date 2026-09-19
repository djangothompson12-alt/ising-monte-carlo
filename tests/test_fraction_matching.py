import unittest
import numpy as np
from research.fraction_matching import integrate,match_fraction,TIE_SEEDS


class FractionMatchingTests(unittest.TestCase):
    def test_exact_count_and_order(self):
        a=np.arange(16).reshape(4,4)/15
        b,meta=match_fraction(a,.25,110)
        np.testing.assert_array_equal(b,a>=.8)
        self.assertEqual(meta['fraction_residual'],0)

    def test_quantization_and_ties(self):
        a=np.full((16,16),.5)
        masks=[]
        for seed in TIE_SEEDS:
            b,meta=match_fraction(a,.1500244140625,seed)
            self.assertEqual(b.sum(),38)
            self.assertLessEqual(abs(meta['fraction_residual']),meta['quantization_bound'])
            np.testing.assert_array_equal(b,match_fraction(a,.1500244140625,seed)[0])
            masks.append(b)
        self.assertFalse(np.array_equal(masks[0],masks[1]))

    def test_indicator_mean_preserved_in_2d_and_3d(self):
        for shape in ((16,16),(16,16,16)):
            a=np.random.default_rng(2).integers(0,2,shape)
            for factor in (1,2,4,8): self.assertEqual(integrate(a,factor).mean(),a.mean())

    def test_empty_and_full(self):
        for fraction in (0,1):
            b,meta=match_fraction(np.full((4,4,4),fraction),fraction,110)
            self.assertEqual(b.mean(),fraction)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError): match_fraction(np.zeros((4,4)),1.1,110)
        with self.assertRaises(ValueError): integrate(np.zeros((4,4)),3)
        with self.assertRaises(ValueError): integrate(np.full((4,4),np.nan),2)

    def test_factor_one_recovers_native_mask(self):
        a=np.random.default_rng(3).integers(0,2,(16,16))
        for seed in TIE_SEEDS: np.testing.assert_array_equal(match_fraction(a,a.mean(),seed)[0],a)
