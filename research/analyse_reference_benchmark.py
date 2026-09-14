"""Analyse a completed, student-verified symmetric literature-measurement table.

Reports both raw chord slopes and a fixed measured initial-length subtraction.
No shift is optimised to obtain 1/3. Whole replicas are bootstrap units.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from research.analyse_campaign import fit_slope


WINDOWS = ((1_000, 200_000), (1_000, 4_500_000), (200_000, 4_500_000))
INITIAL_SWEEP_TARGET = 20
BOOTSTRAP_DRAWS = 500


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slopes(times: np.ndarray, trajectories: np.ndarray, lower: int, upper: int,
            initial_index: int | None) -> tuple[float, float, float, int, int | None, int | None]:
    mask = (times >= lower) & (times <= upper)
    if initial_index is None:
        scaled_time = times.astype(float)
        transformed = trajectories
    else:
        scaled_time = times.astype(float) - float(times[initial_index])
        transformed = trajectories - trajectories[:, [initial_index]]
        mask &= times > times[initial_index]
    mask &= np.all(np.isfinite(transformed) & (transformed > 0), axis=0)
    used_min = int(times[mask][0]) if mask.any() else None
    used_max = int(times[mask][-1]) if mask.any() else None
    if mask.sum() < 4 or scaled_time[mask][-1] / scaled_time[mask][0] < 5:
        return float("nan"), float("nan"), float("nan"), int(mask.sum()), used_min, used_max
    estimate = fit_slope(scaled_time, transformed.mean(axis=0), mask)
    rng = np.random.default_rng(20260913)
    draws = np.asarray([fit_slope(scaled_time, transformed[rng.integers(len(trajectories), size=len(trajectories))].mean(axis=0), mask)
                        for _ in range(BOOTSTRAP_DRAWS)])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(estimate), float(lo), float(hi), int(mask.sum()), used_min, used_max


def analyse(folder: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory")
    provenance_path = folder / "provenance.json"
    table_path = folder / "reference_measurements.csv"
    provenance = json.loads(provenance_path.read_text())
    if provenance["declaration"]["student_verified"] is not True:
        raise ValueError("Comparison declaration was not student verified")
    plan = provenance["plan"]
    with table_path.open(newline="") as stream:
        input_rows = list(csv.DictReader(stream))
    files = sorted({row["input_file"] for row in input_rows})
    if len(files) != plan["replicas"] * len(plan["sizes"]):
        raise ValueError("Measurement table does not contain the full planned replica inventory")
    if len(plan["sizes"]) != 1:
        raise ValueError("This analysis currently requires one planned lattice size")
    paths = [sorted((row for row in input_rows if row["input_file"] == name), key=lambda row: int(row["sweep"])) for name in files]
    times = np.asarray([int(row["sweep"]) for row in paths[0]])
    if any(not np.array_equal(times, [int(row["sweep"]) for row in path]) for path in paths[1:]):
        raise ValueError("Replicas have mismatched time checkpoints")
    values = np.asarray([[float(row["mean_chord_length"]) for row in path] for path in paths])
    if not np.all(np.isfinite(values)):
        raise ValueError("Unresolved chord lengths must be inspected before this fit")
    index = int(np.argmin(abs(times - INITIAL_SWEEP_TARGET)))
    if abs(np.log(times[index] / INITIAL_SWEEP_TARGET)) > np.log(1.2):
        raise ValueError("No checkpoint near the declared initial sweep t=20")
    records = []
    for lower, upper in WINDOWS:
        if upper > plan["max_sweeps"]:
            continue
        for label, initial in (("raw", None), ("measured_initial_length_subtracted", index)):
            estimate, lo, hi, n_points, used_min, used_max = _slopes(times, values, lower, upper, initial)
            records.append(dict(method=label, nominal_t_min=lower, nominal_t_max=upper,
                                initial_sweep=int(times[index]) if initial is not None else "",
                                n_replicas=len(files), n_points=n_points, used_t_min=used_min, used_t_max=used_max,
                                alpha=estimate, bootstrap_low=lo, bootstrap_high=hi))
    output.mkdir(parents=True)
    result = output / "reference_fits.csv"
    with result.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    mean = values.mean(axis=0)
    se = values.std(axis=0, ddof=1) / np.sqrt(len(values))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    axes[0].plot(times, mean, color="tab:blue")
    axes[0].fill_between(times, mean-se, mean+se, color="tab:blue", alpha=0.2)
    axes[0].set(xscale="log", yscale="log", xlabel="Post-quench sweeps", ylabel="Mean finite chord length (sites)", title="Raw majority-filtered chords")
    positive = (times > times[index]) & (mean > mean[index])
    axes[1].plot(times[positive] - times[index], mean[positive] - mean[index], color="tab:orange")
    axes[1].set(xscale="log", yscale="log", xlabel=f"Sweeps since t={times[index]}",
                ylabel="Mean chord length minus measured initial length", title="Fixed initial-length sensitivity")
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.suptitle(f"L={plan['sizes'][0]}, c=0.5, n={len(files)}; no fitted offset")
    fig.savefig(output / "reference_chord_growth.png", dpi=180)
    plt.close(fig)
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=_hash(Path(__file__)), input_table_sha256=_hash(table_path),
        input_provenance_sha256=_hash(provenance_path), windows=WINDOWS,
        initial_sweep_target=INITIAL_SWEEP_TARGET, selected_initial_sweep=int(times[index]),
        bootstrap_draws=BOOTSTRAP_DRAWS,
        interpretation="Fixed-window effective slopes only. Numerical agreement with 1/3 or the source paper requires independent methodological review."),
        indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measurement_folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(analyse(args.measurement_folder, args.output))
