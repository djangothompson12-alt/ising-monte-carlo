"""Metropolis Model A dynamics on a three-dimensional cubic Ising lattice.

This module deliberately lives beside, rather than inside,
``ising_engine.py``: the established two-dimensional analysis remains
unchanged.  A cubic lattice has six nearest neighbours per site and the
Hamiltonian counts one bond in each positive Cartesian direction.

There is no exact three-dimensional analogue of Onsager's two-dimensional
solution.  The often quoted isotropic cubic-lattice critical temperature is a
numerical estimate, not an exact formula, and is not used by this engine.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit


@dataclass(frozen=True)
class CubicQuenchConfig:
    """Parameters for a cubic Model A quench.

    ``L`` gives an ``L x L x L`` volume.  Time is measured in sweeps, where
    one sweep contains ``L**3`` proposed single-spin flips.
    """

    L: int = 32
    J: float = 1.0
    T_initial: float = 8.0
    T_final: float = 3.0
    concentration: float = 0.5
    eq_sweeps_initial: int = 100
    seed: int = 123


def init_lattice_3d(L: int, seed: int, concentration: float = 0.5) -> np.ndarray:
    """Return a seeded random cubic spin volume with entries ``-1`` and ``+1``.

    The initial concentration is exact up to rounding.  Unlike Model B, it
    is not conserved after Model A dynamics begin.
    """
    if not 0.0 <= concentration <= 1.0:
        raise ValueError("concentration must lie in [0, 1]")
    N = L**3
    spins = np.full(N, -1, dtype=np.int8)
    spins[: round(concentration * N)] = 1
    rng = np.random.default_rng(seed)
    rng.shuffle(spins)
    return spins.reshape((L, L, L))


@njit(cache=True)
def _seed_and_init_lattice_3d(L: int, seed: int, concentration: float) -> np.ndarray:
    np.random.seed(seed)
    N = L * L * L
    spins = np.full(N, -1, dtype=np.int8)
    spins[: int(round(concentration * N))] = 1
    np.random.shuffle(spins)
    return spins.reshape((L, L, L))


@njit(cache=True)
def _metropolis_sweep_3d(lattice: np.ndarray, beta: float, J: float) -> float:
    """Perform ``L**3`` periodic, single-spin Metropolis attempts in place."""
    L = lattice.shape[0]
    total_dE = 0.0
    for _ in range(L * L * L):
        z = np.random.randint(0, L)
        y = np.random.randint(0, L)
        x = np.random.randint(0, L)
        spin = lattice[z, y, x]
        neighbor_sum = (
            lattice[z, y, (x + 1) % L]
            + lattice[z, y, (x - 1) % L]
            + lattice[z, (y + 1) % L, x]
            + lattice[z, (y - 1) % L, x]
            + lattice[(z + 1) % L, y, x]
            + lattice[(z - 1) % L, y, x]
        )
        dE = 2.0 * J * spin * neighbor_sum
        if dE <= 0.0 or np.random.random() < np.exp(-beta * dE):
            lattice[z, y, x] = -spin
            total_dE += dE
    return total_dE


@njit(cache=True)
def _total_energy_3d(lattice: np.ndarray, J: float) -> float:
    """Return the cubic-lattice Hamiltonian with every periodic bond once."""
    L = lattice.shape[0]
    energy = 0.0
    for z in range(L):
        for y in range(L):
            for x in range(L):
                spin = lattice[z, y, x]
                energy -= J * spin * (
                    lattice[z, y, (x + 1) % L]
                    + lattice[z, (y + 1) % L, x]
                    + lattice[(z + 1) % L, y, x]
                )
    return energy


@njit(cache=True)
def _run_n_sweeps_3d(lattice: np.ndarray, beta: float, J: float, n_sweeps: int) -> float:
    """Advance a cubic volume and return its summed accepted-move energy change."""
    total_dE = 0.0
    for _ in range(n_sweeps):
        total_dE += _metropolis_sweep_3d(lattice, beta, J)
    return total_dE


def run_quench_snapshot_3d(
    config: CubicQuenchConfig, target_sweeps: int, seed: int | None = None
) -> np.ndarray:
    """Equilibrate then quench a cubic Model A volume and return a raw snapshot.

    This is a dynamics engine, not a calibrated alloy model.  The returned
    array has shape ``(z, y, x)`` and dtype ``int8``.
    """
    if target_sweeps < 0:
        raise ValueError("target_sweeps must be non-negative")
    run_seed = config.seed if seed is None else seed
    lattice = _seed_and_init_lattice_3d(config.L, run_seed, config.concentration)
    _run_n_sweeps_3d(lattice, 1.0 / config.T_initial, config.J, config.eq_sweeps_initial)
    _run_n_sweeps_3d(lattice, 1.0 / config.T_final, config.J, target_sweeps)
    return lattice
