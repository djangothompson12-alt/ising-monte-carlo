"""Presentation and data-boundary checks for the two live demonstrations."""

import csv
import io
from pathlib import Path
import unittest
import zipfile

import numpy as np

from model_b import solara_app
from model_b.research_export import export_zip
from model_b.solara_app import (
    _MATERIALS_SCIENCE_MARKDOWN,
    build_domain_figure,
    effective_growth_exponent,
)


ROOT = Path(__file__).resolve().parents[1]


class LiveVisualizerContractTests(unittest.TestCase):
    def test_solara_uses_canonical_engine_module_for_numba_cache(self):
        self.assertEqual(solara_app._kawasaki_sweep.__module__, "model_b.kawasaki_engine")
        lattice = solara_app.init_lattice_at_concentration(8, 2026, 0.5)
        before = int(lattice.sum())
        solara_app._kawasaki_sweep(lattice, 1.0, 1.0, 0.5)
        self.assertEqual(int(lattice.sum()), before)

    def test_model_a_page_names_dynamics_and_exports_unresolved_status(self):
        page = (ROOT / "index.html").read_text()
        self.assertIn("Model A: Metropolis (Non-Conserved) Dynamics", page)
        self.assertNotIn("Glauber", page)
        self.assertIn("axisAveragedAutocorrelation", page)
        self.assertIn("domain_size_status", page)
        self.assertIn('domainSizeStatus: Number.isFinite(domainSize)', page)
        self.assertNotIn("return Number.isFinite(raw) ? Math.max(1.0, raw) : 1.0", page)
        self.assertIn('makeChart("eChart", "E(t)/N", "#a63603", -2.1, 2.1)', page)
        self.assertIn("const bound = 2.0 * J + Math.abs(state.H) + 0.1", page)
        self.assertIn("Exploratory live demonstration", page)

    def test_model_b_context_does_not_claim_rafting_or_growth_law_validation(self):
        self.assertIn("one live trajectory cannot verify a growth law", _MATERIALS_SCIENCE_MARKDOWN)
        self.assertIn("not a simulation of gamma-prime rafting", _MATERIALS_SCIENCE_MARKDOWN)
        self.assertIn("raw export keeps signed values and unresolved lengths", _MATERIALS_SCIENCE_MARKDOWN)

    def test_model_b_reference_is_labelled_as_a_slope_guide(self):
        figure = build_domain_figure([10.0, 100.0], [1.0, 2.0], [1.1, 2.1], (1.0, 1000.0), 32)
        self.assertEqual(figure.data[2].name, "t^(1/3) slope guide")

    def test_single_run_slope_readout_is_unclipped_but_recovers_known_input(self):
        times = np.geomspace(600.0, 100_000.0, 20)
        lengths = times ** (1.0 / 3.0)
        slope = effective_growth_exponent(times.tolist(), lengths.tolist(), lengths.tolist())
        self.assertAlmostEqual(slope, 1.0 / 3.0, places=12)

    def test_model_b_export_keeps_nan_length_and_signed_heat(self):
        records = [dict(sweep=10, batch_sweeps=10, length_x_sites=float("nan"),
                        length_y_sites=1.5, delta_energy=4.0,
                        bath_entropy_flow_per_spin_per_sweep=-0.01)]
        payload = export_zip(records, np.ones((4, 4), dtype=np.int8),
                             dict(L=4, Jx=1.0, Jy=1.0, T_final=1.0))
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            rows = list(csv.DictReader(io.StringIO(archive.read("raw.csv").decode())))
        self.assertEqual(rows[0]["length_x_sites"].lower(), "nan")
        self.assertEqual(float(rows[0]["bath_entropy_flow_per_spin_per_sweep"]), -0.01)


if __name__ == "__main__":
    unittest.main()
