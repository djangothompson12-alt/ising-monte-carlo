"""Small, deterministic checks of the physics contracts used in the paper.

These tests are deliberately about invariants, not about reproducing fitted
exponents from expensive production runs.  They are fast enough for every
GitHub push and catch errors that can otherwise yield plausible-looking plots.
"""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import quad

# Make direct execution (``python tests/test_physics_invariants.py``) and
# unittest discovery behave identically.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model_a import ising_engine as model_a
from model_a import ising_3d_engine as model_a_3d
from model_b import kawasaki_engine as model_b
from model_b import kawasaki_3d_engine as model_b_3d
from phase_diagram import regular_solution_omega, spinodal_temperature


def anisotropic_energy(lattice: np.ndarray, Jx: float, Jy: float) -> float:
    """Reference Hamiltonian with each periodic bond counted once."""
    horizontal = lattice * np.roll(lattice, -1, axis=1)
    vertical = lattice * np.roll(lattice, -1, axis=0)
    return float(-Jx * horizontal.sum() - Jy * vertical.sum())


class TestPhysicsInvariants(unittest.TestCase):
    def test_exact_isotropic_critical_temperature(self) -> None:
        expected = 2.0 / np.log(1.0 + np.sqrt(2.0))
        actual = model_b.anisotropic_critical_temperature(1.0, 1.0)
        self.assertAlmostEqual(actual, expected, places=12)

    def test_kawasaki_conserves_composition_and_tracks_energy(self) -> None:
        lattice = model_b._seed_and_init_lattice(16, 20260910, 0.35)
        magnetization_before = int(lattice.sum())
        energy_before = anisotropic_energy(lattice, 1.0, 0.5)

        reported_delta = model_b._kawasaki_sweep(lattice, 1.0 / 1.2, 1.0, 0.5)

        self.assertEqual(int(lattice.sum()), magnetization_before)
        measured_delta = anisotropic_energy(lattice, 1.0, 0.5) - energy_before
        self.assertAlmostEqual(reported_delta, measured_delta, places=10)

    def test_metropolis_tracks_hamiltonian_energy(self) -> None:
        lattice = model_a._seed_and_init_lattice(16, 20260910, 0.5)
        energy_before = model_a._total_energy(lattice, 1.0)

        reported_delta = model_a._metropolis_sweep(lattice, 1.0 / 1.5, 1.0)

        measured_delta = model_a._total_energy(lattice, 1.0) - energy_before
        self.assertAlmostEqual(reported_delta, measured_delta, places=10)

    def test_cubic_metropolis_tracks_hamiltonian_energy(self) -> None:
        lattice = model_a_3d._seed_and_init_lattice_3d(4, 20260911, 0.5)
        energy_before = model_a_3d._total_energy_3d(lattice, 1.0)
        reported_delta = model_a_3d._metropolis_sweep_3d(lattice, 1.0 / 3.0, 1.0)
        measured_delta = model_a_3d._total_energy_3d(lattice, 1.0) - energy_before
        self.assertAlmostEqual(reported_delta, measured_delta, places=10)

    def test_cubic_kawasaki_conserves_composition_and_tracks_energy(self) -> None:
        lattice = model_b_3d._seed_and_init_lattice_3d(4, 20260911, 0.375)
        magnetization_before = int(lattice.sum())
        energy_before = model_b_3d._total_energy_3d(lattice, 1.0, 0.7, 1.3)
        reported_delta = model_b_3d._kawasaki_sweep_3d(lattice, 1.0 / 3.0, 1.0, 0.7, 1.3)
        self.assertEqual(int(lattice.sum()), magnetization_before)
        measured_delta = model_b_3d._total_energy_3d(lattice, 1.0, 0.7, 1.3) - energy_before
        self.assertAlmostEqual(reported_delta, measured_delta, places=10)

    def test_periodic_components_join_across_both_seams(self) -> None:
        mask = np.zeros((7, 7), dtype=bool)
        mask[0, 3] = mask[-1, 3] = True
        mask[4, 0] = mask[4, -1] = True

        labels, component_count = model_b._periodic_label(mask)

        self.assertEqual(component_count, 2)
        self.assertEqual(labels[0, 3], labels[-1, 3])
        self.assertEqual(labels[4, 0], labels[4, -1])

    def test_lsw_distribution_is_normalized(self) -> None:
        def density(u: float) -> float:
            return float(model_b.lsw_scaling_function(np.array([u]))[0])

        # Supplying near-endpoint subintervals helps the adaptive integrator
        # resolve the compact-support cutoff without changing the function.
        integral, error = quad(
            density,
            0.0,
            1.5,
            epsabs=1e-11,
            epsrel=1e-11,
            limit=1000,
            points=[1.0, 1.4, 1.49],
        )
        self.assertLess(error, 1e-8)
        self.assertAlmostEqual(integral, 1.0, places=7)

    def test_regular_solution_mapping(self) -> None:
        self.assertAlmostEqual(regular_solution_omega(1.0, 1.0), 8.0)
        self.assertAlmostEqual(float(spinodal_temperature(0.5, 1.0, 1.0)), 4.0)
        self.assertAlmostEqual(float(spinodal_temperature(0.5, 1.0, 0.5)), 3.0)


if __name__ == "__main__":
    unittest.main()
