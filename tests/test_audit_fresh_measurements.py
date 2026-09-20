import itertools
import unittest
import numpy as np
from research.audit_fresh_measurements import (bootstrap_counts, weighted_quantile,
    direct_measures, exact_interval, ols, label)


class FreshAuditTests(unittest.TestCase):
    def test_multinomial_matches_ordered_enumeration(self):
        for n in (2,3,4):
            counts, weights=bootstrap_counts(n)
            exact={tuple(row):weight for row,weight in zip(counts,weights)}
            ordered={key:0 for key in exact}
            for draw in itertools.product(range(n),repeat=n):
                ordered[tuple(np.bincount(draw,minlength=n))]+=1/n**n
            for key in exact: self.assertAlmostEqual(exact[key],ordered[key])

    def test_eight_replica_distribution_normalizes(self):
        counts,weights=bootstrap_counts(8)
        self.assertEqual(len(counts),6435)
        self.assertAlmostEqual(weights.sum(),1)
        np.testing.assert_allclose(weights@counts,np.ones(8),atol=1e-12)

    def test_known_power_and_constant_scale(self):
        t=np.geomspace(10,1000,12)
        native=np.arange(1,9)[:,None]*t[None,:]**(1/3)
        for power in (0.,-.07):
            observed=native*1.1*t[None,:]**power
            result=exact_interval(t,native,observed)
            self.assertAlmostEqual(result['low'],power,places=12)
            self.assertAlmostEqual(result['high'],power,places=12)
        self.assertAlmostEqual(ols(t,t**.27),.27)

    def test_discrete_quantiles(self):
        self.assertEqual(weighted_quantile([0,.5,1],[.25,.5,.25],[0,.25,.5,.75,1]),[0,0,.5,.5,1])
        with self.assertRaises(ValueError): weighted_quantile([1],[0])
        with self.assertRaises(ValueError): bootstrap_counts(9)

    def test_direct_lengths_and_physical_scale(self):
        y,x=np.indices((32,32));field=((x//4+y//4)%2).astype(float)
        result=direct_measures(field)
        # At lag 1 there are seven mismatches per 31 valid horizontal pairs.
        # C(1)=17/31; at lag 2, C(2)=1/15. Linear half-height at 1.1.
        expected=1+((17/31)-.5)/((17/31)-(1/15))
        self.assertAlmostEqual(result['half'],expected)
        self.assertAlmostEqual(direct_measures(field,.2)['half'],expected*.2)
        self.assertTrue(np.isnan(direct_measures(np.ones((8,8)))['lobe']))

    def test_unresolved_and_tolerance(self):
        self.assertTrue(np.isnan(ols([1,2,3],[1,2,3])))
        self.assertTrue(np.isnan(ols([1,2,4,8],[1,2,np.nan,4])))
        self.assertEqual(label(-.08,-.06),'outside')
        self.assertEqual(label(-.01,.01),'within')
        self.assertEqual(label(-.03,.01),'uncertain')
        self.assertEqual(label(np.nan,np.nan),'unresolved')


if __name__=='__main__': unittest.main()
