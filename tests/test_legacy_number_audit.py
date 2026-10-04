import unittest
import numpy as np
from research.audit_legacy_numbers import fit


class LegacyFitTests(unittest.TestCase):
    def test_known_power_and_historical_cutoffs(self):
        t=np.array([1.,2.,3.,5.,10.,30.,100.])
        values=2*t**.4
        result=fit(t,values,40)
        self.assertAlmostEqual(result['alpha'],.4)
        self.assertEqual(result['first_sweep'],3)
        self.assertEqual(result['last_sweep'],10)
        self.assertEqual(result['retained_points'],3)

    def test_invalid_fit_is_explicit(self):
        for t,a in (([1,2],[1,2]),([3,3,3],[1,2,3]),([3,4,5],[1,np.nan,2])):
            with self.assertRaises(ValueError):fit(t,a,128)


if __name__=='__main__':unittest.main()
