import unittest
import numpy as np
from research.growth_reliability import decimation_limit,paired_fit,correlation_measures,tolerance_label


class ReliabilityTests(unittest.TestCase):
    def test_constant_error_and_time_varying_power(self):
        t=np.geomspace(1000,20000,17)
        native=np.arange(1,9)[:,None]*t[None,:]**.3
        constant=paired_fit(t,native,1.1*native,draws=50)
        self.assertAlmostEqual(constant['delta'],0.,13)
        changing=paired_fit(t,native,native*1.1*(t/1000)**(-.07),draws=50)
        for key in ('delta','ratio_slope','low','high'): self.assertAlmostEqual(changing[key],-.07,12)

    def test_ratio_of_means_not_mean_of_ratios(self):
        t=np.geomspace(1000,20000,17)
        a=np.array([t**.2,5*t**.4]);b=np.array([2*t**.3,t**.2])
        result=paired_fit(t,a,b,draws=50)
        self.assertLess(result['identity_error'],1e-12)
        self.assertAlmostEqual(result['ratio_first'],b[:,0].mean()/a[:,0].mean())
        self.assertNotAlmostEqual(result['ratio_first'],(b[:,0]/a[:,0]).mean())

    def test_equation_rounding(self):
        self.assertEqual(decimation_limit((128,128),12),4)
        self.assertEqual(decimation_limit((128,128),11.9),2)
        self.assertEqual(decimation_limit((128,128),2),1)
        self.assertTrue(np.isnan(decimation_limit((128,128),np.nan)))

    def test_correlations_known_triangle(self):
        c=np.array([1.,.75,.5,.25,0.,-.25])
        m=correlation_measures([c,c],2.)
        self.assertAlmostEqual(m['half'],4.)
        self.assertAlmostEqual(m['lobe'],4.)
        self.assertAlmostEqual(m['near_zero_min'],7.84)

    def test_unresolved_and_interval_labels(self):
        m=correlation_measures([np.ones(5),np.ones(5)])
        self.assertTrue(np.isnan(m['lobe']))
        self.assertEqual(tolerance_label(-.01,.01),'within')
        self.assertEqual(tolerance_label(-.04,-.03),'outside')
        self.assertEqual(tolerance_label(-.04,-.01),'uncertain')
        self.assertEqual(tolerance_label(np.nan,np.nan),'unresolved')


if __name__=='__main__':unittest.main()
