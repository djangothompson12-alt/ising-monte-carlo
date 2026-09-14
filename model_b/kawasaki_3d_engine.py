"""Conserved Kawasaki dynamics on a three-dimensional anisotropic cubic lattice.

The array convention is ``(z, y, x)``.  ``Jx``, ``Jy`` and ``Jz`` couple
neighbours along the last, middle and first axes respectively.  The 2D engine
and all of its published analysis are intentionally left untouched.

Unlike the anisotropic 2D square model, the 3D anisotropic Ising critical
surface has no exact Onsager-style closed form.  Quench temperatures are thus
explicit inputs; callers must justify them rather than treating them as an
exactly known reduced temperature.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit


@dataclass(frozen=True)
class CubicKawasakiConfig:
    """Parameters for a 3D conserved-order-parameter quench."""

    L: int = 32
    Jx: float = 1.0
    Jy: float = 1.0
    Jz: float = 1.0
    T_initial: float = 8.0
    T_final: float = 3.0
    concentration: float = 0.5
    eq_sweeps_initial: int = 100
    seed: int = 123


def init_lattice_3d(L: int, seed: int, concentration: float = 0.5) -> np.ndarray:
    """Return a seeded cubic volume with an exact rounded +1-spin fraction."""
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
def _local_field_3d(
    lattice: np.ndarray, z: int, y: int, x: int, Jx: float, Jy: float, Jz: float
) -> float:
    L = lattice.shape[0]
    return (
        Jx * (lattice[z, y, (x + 1) % L] + lattice[z, y, (x - 1) % L])
        + Jy * (lattice[z, (y + 1) % L, x] + lattice[z, (y - 1) % L, x])
        + Jz * (lattice[(z + 1) % L, y, x] + lattice[(z - 1) % L, y, x])
    )


@njit(cache=True)
def _kawasaki_sweep_3d(
    lattice: np.ndarray, beta: float, Jx: float, Jy: float, Jz: float
) -> float:
    """Perform ``L**3`` nearest-neighbour exchange attempts in place.

    The energy-change expression is the 3D extension of the 2D engine: the
    swapped bond itself is invariant, leaving only each site's other bonds.
    """
    L = lattice.shape[0]
    total_dE = 0.0
    for _ in range(L * L * L):
        z = np.random.randint(0, L)
        y = np.random.randint(0, L)
        x = np.random.randint(0, L)
        direction = np.random.randint(0, 6)
        if direction == 0:
            z2, y2, x2, J_bond = z, y, (x + 1) % L, Jx
        elif direction == 1:
            z2, y2, x2, J_bond = z, y, (x - 1) % L, Jx
        elif direction == 2:
            z2, y2, x2, J_bond = z, (y + 1) % L, x, Jy
        elif direction == 3:
            z2, y2, x2, J_bond = z, (y - 1) % L, x, Jy
        elif direction == 4:
            z2, y2, x2, J_bond = (z + 1) % L, y, x, Jz
        else:
            z2, y2, x2, J_bond = (z - 1) % L, y, x, Jz

        s_i = lattice[z, y, x]
        s_j = lattice[z2, y2, x2]
        if s_i == s_j:
            continue
        field_i = _local_field_3d(lattice, z, y, x, Jx, Jy, Jz)
        field_j = _local_field_3d(lattice, z2, y2, x2, Jx, Jy, Jz)
        dE = 2.0 * s_i * (field_i - field_j) + 4.0 * J_bond
        if dE <= 0.0 or np.random.random() < np.exp(-beta * dE):
            lattice[z, y, x] = s_j
            lattice[z2, y2, x2] = s_i
            total_dE += dE
    return total_dE


@njit(cache=True)
def _total_energy_3d(lattice: np.ndarray, Jx: float, Jy: float, Jz: float) -> float:
    """Return the anisotropic cubic Hamiltonian, counting each bond once."""
    L = lattice.shape[0]
    energy = 0.0
    for z in range(L):
        for y in range(L):
            for x in range(L):
                spin = lattice[z, y, x]
                energy -= spin * (
                    Jx * lattice[z, y, (x + 1) % L]
                    + Jy * lattice[z, (y + 1) % L, x]
                    + Jz * lattice[(z + 1) % L, y, x]
                )
    return energy


@njit(cache=True)
def _run_n_sweeps_3d(
    lattice: np.ndarray, beta: float, Jx: float, Jy: float, Jz: float, n_sweeps: int
) -> float:
    total_dE = 0.0
    for _ in range(n_sweeps):
        total_dE += _kawasaki_sweep_3d(lattice, beta, Jx, Jy, Jz)
    return total_dE


def run_quench_snapshot_3d(
    config: CubicKawasakiConfig, target_sweeps: int, seed: int | None = None
) -> np.ndarray:
    """Equilibrate, quench and return a raw conserved cubic-lattice snapshot."""
    if target_sweeps < 0:
        raise ValueError("target_sweeps must be non-negative")
    run_seed = config.seed if seed is None else seed
    lattice = _seed_and_init_lattice_3d(config.L, run_seed, config.concentration)
    _run_n_sweeps_3d(
        lattice, 1.0 / config.T_initial, config.Jx, config.Jy, config.Jz, config.eq_sweeps_initial
    )
    _run_n_sweeps_3d(
        lattice, 1.0 / config.T_final, config.Jx, config.Jy, config.Jz, target_sweeps
    )
    return lattice
