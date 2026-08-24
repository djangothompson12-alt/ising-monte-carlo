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
from scipy.fft import fft2, ifft2

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


@dataclass
class QuenchConfig:
    """Parameters for a non-equilibrium temperature quench.

    The lattice is first equilibrated at `T_initial`, then the temperature
    is instantaneously dropped to `T_final` and evolved for `max_sweeps`
    sweeps, with the spin-spin correlation function recorded at
    logarithmically spaced sweep counts. Averaging over `n_replicas`
    independent runs suppresses realization noise in the extracted domain size.

    Attributes:
        L: Linear lattice dimension (lattice has L * L spins).
        J: Nearest-neighbor coupling constant.
        T_initial: Temperature the lattice is equilibrated at before the quench.
        T_final: Post-quench temperature the system evolves at.
        n_replicas: Number of independent quench realizations to average over.
        max_sweeps: Number of post-quench sweeps to evolve.
        n_time_samples: Number of logarithmically spaced sweep counts to sample.
        eq_sweeps_initial: Sweeps used to equilibrate at T_initial before the quench.
        seed: Base random seed; each replica gets a derived, distinct seed.
    """

    L: int = 128
    J: float = 1.0
    T_initial: float = 5.0
    T_final: float = 1.5
    n_replicas: int = 16
    max_sweeps: int = 2000
    n_time_samples: int = 28
    eq_sweeps_initial: int = 200
    seed: int = 123


@dataclass
class QuenchResult:
    """Domain-growth kinetics extracted from a quench.

    Attributes:
        t: Post-quench sweep counts (Monte Carlo time) at which C(r, t) was sampled.
        domain_size: Characteristic domain size L(t), averaged over replicas.
        domain_size_err: Standard error of L(t) across replicas.
    """

    t: np.ndarray
    domain_size: np.ndarray
    domain_size_err: np.ndarray


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


# ---------------------------------------------------------------------------
# Non-equilibrium quench kinetics
# ---------------------------------------------------------------------------
#
# Quenching the system from a high-temperature disordered state to T_final < T_c
# breaks ergodicity: ferromagnetic domains nucleate and coarsen over time rather
# than the lattice reaching global equilibrium. Phase-ordering ("Allen-Cahn" /
# Lifshitz-Allen-Cahn) theory predicts that for a non-conserved scalar order
# parameter (single-spin-flip dynamics, as here), domains grow as a power law
#
#     L(t) ~ t^n,   n = 1/2
#
# driven by curvature-reducing interface motion. L(t) is estimated from the
# equal-time spatial spin-autocorrelation function
#
#     C(r, t) = < sigma_i(t) sigma_{i+r}(t) >
#
# averaged over lattice sites i and the two principal lattice directions,
# as the (interpolated) distance r at which C(r, t) first decays to 1/2.


def _axis_correlation(lattice: np.ndarray, r_max: int) -> np.ndarray:
    """Compute C(r) = <sigma_i sigma_{i+r}> for r = 0..r_max via 2D FFT.

    By the Wiener-Khinchin theorem, the full periodic 2D autocorrelation of
    the spin field equals the inverse FFT of its power spectrum. This gives
    every displacement (dx, dy) at once in O(L^2 log L), versus the
    O(L^2 * r_max) cost of directly summing shifted-lattice products for
    each r individually. The two axis correlations needed here are then a
    vectorized slice out of that 2D result.

    Averaged over all lattice sites and both principal (x, y) directions,
    under periodic boundary conditions.
    """
    L = lattice.shape[0]
    spins = lattice.astype(np.float64)
    power_spectrum = np.abs(fft2(spins)) ** 2
    autocorr = ifft2(power_spectrum).real / (L * L)  # autocorr[dx, dy], periodic

    C = np.empty(r_max + 1)
    C[0] = 1.0
    if r_max > 0:
        C[1:] = 0.5 * (autocorr[1 : r_max + 1, 0] + autocorr[0, 1 : r_max + 1])
    return C


@njit(cache=True)
def _init_lattice_jit(L: int) -> np.ndarray:
    """Random +-1 lattice drawn from Numba's own RNG (seedable with np.random.seed inside jit)."""
    lattice = np.empty((L, L), dtype=np.int8)
    for i in range(L):
        for j in range(L):
            lattice[i, j] = 1 if np.random.random() < 0.5 else -1
    return lattice


@njit(cache=True)
def _seed_and_init_lattice(L: int, seed: int) -> np.ndarray:
    """Seed Numba's RNG and return a fresh random +-1 lattice.

    Seeding Numba's RNG (rather than only seeding the initial lattice via
    NumPy's generator) makes every subsequent jitted Metropolis sweep that
    follows -- not just the initial condition -- deterministic given `seed`.
    """
    np.random.seed(seed)
    return _init_lattice_jit(L)


