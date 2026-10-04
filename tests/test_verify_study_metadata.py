"""Archived file names, seeds and configurations must agree with the plan."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from research.imaging_benchmark import sha
from research.verify_study import verify, planned_temperatures


ROOT = Path(__file__).resolve().parents[1]


class MetadataVerificationTests(unittest.TestCase):
    def test_seed_mismatch_is_rejected_even_if_unique(self):
        plan = dict(sizes=[4], concentrations=[0.5], replicas=1,
                    max_sweeps=10, time_samples=2, equilibration=0,
                    Jx=1.0, Jy=1.0, seed=2026)
        seed = int(np.random.SeedSequence([plan["seed"], 0, 0, 0]).generate_state(1)[0])
        config = dict(L=4, concentration=0.5, n_replicas=1, max_sweeps=10,
                      n_time_samples=2, eq_sweeps_initial=0, Jx=1.0,
                      Jy=1.0, seed=seed)
        config.update(planned_temperatures(plan))
        lattice = np.tile(np.array([[1, -1], [-1, 1]], dtype=np.int8), (2, 2))
        sources = {name: sha(ROOT / name)
                   for name in ("model_b/kawasaki_engine.py", "research/campaign.py")}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "manifest.json").write_text(json.dumps({
                "identity": {"plan": plan, "sources": sources}}))
            path = folder / "c0_L4_rep000.npz"

            def save():
                np.savez_compressed(path, config=json.dumps(config),
                                    t=np.array([1, 10]),
                                    snapshots=np.array([lattice, lattice]),
                                    magnetization=int(lattice.sum()),
                                    realized_concentration=0.5,
                                    delta_energy=np.array([0., 0.]))

            save()
            self.assertEqual(verify(folder)["replicas"], 1)
            config["seed"] = seed + 1
            save()
            with self.assertRaisesRegex(ValueError, "config seed"):
                verify(folder)

    def test_temperature_and_grid_corruption_are_rejected(self):
        from research.campaign import config_from_plan, one_replica
        plan=dict(sizes=[4],concentrations=[.5],replicas=1,max_sweeps=10,
                  time_samples=4,equilibration=2,Jx=1.,Jy=.5,seed=93,
                  T_initial_over_tc=3.,T_final_over_tc=.6)
        seed=int(np.random.SeedSequence([93,0,0,0]).generate_state(1)[0])
        data=one_replica(config_from_plan(plan,4,.5,seed))
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            sources={name:sha(ROOT/name) for name in ('model_b/kawasaki_engine.py','research/campaign.py')}
            (folder/'manifest.json').write_text(json.dumps({'identity':{'plan':plan,'sources':sources}}))
            path=folder/'c0_L4_rep000.npz'
            np.savez_compressed(path,**data)
            self.assertTrue(verify(folder)['temperatures_checkpoint_grid_and_nominal_species_count_checked'])
            for key in ('T_initial','T_final'):
                changed=dict(data);config=json.loads(data['config']);config[key]*=1.1
                changed['config']=json.dumps(config);np.savez_compressed(path,**changed)
                with self.assertRaisesRegex(ValueError,key):verify(folder)
            changed=dict(data);changed['t']=data['t'].copy();changed['t'][1]+=1
            np.savez_compressed(path,**changed)
            with self.assertRaisesRegex(ValueError,'Checkpoint grid'):verify(folder)
            # Internally consistent saved magnetisation still must match the plan.
            changed=dict(data);s=data['snapshots'].copy()
            for frame in s:
                index=tuple(np.argwhere(frame==-1)[0]);frame[index]=1
            changed.update(snapshots=s,magnetization=int(s[0].sum()),realized_concentration=float((s[0].mean()+1)/2))
            np.savez_compressed(path,**changed)
            with self.assertRaisesRegex(ValueError,'Species count'):verify(folder)

    def test_temperature_defaults_and_invalid_inputs(self):
        tc=2/np.log(1+np.sqrt(2))
        for plan in (dict(Jx=1,Jy=1),dict(Jx=1,Jy=1,T_final_over_tc=None)):
            values=planned_temperatures(plan)
            self.assertAlmostEqual(values['T_initial'],3*tc)
            self.assertAlmostEqual(values['T_final'],.65*tc)
        for plan in (dict(Jx=0,Jy=1),dict(Jx=1,Jy=1,T_final_over_tc=float('nan'))):
            with self.assertRaises(ValueError):planned_temperatures(plan)


if __name__ == "__main__":
    unittest.main()
