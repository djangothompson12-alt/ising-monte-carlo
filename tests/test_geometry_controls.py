import unittest
import tempfile
import json
from pathlib import Path
import numpy as np
from research.geometry_controls import checkerboard, balanced_defects, direct_correlations, sequential_binary, run, sha
from research.fraction_matching import integrate, match_fraction
from research.growth_reliability import measures, log_slope
from research.imaging import finite_correlations


class GeometryControlsTests(unittest.TestCase):
    def test_analytic_periodic_and_finite_pairs(self):
        a = checkerboard(32, 4)
        expected = np.broadcast_to(1-2*np.arange(5)/4, (2,5))
        np.testing.assert_allclose(direct_correlations(a,True)[:,:5],expected,atol=1e-14)
        np.testing.assert_allclose(direct_correlations(a),finite_correlations(a),atol=1e-14)
        self.assertEqual(a.mean(),.5)

    def test_exact_known_growth_and_factor_one(self):
        widths=np.array([4,8,16,32,64])
        self.assertAlmostEqual(log_slope(widths**3,widths/4),1/3)
        a=checkerboard(32,4)
        np.testing.assert_array_equal(integrate(a,1),a)
        np.testing.assert_array_equal(match_fraction(a,.5,11)[0],a)

    def test_defects_conserve_and_do_not_mutate(self):
        a=checkerboard(32,4); old=a.copy()
        b=balanced_defects(a,.1,12)
        self.assertEqual(a.sum(),b.sum())
        self.assertGreater(np.count_nonzero(a!=b),0)
        np.testing.assert_array_equal(a,old)
        np.testing.assert_array_equal(b,balanced_defects(a,.1,12))

    def test_flat_aliasing_does_not_become_resolved(self):
        a=checkerboard(64,4); gray=integrate(a,8)
        self.assertTrue(np.all(gray==.5))
        self.assertTrue(np.isnan(measures(gray)['half']))
        self.assertTrue(np.isnan(measures(gray)['lobe']))
        matched,_=match_fraction(gray,.5,110)
        self.assertEqual(matched.mean(),.5)

    def test_unresolved_not_silently_trimmed(self):
        self.assertTrue(np.isnan(log_slope([1,8,64,512],[1,2,np.nan,8])))

    def test_sequential_is_not_single_step(self):
        # Two 2x2 blocks tie; rounding both up gives a half-filled next level.
        a=np.zeros((8,8),dtype=np.uint8)
        a[:2,0]=1; a[:2,2]=1
        self.assertNotEqual(sequential_binary(a,4)[0,0], (integrate(a,4)>=.5)[0,0])
        np.testing.assert_array_equal(sequential_binary(a,2),integrate(a,2)>=.5)

    def test_validation(self):
        for size,width in ((32,3),(32,0),(31,4)):
            with self.assertRaises(ValueError): checkerboard(size,width)
        with self.assertRaises(ValueError): balanced_defects(np.full((8,8),.5))
        with self.assertRaises(ValueError): sequential_binary(np.zeros((8,8)),3)

    def test_complete_output_and_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'result'
            result=run(folder)
            self.assertEqual(result['observations'],480)
            self.assertEqual(result['fits'],192)
            d=json.loads((folder/'results.json').read_text())
            self.assertEqual(len(d['direct_checks']),5)
            self.assertEqual(sum(not r['resolved_all_widths'] for r in d['fits']),20)
            for name,digest in json.loads((folder/'manifest.json').read_text())['output_sha256'].items():
                self.assertEqual(sha(folder/name),digest)
            with self.assertRaises(FileExistsError): run(folder)


if __name__=='__main__': unittest.main()
