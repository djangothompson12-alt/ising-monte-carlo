"""Exploratory, non-tuned initial-length sensitivity on the complete 64-run study.

This does not reproduce Majumder--Das finite-size scaling. For each independent
trajectory, subtract the *measured* length at both saved checkpoints adjacent
to 20 sweeps (18 and 22 in this archive), and shift time by the same amount.
Compare against the raw slope on identical jointly resolved checkpoints.
No offset or time window is optimised to obtain a target exponent.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from research.analyse_campaign import fit_slope


WINDOWS = ((1_000, 200_000), (20_000, 200_000))
INITIAL_SWEEPS = (18, 22)
BOOTSTRAP_DRAWS = 500


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def paired_slopes(times: np.ndarray, trajectories: np.ndarray, *,
                  initial_index: int, lower: int, upper: int,
                  draws: int = BOOTSTRAP_DRAWS, seed: int = 20260917) -> dict:
    """Fit raw/shifted ensemble means and paired whole-trajectory bootstrap.

    The same retained checkpoints are used for both slopes. An unresolved or
    non-positive adjusted value in any independent run removes that checkpoint
    from *both* methods; no changing subset of runs is averaged.
    """
    times = np.asarray(times, dtype=float)
    trajectories = np.asarray(trajectories, dtype=float)
    if times.ndim != 1 or trajectories.ndim != 2 or trajectories.shape[1] != len(times):
        raise ValueError("Expected n_replicas x n_times trajectories")
    if len(trajectories) < 2 or not 0 <= initial_index < len(times):
        raise ValueError("Need at least two replicas and a valid initial index")
    if not np.all(np.diff(times) > 0):
        raise ValueError("Times must be strictly increasing")
    shifted_time = times - times[initial_index]
    shifted_lengths = trajectories - trajectories[:, [initial_index]]
    mask = ((times >= lower) & (times <= upper) & (shifted_time > 0) &
            np.all(np.isfinite(trajectories) & (trajectories > 0) &
                   np.isfinite(shifted_lengths) & (shifted_lengths > 0), axis=0))
    count = int(mask.sum())
    if count < 4 or shifted_time[mask][-1] / shifted_time[mask][0] < 5:
        return dict(points=count, used_t_min=int(times[mask][0]) if count else "",
                    used_t_max=int(times[mask][-1]) if count else "",
                    raw=float("nan"), shifted=float("nan"), delta=float("nan"),
                    delta_low=float("nan"), delta_high=float("nan"))

    def estimates(sample: np.ndarray) -> tuple[float, float]:
        raw = fit_slope(times, sample.mean(axis=0), mask)
        shifted = fit_slope(shifted_time,
                            (sample - sample[:, [initial_index]]).mean(axis=0), mask)
        return raw, shifted

    raw, shifted = estimates(trajectories)
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(draws):
        sample = trajectories[rng.integers(len(trajectories), size=len(trajectories))]
        sample_raw, sample_shifted = estimates(sample)
        deltas.append(sample_shifted - sample_raw)
    deltas = np.asarray(deltas)
    finite = deltas[np.isfinite(deltas)]
    lo, hi = np.percentile(finite, [2.5, 97.5]) if len(finite) >= .9 * draws else (float("nan"), float("nan"))
    return dict(points=count, used_t_min=int(times[mask][0]),
                used_t_max=int(times[mask][-1]), raw=raw, shifted=shifted,
                delta=shifted - raw, delta_low=float(lo), delta_high=float(hi))


def analyse(folder: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory")
    manifest_path = folder / "manifest.json"
    status = json.loads((folder / "status.json").read_text())
    manifest = json.loads(manifest_path.read_text())
    plan = manifest["identity"]["plan"]
    if (status.get("state") != "complete" or status.get("completed") != 64 or
            plan["sizes"] != [32, 64, 96, 128] or
            plan["concentrations"] != [0.5, 0.15] or
            plan["replicas"] != 8 or plan["max_sweeps"] != 200_000):
        raise ValueError("Input is not the complete frozen 64-run study")
    expected = {f"c{ci}_L{L}_rep{rep:03d}.npz"
                for ci in range(2) for L in plan["sizes"] for rep in range(8)}
    actual = {path.name for path in folder.glob("*.npz")}
    if actual != expected:
        raise ValueError(f"Replica inventory differs: {len(expected-actual)} missing, {len(actual-expected)} unexpected")

    rows = []
    hashes = {}
    for ci, composition in enumerate(plan["concentrations"]):
        for size in plan["sizes"]:
            runs = []
            for rep in range(8):
                path = folder / f"c{ci}_L{size}_rep{rep:03d}.npz"
                with np.load(path, allow_pickle=False) as data:
                    times = np.asarray(data["t"], dtype=int)
                    directional = np.asarray(data["lengths"], dtype=float)
                if times[-1] != 200_000 or directional.shape != (len(times), 2):
                    raise ValueError(f"Incomplete or malformed replica: {path}")
                runs.append((times, directional.mean(axis=1)))
                hashes[path.name] = sha(path)
            times = runs[0][0]
            if any(not np.array_equal(times, other_times) for other_times, _ in runs[1:]):
                raise ValueError(f"Time grids differ for c={composition}, L={size}")
            if not set(INITIAL_SWEEPS).issubset(set(times.tolist())):
                raise ValueError("Declared 18- and 22-sweep initial checkpoints are absent")
            trajectories = np.asarray([lengths for _, lengths in runs])
            for initial_sweep in INITIAL_SWEEPS:
                index = int(np.searchsorted(times, initial_sweep))
                for lower, upper in WINDOWS:
                    result = paired_slopes(times, trajectories, initial_index=index,
                                           lower=lower, upper=upper)
                    rows.append(dict(composition=composition, L=size,
                                     n_replicas=len(runs), initial_sweep=initial_sweep,
                                     nominal_t_min=lower, nominal_t_max=upper,
                                     **result))
    output.mkdir(parents=True)
    table = output / "paired_initial_length_fits.csv"
    with table.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)), campaign_manifest_sha256=sha(manifest_path),
        input_sha256=hashes, initial_sweeps=INITIAL_SWEEPS, windows=WINDOWS,
        bootstrap_draws=BOOTSTRAP_DRAWS, bootstrap_unit="independent trajectory",
        interpretation="Exploratory fixed-measured-offset sensitivity, not a fitted asymptotic law or literature reproduction",
    ), indent=2) + "\n")
    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(analyse(args.campaign_folder, args.output))
