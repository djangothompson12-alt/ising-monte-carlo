"""
ising_engine.py
================

Numba-accelerated Metropolis Monte Carlo engine for the 2D square-lattice
Ising model with periodic boundary conditions.

Statistical mechanics background
---------------------------------
The Ising Hamiltonian for a configuration of spins :math:`\\sigma_i \\in \\{-1, +1\\}`
on a lattice with nearest-neighbor coupling :math:`J` and no external field is

.. math::
    H = -J \\sum_{\\langle i, j \\rangle} \\sigma_i \\sigma_j

where :math:`\\langle i, j \\rangle` denotes a sum over nearest-neighbor pairs
(each pair counted once). At temperature :math:`T` (with :math:`k_B \\equiv 1`,
:math:`\\beta = 1/T`), configurations are sampled from the Boltzmann
distribution :math:`P(\\sigma) \\propto e^{-\\beta H(\\sigma)}` using single-spin-flip
Metropolis dynamics: a spin :math:`\\sigma_i` is flipped with probability
:math:`\\min(1, e^{-\\beta \\Delta E})`, where :math:`\\Delta E` is the energy change
of the flip. This Markov chain has the Boltzmann distribution as its unique
stationary distribution (detailed balance + ergodicity).

From long-run trajectories at each temperature, four thermodynamic
observables are estimated (per spin, extensive quantities divided by
:math:`N = L^2`):

.. math::
    \\langle |M| \\rangle = \\frac{1}{N}\\Big\\langle \\Big| \\sum_i \\sigma_i \\Big| \\Big\\rangle,
    \\qquad
    \\langle E \\rangle = \\frac{1}{N}\\langle H \\rangle

.. math::
    C_v = \\frac{1}{N T^2}\\big(\\langle H^2 \\rangle - \\langle H \\rangle^2\\big),
    \\qquad
    \\chi = \\frac{1}{N T}\\big(\\langle M^2 \\rangle - \\langle |M| \\rangle^2\\big)

:math:`C_v` (specific heat) and :math:`\\chi` (magnetic susceptibility) are
fluctuation-dissipation quantities: both diverge (in the infinite-lattice
limit) at the critical temperature :math:`T_c \\approx 2.269 J / k_B`
(Onsager's exact result, :math:`T_c = 2 / \\ln(1 + \\sqrt{2})`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numba import njit

#: Onsager's exact critical temperature for the 2D square-lattice Ising model (J = 1, k_B = 1).
T_CRITICAL: float = 2.0 / np.log(1.0 + np.sqrt(2.0))


@dataclass
class SimulationConfig:
    """Parameters controlling a temperature-sweep Monte Carlo run.

    Attributes:
        L: Linear lattice dimension (lattice has L * L spins).
        J: Nearest-neighbor coupling constant.
        t_min: Lowest temperature sampled.
        t_max: Highest temperature sampled.
        n_temperatures: Number of temperature points between t_min and t_max.
        eq_sweeps: Equilibration (burn-in) sweeps discarded before sampling.
        mc_sweeps: Number of full-lattice sweeps sampled after equilibration.
        sample_interval: Sweeps between successive samples (thins autocorrelation).
        seed: Base random seed; each temperature gets a derived, distinct seed.
    """

    L: int = 24
    J: float = 1.0
    t_min: float = 1.2
    t_max: float = 3.6
    n_temperatures: int = 40
    eq_sweeps: int = 3000
    mc_sweeps: int = 4000
    sample_interval: int = 4
    seed: int = 42

    def temperatures(self) -> np.ndarray:
        """Return the array of temperatures to sweep over."""
        return np.linspace(self.t_min, self.t_max, self.n_temperatures)


@dataclass
class SweepResult:
    """Aggregated observables from a full temperature sweep.

    All arrays are indexed in parallel with `temperatures`, one entry per
    temperature point.
    """

    temperatures: np.ndarray
    magnetization: np.ndarray
    energy: np.ndarray
    specific_heat: np.ndarray
    susceptibility: np.ndarray
    magnetization_err: np.ndarray = field(default_factory=lambda: np.array([]))
    energy_err: np.ndarray = field(default_factory=lambda: np.array([]))


def init_lattice(L: int, seed: int) -> np.ndarray:
    """Initialize an L x L lattice of random +-1 spins ("hot start").

    Args:
        L: Linear lattice dimension.
        seed: Seed for the NumPy random generator.

    Returns:
        An (L, L) array of dtype int8 with entries in {-1, +1}.
    """
    rng = np.random.default_rng(seed)
    return rng.choice(np.array([-1, 1], dtype=np.int8), size=(L, L))


@njit(cache=True)
def _metropolis_sweep(lattice: np.ndarray, beta: float, J: float) -> None:
    """Perform one Monte Carlo sweep (L*L single-spin-flip attempts) in place.

    Each attempt picks a random site, computes the energy change dE of
    flipping it (using the periodic nearest-neighbor sum), and accepts the
    flip with the Metropolis probability min(1, exp(-beta * dE)).
    """
    L = lattice.shape[0]
    for _ in range(L * L):
        i = np.random.randint(0, L)
        j = np.random.randint(0, L)
        s = lattice[i, j]
        neighbor_sum = (
            lattice[(i + 1) % L, j]
            + lattice[(i - 1) % L, j]
            + lattice[i, (j + 1) % L]
            + lattice[i, (j - 1) % L]
        )
        dE = 2.0 * J * s * neighbor_sum
        if dE <= 0.0 or np.random.random() < np.exp(-beta * dE):
            lattice[i, j] = -s


@njit(cache=True)
def _total_energy(lattice: np.ndarray, J: float) -> float:
    """Compute the total Hamiltonian energy H = -J * sum_<i,j> s_i s_j.

    Each bond is counted once by summing only the "right" and "down"
    neighbors of every site under periodic boundary conditions.
    """
    L = lattice.shape[0]
    E = 0.0
    for i in range(L):
        for j in range(L):
            s = lattice[i, j]
            neighbor_sum = lattice[(i + 1) % L, j] + lattice[i, (j + 1) % L]
            E += -J * s * neighbor_sum
    return E


@njit(cache=True)
def _total_magnetization(lattice: np.ndarray) -> float:
    """Compute the total magnetization M = sum_i s_i."""
    return float(np.sum(lattice))


@njit(cache=True)
def _run_at_temperature(
    lattice: np.ndarray,
    beta: float,
    J: float,
    eq_sweeps: int,
    mc_sweeps: int,
    sample_interval: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Equilibrate the lattice, then sample energy/magnetization at fixed T.

    Returns:
        (energies, magnetizations): total (not per-spin) samples collected
        every `sample_interval` sweeps after equilibration, mutating
        `lattice` in place.
    """
    for _ in range(eq_sweeps):
        _metropolis_sweep(lattice, beta, J)

    n_samples = mc_sweeps // sample_interval
    energies = np.empty(n_samples, dtype=np.float64)
    magnetizations = np.empty(n_samples, dtype=np.float64)

    sample_idx = 0
    for sweep in range(mc_sweeps):
        _metropolis_sweep(lattice, beta, J)
        if (sweep + 1) % sample_interval == 0 and sample_idx < n_samples:
            energies[sample_idx] = _total_energy(lattice, J)
            magnetizations[sample_idx] = _total_magnetization(lattice)
            sample_idx += 1

    return energies, magnetizations


