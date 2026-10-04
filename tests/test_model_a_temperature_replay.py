"""A temperature-run seed must cover the updates as well as the hot start."""
import unittest
import numpy as np

from model_a import ising_engine as engine


class TemperatureReplayTests(unittest.TestCase):
    def test_replay_after_unrelated_run(self):
        cfg=engine.SimulationConfig(L=12,eq_sweeps=20,mc_sweeps=40,sample_interval=2)
        first=engine.simulate_temperature(2.4,cfg,321,return_lattice=True)
        other=engine.simulate_temperature(2.4,cfg,322,return_lattice=True)
        repeated=engine.simulate_temperature(2.4,cfg,321,return_lattice=True)
        for key in first:
            np.testing.assert_array_equal(first[key],repeated[key])
        self.assertFalse(np.array_equal(first['lattice'],other['lattice']))

    def test_quench_seed_remains_self_contained(self):
        args=(12,901,1/5.,1/1.5,1.,.5,10,np.array([1,3,10]),6)
        first=engine._run_quench_replica(*args)
        cfg=engine.SimulationConfig(L=12,eq_sweeps=10,mc_sweeps=20,sample_interval=2)
        engine.simulate_temperature(2.4,cfg,42)
        second=engine._run_quench_replica(*args)
        for a,b in zip(first,second): np.testing.assert_array_equal(a,b)


if __name__=='__main__': unittest.main()
