import unittest
import numpy as np
from research.imaging import finite_correlations,image_length,block_average,observe,corner_crops


class ImagingTests(unittest.TestCase):
    def test_linear_fft_matches_explicit_nonperiodic_pairs(self):
        x=np.random.default_rng(1).normal(size=(12,16));z=x-x.mean();v=np.mean(z*z)
        expected=[]
        for axis in (1,0):
            out=[1.]
            for r in range(1,7):
                a,b=(z[:,:-r],z[:,r:]) if axis==1 else (z[:-r,:],z[r:,:])
                out.append(np.mean(a*b)/v)
            expected.append(out)
        np.testing.assert_allclose(finite_correlations(x),expected,atol=1e-13)

    def test_boundary_is_not_periodic(self):
        x=np.zeros((8,8));x[:,0]=1;x[:,-1]=-1
        actual=finite_correlations(x)[0,1]
        circular=np.mean(x*np.roll(x,1,axis=1))/np.var(x)
        self.assertAlmostEqual(actual,0.)
        self.assertNotAlmostEqual(actual,circular)

    def test_sign_transpose_offset_and_spacing(self):
        x=np.random.default_rng(4).choice([-1,1],size=(32,32))
        for y in (-x,x+3,x.T):
            self.assertAlmostEqual(image_length(x)['length'],image_length(y)['length'])
        self.assertAlmostEqual(image_length(x,2)['length'],2*image_length(x)['length'])

    def test_constant_and_one_direction_unresolved(self):
        self.assertFalse(image_length(np.ones((8,8)))['resolved'])
        x=np.tile(np.repeat([1,-1],8),(16,1))
        m=image_length(x)
        self.assertTrue(np.isfinite(m['length_x']))
        self.assertTrue(np.isnan(m['length_y']))
        self.assertTrue(np.isnan(m['length']))

    def test_block_average_preserves_mean_and_identity(self):
        x=np.arange(64).reshape(8,8)
        np.testing.assert_equal(block_average(x,1),x)
        self.assertAlmostEqual(block_average(x,2).mean(),x.mean())
        np.testing.assert_equal(block_average(x,2)[0],[4.5,6.5,8.5,10.5])

    def test_observation_does_not_mutate_source(self):
        x=np.random.default_rng(8).choice([-1,1],size=(16,16));copy=x.copy()
        np.testing.assert_equal(observe(x),x)
        observe(x,sigma=2,factor=2)
        np.testing.assert_equal(x,copy)

    def test_crop_origins_and_no_wrap(self):
        x=np.arange(64).reshape(8,8);crops=corner_crops(x,4)
        self.assertEqual([p for p,_ in crops],[(0,0),(0,4),(4,0),(4,4)])
        np.testing.assert_equal(crops[-1][1],x[4:,4:])
        self.assertEqual(len(corner_crops(x,8)),1)

    def test_invalid_inputs(self):
        for bad in (np.ones((3,3)),np.ones((8,8,2)),np.full((8,8),np.nan)):
            with self.assertRaises(ValueError):image_length(bad)
        for factor in (0,3,1.5):
            with self.assertRaises(ValueError):block_average(np.ones((8,8)),factor)
        with self.assertRaises(ValueError):image_length(np.ones((8,8)),0)
        with self.assertRaises(ValueError):observe(np.ones((8,8)),sigma=-1)


if __name__=='__main__':unittest.main()
