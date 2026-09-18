"""Compare actual Kawasaki samples with an exactly enumerated 3×3 ensemble.

This checks one finite equilibrium sector, not coarsening or physical time.
The small lattice is deliberately separate from every growth-law campaign.
"""

from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path

import numpy as np

from model_b import kawasaki_engine as engine
from research.imaging_benchmark import sha


L, N_UP, JX, JY, BETA = 3, 4, 0.7, 1.3, 0.4
SEEDS = (20260917, 20260918, 20260919)
BURN_SWEEPS = 2000
SAMPLE_GAP_SWEEPS = 10
SAMPLES_PER_SEED = 4000
BATCH_SIZE = 100


def energy(spins: np.ndarray) -> float:
    field = spins.astype(np.float64)
    return float(-JX * np.sum(field * np.roll(field, 1, axis=1))
                 -JY * np.sum(field * np.roll(field, 1, axis=0)))


def exact_moments() -> tuple[int, float, float]:
    values = []
    for positive in combinations(range(L * L), N_UP):
        flat = np.full(L * L, -1, dtype=np.int8)
        flat[list(positive)] = 1
        values.append(energy(flat.reshape(L, L)))
    energies = np.asarray(values)
    weights = np.exp(-BETA * (energies - energies.min()))
    probabilities = weights / weights.sum()
    mean = float(np.sum(probabilities * energies))
    variance = float(np.sum(probabilities * (energies - mean) ** 2))
    return len(values), mean, variance


def check(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    states, exact_mean, exact_variance = exact_moments()
    means = []
    all_batches = []
    for seed in SEEDS:
        lattice = engine._seed_and_init_lattice(L, seed, N_UP / (L * L))
        initial_count = int(np.count_nonzero(lattice > 0))
        if initial_count != N_UP:
            raise ValueError("Initial composition mismatch")
        engine._run_n_sweeps(lattice, BETA, JX, JY, BURN_SWEEPS)
        observations = np.empty(SAMPLES_PER_SEED)
        for index in range(SAMPLES_PER_SEED):
            engine._run_n_sweeps(lattice, BETA, JX, JY, SAMPLE_GAP_SWEEPS)
            if int(np.count_nonzero(lattice > 0)) != N_UP:
                raise ValueError("Kawasaki composition was not conserved")
            observations[index] = energy(lattice)
        means.append(float(observations.mean()))
        all_batches.extend(observations.reshape(-1, BATCH_SIZE).mean(axis=1))
    batch_means = np.asarray(all_batches)
    sampled_mean = float(np.mean(means))
    batch_standard_error = float(np.std(batch_means, ddof=1) / np.sqrt(len(batch_means)))
    difference = sampled_mean - exact_mean
    # This is a conservative screening rule, not a formal model-selection test.
    tolerance = max(5 * batch_standard_error, 0.03)
    if abs(difference) > tolerance:
        raise ValueError(f"Sampler/exact mean discrepancy {difference:.4g} exceeds {tolerance:.4g}")
    result = dict(
        status="passed finite-equilibrium diagnostic",
        scope="3x3 fixed-composition canonical sector only; not late-time coarsening validation",
        states=states, n_up=N_UP, Jx=JX, Jy=JY, beta=BETA,
        seeds=SEEDS, burn_sweeps=BURN_SWEEPS,
        sample_gap_sweeps=SAMPLE_GAP_SWEEPS, samples_per_seed=SAMPLES_PER_SEED,
        batch_size=BATCH_SIZE, independent_seed_means=means,
        exact_mean_energy=exact_mean, exact_energy_variance=exact_variance,
        sampled_mean_energy=sampled_mean, sampled_minus_exact=difference,
        batch_standard_error=batch_standard_error, screening_tolerance=tolerance,
        source_sha256=sha(Path(__file__)), engine_sha256=sha(Path(engine.__file__)),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.output), indent=2))
