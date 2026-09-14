"""Analytic and invariance checks for exploratory Model B observables."""
import unittest
import numpy as np
from research.metrology import (first_crossing, positive_lobe_integral,
    spectrum, inverse_first_moment, snapshot_measures)
from research.compare_estimators import paired_slopes
from research.reference_measurements import (majority_filter_once, periodic_chord_lengths,
    raw_axis_correlations, reference_measurements)
from model_b.kawasaki_engine import _axis_correlation_xy, domain_size_from_correlation
from research.dynamic_scaling import overlap_rms, radial_structure
from research.analyse_reference_benchmark import _slopes


class MetrologyTests(unittest.TestCase):
    def test_piecewise_linear_correlation(self):
        c=np.array([1., .5, 0., -.5])
        self.assertEqual(first_crossing(c,.5),1.)
        self.assertEqual(positive_lobe_integral(c),1.)
        self.assertAlmostEqual(positive_lobe_integral([1.,-.5]),1/3)

    def test_unresolved_is_not_a_fabricated_length(self):
        self.assertTrue(np.isnan(first_crossing([1.,.9,.8],.5)))
        self.assertTrue(np.isnan(positive_lobe_integral([1.,.9,.8])))
        self.assertTrue(np.isnan(inverse_first_moment(np.ones((8,8)))))

    def test_parseval_normalisation(self):
        x=np.random.default_rng(9).normal(size=(32,48))
        _,s=spectrum(x)
        self.assertAlmostEqual(s.sum()/x.size,np.var(x),places=13)

    def test_spectral_known_wavelength_and_invariances(self):
        x=np.broadcast_to(np.cos(2*np.pi*np.arange(64)/8),(64,64))
        for field in (x,-x,np.roll(x,3,axis=1),x+5,x.T):
            self.assertAlmostEqual(inverse_first_moment(field),8.,places=11)

    def test_matches_archived_engine_threshold(self):
        x=np.random.default_rng(10).choice([-1,1],size=(32,32))
        corr=_axis_correlation_xy(x,16)
        expected=np.mean([domain_size_from_correlation(c) for c in corr])
        self.assertAlmostEqual(snapshot_measures(x,corr)['threshold_05'],expected)

    def test_interface_count_for_stripes(self):
        x=np.tile(np.repeat([1,-1,1,-1],4),(16,1))
        corr=_axis_correlation_xy(x,8)
        # Four interfaces per row: rho=64/(2*256)=1/8.
        self.assertEqual(snapshot_measures(x,corr)['inverse_interface_proxy'],8.)

    def test_paired_bootstrap_known_exponent_difference(self):
        t=np.geomspace(100,20000,32)
        amplitudes=np.array([.9,1.,1.1,1.2])[:,None]
        reference=amplitudes*t**.2
        values=amplitudes*t**.3
        result=paired_slopes(t,values,reference,np.ones(32,dtype=bool),draws=100)
        np.testing.assert_allclose(result[:3],.3,atol=1e-12)
        np.testing.assert_allclose(result[3:],.1,atol=1e-12)
        same=paired_slopes(t,reference,reference,np.ones(32,dtype=bool),draws=100)
        np.testing.assert_allclose(same[3:],0.,atol=1e-12)

    def test_reference_majority_filter_is_non_mutating_and_removes_isolated_spin(self):
        x=np.ones((8,8),dtype=np.int8);x[3,3]=-1;original=x.copy()
        filtered=majority_filter_once(x)
        np.testing.assert_array_equal(x,original)
        self.assertEqual(filtered[3,3],1)

    def test_reference_periodic_chords_for_stripes(self):
        x=np.tile(np.tile(np.repeat([1,-1],4),2),(16,1)).astype(np.int8)
        np.testing.assert_array_equal(periodic_chord_lengths(x,axis=1),np.full(64,4.))
        self.assertEqual(len(periodic_chord_lengths(x,axis=0)),0)
        cx,cy=raw_axis_correlations(x,8)
        self.assertEqual(cx[0],1.)
        self.assertEqual(cy[0],1.)
        measures=reference_measurements(x)
        self.assertAlmostEqual(measures['mean_chord_length'],4.)

    def test_scaling_overlap_and_radial_peak_on_known_fields(self):
        x=np.geomspace(.1,3.,40);y=np.exp(-x)
        self.assertAlmostEqual(overlap_rms([(x,y),(x,y)])['rms'],0.,places=14)
        self.assertEqual(overlap_rms([(x,y),(x,y)],x_max=2)['x_max'],2.)
        self.assertGreater(overlap_rms([(x,y),(x,y+.1)])['rms'],0.)
        field=np.broadcast_to(np.cos(2*np.pi*np.arange(64)/8),(64,64))
        q,power=radial_structure(field)
        self.assertAlmostEqual(q[np.argmax(power)],1/8,delta=.011)

    def test_fixed_initial_length_recovers_synthetic_growth_law(self):
        t=np.array([20,1000,5000,20000,100000,200000,1000000,4500000])
        amplitudes=np.array([.8,.9,1.,1.1,1.2])[:,None]
        values=3.6+amplitudes*(t-20)**(1/3)
        adjusted=_slopes(t,values,1000,4500000,0)
        raw=_slopes(t,values,1000,4500000,None)
        self.assertAlmostEqual(adjusted[0],1/3,places=12)
        self.assertLess(raw[0],1/3)


if __name__=='__main__':
    unittest.main()
