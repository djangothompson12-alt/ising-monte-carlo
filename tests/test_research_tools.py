"""Synthetic checks, not experimental validation."""
import io
import csv
import json
import unittest
import zipfile
import tempfile
from pathlib import Path
import numpy as np
from experiments.string_lab import (predict_frequency, infer_tension,
    tension_uncertainty, spectrum_peak, compare_records, plot_comparison)
from model_b.research_export import export_zip
from model_b.kawasaki_engine import KawasakiConfig
from research.campaign import one_replica, config_from_plan
from research.analyse_campaign import fit_slope, bootstrap_slope
from research.reference_benchmark import load_declaration, measure_campaign
from research.analyse_main_extension import analyse as analyse_main_extension


class StringTests(unittest.TestCase):
    def test_analytic_value_and_inverse(self):
        self.assertAlmostEqual(predict_frequency(4, .5, .002), np.sqrt(2000))
        for F in (1, 5, 10):
            self.assertAlmostEqual(infer_tension(predict_frequency(F,.4,.001),.4,.001), F)

    def test_input_guards(self):
        for bad in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                predict_frequency(bad, .5, .002)
        with self.assertRaises(ValueError):
            spectrum_peak(np.zeros(8000), 8000, 10, 500)
        with self.assertRaises(ValueError):
            compare_records([])

    def test_uncertainty_against_monte_carlo(self):
        rng = np.random.default_rng(34)
        f, L, mu = 100., .5, .002
        uf, uL, umu = .2, .001, .000002
        samples = 4*rng.normal(mu,umu,100000)*rng.normal(L,uL,100000)**2*rng.normal(f,uf,100000)**2
        predicted = tension_uncertainty(f,L,mu,uf,uL,umu)
        self.assertAlmostEqual(predicted/samples.std(), 1., delta=.015)

    def test_synthetic_peak_with_noise(self):
        rate = 8000
        t = np.arange(rate*2)/rate
        x = np.exp(-t)*np.sin(2*np.pi*123.4*t) + .01*np.random.default_rng(12).normal(size=len(t))
        measured = spectrum_peak(x, rate, 30, 500)
        self.assertAlmostEqual(measured['peak_Hz'], 123.4, delta=.04)
        self.assertFalse(measured['fundamental_automatically_verified'])

    def test_loud_harmonic_not_declared_fundamental(self):
        t = np.arange(16000)/8000
        x = np.sin(2*np.pi*100*t) + 1.5*np.sin(2*np.pi*200*t)
        result = spectrum_peak(x,8000,30,500)
        self.assertAlmostEqual(result['peak_Hz'],200,delta=.1)
        self.assertTrue(any('ambiguous' in warning for warning in result['warnings']))

    def test_compare_and_specimen_holdout(self):
        f = predict_frequency(4,.5,.002)
        record = dict(record_id='synthetic-1', specimen_id='synthetic-a', role='validation',
            fundamental_confirmed=True, reference_force_N=4, loaded_length_m=.5,
            loaded_linear_density_kg_m=.002, frequency_repeats_Hz=[f,f,f])
        result = compare_records([record])
        self.assertAlmostEqual(result['validation_specimen_weighted_mean_absolute_relative_force_error'],0)
        with tempfile.TemporaryDirectory() as directory:
            plot = Path(directory)/'SYNTHETIC_TEST.png'
            plot_comparison(result,plot)
            self.assertGreater(plot.stat().st_size,1000)
            with self.assertRaises(FileExistsError):
                plot_comparison(result,plot)
        with self.assertRaises(ValueError):
            compare_records([record, dict(record, record_id='synthetic-2',role='pilot')])


