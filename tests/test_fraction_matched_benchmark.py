"""Known powers and whole-trajectory/shared-window regression checks."""
import unittest
import numpy as np
from research.fraction_matched_benchmark import fit_simulations, FACTORS
from research.fraction_matching import TIE_SEEDS


class FitTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for c in (.5,.15):
            for factor in FACTORS:
                for replica in range(16):
                    for t in (1000,2000,4000,8000,16000,32000,64000,128000):
                        for stage,power in [('native',.3),('integrated',.2),('fixed',.25),('matched',.27)]:
                            for seed in TIE_SEEDS if stage=='matched' else (-1,):
                                # Different replica/tie amplitudes, identical known exponent.
                                amplitude=(1+replica/20)*(1+max(seed,0)/10000)
                                rows.append(dict(composition=c,factor=factor,id=replica,
                                    sweep=t,stage=stage,tie_seed=seed,length=amplitude*t**power))
        return rows

    def test_known_powers_and_paired_resampling(self):
        fits=fit_simulations(self.rows())
        self.assertEqual(len(fits),36)
        for r in fits:
            expected={'integrated':-.1,'fixed':-.05,'matched':-.03}[r['stage']]
            self.assertAlmostEqual(r['native_alpha'],.3,12)
            for key in ('delta_alpha','low','high'):
                self.assertAlmostEqual(r[key],expected,12)
            self.assertEqual(r['independent_trajectories'],16)
            if r['stage']=='matched':
                self.assertAlmostEqual(r['tie_delta_min'],expected,12)
                self.assertAlmostEqual(r['tie_delta_max'],expected,12)

    def test_one_missing_tie_excludes_time_from_all_paired_stages(self):
        rows=self.rows()
        for r in rows:
            if (r['composition'],r['factor'],r['id'],r['sweep'],r['stage'],r['tie_seed'])==(.5,4,0,2000,'matched',TIE_SEEDS[0]):
                r['length']=np.nan
        fits=fit_simulations(rows)
        for r in fits:
            expected=5 if r['nominal_t_max']==20000 else 8
            if r['composition']==.5 and r['factor']==4: expected-=1
            self.assertEqual(r['retained_points'],expected)
            self.assertAlmostEqual(r['native_alpha'],.3,12)


if __name__=='__main__': unittest.main()
