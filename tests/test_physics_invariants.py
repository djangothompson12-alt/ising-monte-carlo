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
from phase_diagram import (anisotropic_critical_temperature, binodal_temperature,
                           exact_coexistence_compositions,
                           exact_spontaneous_magnetization,
                           regular_solution_chemical_potential,
                           regular_solution_free_energy, regular_solution_omega,
                           spinodal_temperature)


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

    def test_every_nearest_neighbour_swap_energy_and_balance(self) -> None:
        """Exercise both anisotropic bond directions, including periodic seams."""
        beta, jx, jy = 0.8, 0.7, 1.3
        for seed in range(5):
            lattice = model_b._seed_and_init_lattice(4, 1200 + seed, 0.5)
            before = anisotropic_energy(lattice, jx, jy)
            for row in range(4):
                for col in range(4):
                    for dr, dc, bond in ((0, 1, jx), (0, -1, jx),
                                          (1, 0, jy), (-1, 0, jy)):
                        other = ((row + dr) % 4, (col + dc) % 4)
                        if lattice[row, col] == lattice[other]:
                            continue
                        local_delta = (2 * lattice[row, col] *
                                       (model_b._local_field(lattice, row, col, jx, jy)
                                        - model_b._local_field(lattice, *other, jx, jy))
                                       + 4 * bond)
                        swapped = lattice.copy()
                        swapped[row, col], swapped[other] = swapped[other], swapped[row, col]
                        direct_delta = anisotropic_energy(swapped, jx, jy) - before
                        self.assertAlmostEqual(local_delta, direct_delta, places=10)
                        forward = min(1., np.exp(-beta * direct_delta))
                        reverse = min(1., np.exp(beta * direct_delta))
                        self.assertAlmostEqual(forward / reverse,
                                               np.exp(-beta * direct_delta), places=10)

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

    def test_regular_solution_binodal_satisfies_common_tangent(self) -> None:
        self.assertAlmostEqual(float(binodal_temperature(0.5, 1.0, 1.0)), 4.0)
        self.assertAlmostEqual(float(binodal_temperature(0.0, 1.0, 1.0)), 0.0)
        self.assertAlmostEqual(float(binodal_temperature(1.0, 1.0, 1.0)), 0.0)
        for fraction in np.linspace(0.02, 0.48, 24):
            temperature = float(binodal_temperature(fraction, 1.0, 1.0))
            self.assertGreater(temperature, float(spinodal_temperature(fraction, 1.0, 1.0)))
            self.assertAlmostEqual(float(regular_solution_chemical_potential(fraction, temperature, 1.0, 1.0)), 0.0, places=10)
            left = float(regular_solution_free_energy(fraction, temperature, 1.0, 1.0))
            right = float(regular_solution_free_energy(1.0-fraction, temperature, 1.0, 1.0))
            self.assertAlmostEqual(left, right, places=10)
            self.assertLess(left, float(regular_solution_free_energy(0.5, temperature, 1.0, 1.0)))
            curvature = temperature / (fraction * (1.0-fraction)) - 2.0 * regular_solution_omega(1.0, 1.0)
            self.assertGreater(curvature, 0.0)
            grid = np.linspace(0.0, 1.0, 501)
            self.assertGreaterEqual(float(np.min(regular_solution_free_energy(grid, temperature, 1.0, 1.0))),
                                    left - 1e-4)

    def test_dilute_quenches_are_metastable_only_in_mean_field(self) -> None:
        final_temperature = 0.65 * anisotropic_critical_temperature(1.0, 1.0)
        for fraction in (0.06, 0.10):
            self.assertLess(float(spinodal_temperature(fraction, 1.0, 1.0)), final_temperature)
            self.assertGreater(float(binodal_temperature(fraction, 1.0, 1.0)), final_temperature)
        self.assertGreater(float(spinodal_temperature(0.15, 1.0, 1.0)), final_temperature)

    def test_exact_2d_coexistence_limits_and_mass_balance(self) -> None:
        tc = 2.0 / np.log(1.0 + np.sqrt(2.0))
        temperatures = np.array([0.0, 0.65 * tc, tc, 1.2 * tc])
        magnetizations = exact_spontaneous_magnetization(temperatures, 1.0, 1.0)
        low, high = exact_coexistence_compositions(temperatures, 1.0, 1.0)
        self.assertAlmostEqual(float(magnetizations[0]), 1.0)
        self.assertAlmostEqual(float(magnetizations[1]), 0.9878880274703111, places=12)
        np.testing.assert_allclose(magnetizations[2:], 0.0, atol=1e-14)
        np.testing.assert_allclose(low + high, 1.0, atol=1e-14)
        self.assertAlmostEqual(float(low[1]), 0.006055986264844437, places=12)
        # Lever-rule arithmetic describes equilibrium area fractions only;
        # it is not a claim that these finite-time trajectories equilibrated.
        phase_fraction = (0.15 - low[1]) / (high[1] - low[1])
        self.assertTrue(0.0 < phase_fraction < 1.0)
        self.assertAlmostEqual(float((1-phase_fraction)*low[1] + phase_fraction*high[1]), 0.15)
        self.assertTrue(all(low[1] < c < high[1] for c in (0.06, 0.10, 0.15, 0.25, 0.35, 0.50)))

    def test_exact_2d_anisotropic_formula_has_the_right_critical_point(self) -> None:
        tc = anisotropic_critical_temperature(1.0, 0.5)
        self.assertAlmostEqual(float(exact_spontaneous_magnetization(tc, 1.0, 0.5)), 0.0)
        self.assertGreater(float(exact_spontaneous_magnetization(0.65*tc, 1.0, 0.5)), 0.0)
        for fraction in (0.2, 0.65, 0.95):
            self.assertAlmostEqual(
                float(exact_spontaneous_magnetization(fraction*tc, 1.0, 0.5)),
                float(exact_spontaneous_magnetization(fraction*tc, 0.5, 1.0)), places=13)
        with self.assertRaises(ValueError):
            exact_spontaneous_magnetization(-1.0, 1.0, 1.0)
        with self.assertRaises(ValueError):
            exact_spontaneous_magnetization(1.0, 0.0, 1.0)

    def test_composition_quenches_are_not_all_inside_mean_field_spinodal(self) -> None:
        final_temperature = 0.65 * model_b.anisotropic_critical_temperature(1.0, 1.0)
        self.assertLess(float(spinodal_temperature(0.06, 1.0, 1.0)), final_temperature)
        self.assertLess(float(spinodal_temperature(0.10, 1.0, 1.0)), final_temperature)
        self.assertGreater(float(spinodal_temperature(0.15, 1.0, 1.0)), final_temperature)


if __name__ == "__main__":
    unittest.main()