@njit(cache=True)
def _run_n_sweeps(lattice: np.ndarray, beta: float, J: float, n_sweeps: int) -> None:
    """Advance `lattice` by n_sweeps Metropolis sweeps in place."""
    for _ in range(n_sweeps):
        _metropolis_sweep(lattice, beta, J)


def _run_quench_replica(
    L: int,
    seed: int,
    beta_initial: float,
    beta_final: float,
    J: float,
    eq_sweeps_initial: int,
    checkpoints: np.ndarray,
    r_max: int,
) -> np.ndarray:
    """Run one full, independently seeded quench replica: init -> equilibrate at
    T_initial -> quench to T_final -> record C(r,t) at each checkpoint.

    Sweeps advance in Numba-jitted chunks between checkpoints; C(r,t) is then
    measured with the FFT-based `_axis_correlation`, which (relying on SciPy)
    cannot run inside nopython-mode Numba code, so this outer orchestration
    stays in plain Python while the hot inner loop (`_run_n_sweeps`) stays jitted.

    Returns:
        Array of shape (len(checkpoints), r_max + 1): C(r) at each checkpoint.
    """
    lattice = _seed_and_init_lattice(L, seed)
    _run_n_sweeps(lattice, beta_initial, J, eq_sweeps_initial)

    n_checkpoints = len(checkpoints)
    C_traj = np.zeros((n_checkpoints, r_max + 1))
    sweep = 0
    for k in range(n_checkpoints):
        _run_n_sweeps(lattice, beta_final, J, int(checkpoints[k]) - sweep)
        sweep = int(checkpoints[k])
        C_traj[k] = _axis_correlation(lattice, r_max)
    return C_traj


def _log_time_checkpoints(max_sweeps: int, n_points: int) -> np.ndarray:
    """Return unique, ascending, logarithmically spaced integer sweep counts in [1, max_sweeps]."""
    raw = np.logspace(0.0, np.log10(max_sweeps), n_points)
    checkpoints = np.unique(np.round(raw).astype(np.int64))
    return checkpoints[checkpoints >= 1]


def domain_size_from_correlation(C: np.ndarray) -> float:
    """Extract the characteristic domain size as the r where C(r) crosses 0.5.

    Linearly interpolates between the two integer separations bracketing the
    crossing. Returns NaN if C(r) never decays to 0.5 within the sampled
    range (e.g. too early after the quench, or the correlation length has
    outgrown the measurable half-lattice at late times).
    """
    for r in range(len(C) - 1):
        if C[r] >= 0.5 > C[r + 1]:
            span = C[r] - C[r + 1]
            if span <= 0.0:
                return float(r)
            frac = (C[r] - 0.5) / span
            return r + frac
    return float("nan")


def run_quench_kinetics(config: QuenchConfig) -> QuenchResult:
    """Simulate a T_initial -> T_final quench and extract domain-growth kinetics L(t).

    For each of `config.n_replicas` independent runs, a lattice is equilibrated
    at `T_initial`, instantaneously cooled to `T_final`, and evolved while
    sampling C(r, t) at logarithmically spaced sweep counts; L(t) is then
    extracted per replica and averaged.

    Args:
        config: Quench simulation parameters.

    Returns:
        A QuenchResult with domain_size(t) and its standard error across replicas.
    """
    checkpoints = _log_time_checkpoints(config.max_sweeps, config.n_time_samples)
    r_max = config.L // 2
    n_ckpt = len(checkpoints)

    L_replicas = np.full((config.n_replicas, n_ckpt), np.nan)

    beta_initial = 1.0 / config.T_initial
    beta_final = 1.0 / config.T_final

    for rep in range(config.n_replicas):
        C_traj = _run_quench_replica(
            config.L,
            config.seed + rep,
            beta_initial,
            beta_final,
            config.J,
            config.eq_sweeps_initial,
            checkpoints,
            r_max,
        )
        for k in range(n_ckpt):
            L_replicas[rep, k] = domain_size_from_correlation(C_traj[k])

    with np.errstate(invalid="ignore"):
        domain_size = np.nanmean(L_replicas, axis=0)
        domain_size_err = np.nanstd(L_replicas, axis=0) / np.sqrt(config.n_replicas)

    return QuenchResult(
        t=checkpoints.astype(np.float64),
        domain_size=domain_size,
        domain_size_err=domain_size_err,
    )