class CampaignTests(unittest.TestCase):
    def test_main_extension_refuses_incomplete_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'campaign'; folder.mkdir()
            plan = dict(sizes=[32,64,96,128], concentrations=[.5,.15],
                        max_sweeps=1_000_000, replicas=16, T_final_over_tc=.65)
            (folder / 'manifest.json').write_text(json.dumps({'identity':{'plan':plan}}))
            with self.assertRaisesRegex(ValueError, 'Campaign incomplete'):
                analyse_main_extension(folder, root / 'out')
            self.assertFalse((root / 'out').exists())

    def test_exact_synthetic_power_law(self):
        t = np.geomspace(1, 10000, 40)
        trajectories = np.array([a*t**(1/3) for a in (1,1.2,.8,1.1)])
        alpha, lo, hi = bootstrap_slope(t,trajectories,t>10,draws=50)
        for value in (alpha,lo,hi):
            self.assertAlmostEqual(value,1/3,places=12)

    def test_short_windows_not_fitted(self):
        t = np.arange(10.,15.)
        self.assertTrue(np.isnan(fit_slope(t,t**.3,np.ones(5,dtype=bool))))

    def test_replica_reproducibility_conservation_and_heat(self):
        config = KawasakiConfig(L=12, concentration=.15, n_replicas=1,
            max_sweeps=30, n_time_samples=10, eq_sweeps_initial=5, seed=175)
        a, b = one_replica(config), one_replica(config)
        for key in ('snapshots','delta_energy','lengths','correlations'):
            np.testing.assert_equal(a[key],b[key])
        magnetization = a['snapshots'].sum(axis=(1,2))
        np.testing.assert_equal(magnetization, np.full(len(magnetization),a['magnetization']))
        snapshots = a['snapshots'].astype(float)
        energy = -config.Jx*np.sum(snapshots*np.roll(snapshots,1,axis=2),axis=(1,2))-config.Jy*np.sum(snapshots*np.roll(snapshots,1,axis=1),axis=(1,2))
        np.testing.assert_allclose(np.diff(energy),a['delta_energy'][1:],atol=1e-9)

    def test_campaign_temperature_ratios_are_resolved_against_tc(self):
        plan = dict(Jx=1., Jy=1., max_sweeps=20, time_samples=6, equilibration=0,
                    T_initial_over_tc=3., T_final_over_tc=.6)
        config = config_from_plan(plan, 12, .5, 18)
        default = KawasakiConfig(Jx=1., Jy=1.)
        tc = default.T_final / .65
        self.assertAlmostEqual(config.T_initial, 3*tc)
        self.assertAlmostEqual(config.T_final, .6*tc)

    def test_export_preserves_unresolved_and_negative_values(self):
        lattice = np.ones((4,4),dtype=np.int8)
        record = dict(sweep=10,batch_sweeps=10,length_x_sites=float('nan'),length_y_sites=.7,
            delta_energy=4.,bath_entropy_flow_per_spin_per_sweep=-.025)
        with zipfile.ZipFile(io.BytesIO(export_zip([record],lattice,dict(L=4)))) as archive:
            data = archive.read('raw.csv').decode()
            self.assertIn('nan',data)
            self.assertIn('-0.025',data)
            np.testing.assert_equal(np.load(io.BytesIO(archive.read('snapshot.npy'))),lattice)
            self.assertEqual(json.loads(archive.read('metadata.json'))['format_version'],1)

    def test_reference_benchmark_requires_declaration_and_preserves_all_snapshots(self):
        config = KawasakiConfig(L=12, concentration=.5, n_replicas=1,
            max_sweeps=30, n_time_samples=6, eq_sweeps_initial=5, seed=173)
        result = one_replica(config)
        declaration = dict(reference="Example, DOI:10.example/test", purpose="Measurement check",
            dynamics_match="Declared", postprocessing_match="Declared", observable_match="Declared",
            comparison_scope="Symmetric only", reviewer_status="not_yet_reviewed", student_verified=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / 'campaign'; campaign.mkdir()
            plan = dict(sizes=[12], concentrations=[.5], replicas=1, max_sweeps=30,
                time_samples=6, equilibration=5, Jx=1., Jy=1., seed=173)
            (campaign/'manifest.json').write_text(json.dumps(dict(identity=dict(plan=plan))))
            np.savez_compressed(campaign/'c0_L12_rep000.npz', **result)
            declaration_path = root/'declaration.json'; declaration_path.write_text(json.dumps(declaration))
            table = measure_campaign(campaign, declaration_path, root/'output')
            with table.open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), len(result['t']))
            self.assertEqual({int(row['sweep']) for row in rows}, set(result['t']))
            with self.assertRaises(FileExistsError):
                measure_campaign(campaign, declaration_path, root/'output')
            declaration_path.write_text(json.dumps(dict(declaration, student_verified=False)))
            with self.assertRaises(ValueError):
                load_declaration(declaration_path)


if __name__ == '__main__':
    unittest.main()