def simulate_temperature(
    T: float,
    config: SimulationConfig,
    seed: int,
    return_lattice: bool = False,
) -> dict:
    """Run equilibration + sampling at a single temperature and reduce to observables.

    Args:
        T: Temperature (k_B = 1).
        config: Simulation parameters (lattice size, sweep counts, coupling).
        seed: Random seed for this temperature's lattice initialization and dynamics.
        return_lattice: If True, include the final equilibrated lattice snapshot.

    Returns:
        Dictionary with per-spin observables `magnetization`, `energy`,
        `specific_heat`, `susceptibility`, plus standard errors on the mean
        for magnetization/energy, and optionally `lattice`.
    """
    N = config.L * config.L
    beta = 1.0 / T

    lattice = init_lattice(config.L, seed)
    energies, magnetizations = _run_at_temperature(
        lattice, beta, config.J, config.eq_sweeps, config.mc_sweeps, config.sample_interval
    )

    abs_m = np.abs(magnetizations)

    mean_E = np.mean(energies)
    mean_M = np.mean(abs_m)
    var_E = np.var(energies)
    var_M = np.var(abs_m)

    specific_heat = var_E / (N * T**2)
    susceptibility = var_M / (N * T)

    n_samples = len(energies)
    result = {
        "magnetization": mean_M / N,
        "energy": mean_E / N,
        "specific_heat": specific_heat,
        "susceptibility": susceptibility,
        "magnetization_err": np.std(abs_m) / np.sqrt(n_samples) / N,
        "energy_err": np.std(energies) / np.sqrt(n_samples) / N,
    }
    if return_lattice:
        result["lattice"] = lattice
    return result


def run_temperature_sweep(config: SimulationConfig) -> SweepResult:
    """Sweep temperature and compute |M|, E, Cv, chi at each point.

    Args:
        config: Simulation parameters.

    Returns:
        A SweepResult with one entry per temperature in config.temperatures().
    """
    temperatures = config.temperatures()
    n = len(temperatures)

    magnetization = np.empty(n)
    energy = np.empty(n)
    specific_heat = np.empty(n)
    susceptibility = np.empty(n)
    magnetization_err = np.empty(n)
    energy_err = np.empty(n)

    for idx, T in enumerate(temperatures):
        seed = config.seed + idx
        obs = simulate_temperature(T, config, seed=seed)
        magnetization[idx] = obs["magnetization"]
        energy[idx] = obs["energy"]
        specific_heat[idx] = obs["specific_heat"]
        susceptibility[idx] = obs["susceptibility"]
        magnetization_err[idx] = obs["magnetization_err"]
        energy_err[idx] = obs["energy_err"]

    return SweepResult(
        temperatures=temperatures,
        magnetization=magnetization,
        energy=energy,
        specific_heat=specific_heat,
        susceptibility=susceptibility,
        magnetization_err=magnetization_err,
        energy_err=energy_err,
    )


def sample_snapshot(T: float, config: SimulationConfig, seed: int) -> np.ndarray:
    """Equilibrate a fresh lattice at temperature T and return the spin configuration.

    Args:
        T: Temperature (k_B = 1).
        config: Simulation parameters (lattice size, coupling, equilibration length).
        seed: Random seed for lattice initialization and dynamics.

    Returns:
        The (L, L) int8 spin lattice after `config.eq_sweeps` equilibration sweeps.
    """
    obs = simulate_temperature(T, config, seed=seed, return_lattice=True)
    return obs["lattice"]
