"""Read-only arithmetic audit of the original 64-run growth-analysis tables.

Rebuilds ensemble means, finite-window slopes and whole-replica bootstrap
percentiles without calling research.analyse_campaign. This verifies the
reported numbers for that fixed analysis recipe, not that the recipe uniquely
isolates a physical asymptotic exponent.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from research.imaging_benchmark import sha


TOLERANCE = 1e-11


def _same_number(computed: float, reported: float) -> bool:
    return bool((np.isnan(computed) and np.isnan(reported))
                or np.isclose(computed, reported, rtol=0.0, atol=TOLERANCE))


def log_slope(times: np.ndarray, lengths: np.ndarray, selected: np.ndarray) -> float:
    """Unweighted log-log least-squares slope using explicit covariance."""
    keep = selected & np.isfinite(lengths) & (lengths > 0) & (times > 0)
    if keep.sum() < 4 or times[keep][-1] / times[keep][0] < 5:
        return float("nan")
    x = np.log(times[keep])
    y = np.log(lengths[keep])
    centered = x - x.mean()
    return float(np.dot(centered, y - y.mean()) / np.dot(centered, centered))


def _bootstrap(times: np.ndarray, trajectories: np.ndarray, selected: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(17)
    values = []
    for _ in range(500):
        indices = rng.integers(len(trajectories), size=len(trajectories))
        values.append(log_slope(times, trajectories[indices].mean(axis=0), selected))
    values = np.asarray(values)
    if np.isfinite(values).sum() < 450:
        return float("nan"), float("nan")
    low, high = np.nanpercentile(values, [2.5, 97.5])
    return float(low), float(high)


def _check(label: str, computed: float, reported: float) -> float:
    if not _same_number(computed, reported):
        raise ValueError(f"{label} mismatch: recomputed={computed}, reported={reported}")
    return abs(computed - reported) if np.isfinite(computed) else 0.0


def audit(folder: Path) -> dict:
    analysis = folder / "analysis"
    provenance = json.loads((analysis / "analysis_manifest.json").read_text())
    if provenance["campaign_manifest_sha256"] != sha(folder / "manifest.json"):
        raise ValueError("Analysis points to a different campaign manifest")
    recorded = provenance["raw_files"]
    paths = {path.name: path for path in folder.glob("*.npz")}
    if set(recorded) != set(paths):
        raise ValueError("Analysis input inventory differs from current NPZ files")
    for name, digest in recorded.items():
        if sha(paths[name]) != digest:
            raise ValueError(f"Raw replica changed since analysis: {name}")

    with (analysis / "exponents.csv").open(newline="") as stream:
        fits = list(csv.DictReader(stream))
    with (analysis / "ensemble_lengths.csv").open(newline="") as stream:
        means_table = list(csv.DictReader(stream))
    if not fits or not means_table:
        raise ValueError("Missing growth-analysis rows")

    groups: dict[tuple[float, int], tuple[np.ndarray, np.ndarray]] = {}
    plan = json.loads((folder / "manifest.json").read_text())["identity"]["plan"]
    for ci, concentration in enumerate(plan["concentrations"]):
        for side in plan["sizes"]:
            trajectories = []
            times = None
            for replica in range(plan["replicas"]):
                path = paths[f"c{ci}_L{side}_rep{replica:03d}.npz"]
                with np.load(path, allow_pickle=False) as item:
                    current = item["t"]
                    if times is not None and not np.array_equal(times, current):
                        raise ValueError(f"Checkpoint mismatch in {path.name}")
                    times = current.copy()
                    trajectories.append(item["lengths"].mean(axis=1))
            groups[(float(concentration), side)] = (times, np.asarray(trajectories))

    maximum_fit_error = 0.0
    maximum_interval_error = 0.0
    for row in fits:
        concentration, side = float(row["c"]), int(row["L"])
        times, trajectories = groups[(concentration, side)]
        if int(row["n"]) != len(trajectories):
            raise ValueError("Replica count mismatch")
        mean = trajectories.mean(axis=0)  # Never nanmean: fixed replica set.
        selected = ((times >= int(row["t_min"]))
                    & (times <= int(row["t_max"]))
                    & (mean / side < 0.15))
        if int(row["n_points"]) != int(selected.sum()):
            raise ValueError(f"Retained-point count mismatch for c={concentration}, L={side}")
        slope = log_slope(times, mean, selected)
        maximum_fit_error = max(maximum_fit_error, _check("Slope", slope, float(row["alpha"])))
        low, high = _bootstrap(times, trajectories, selected)
        maximum_interval_error = max(maximum_interval_error,
                                     _check("Bootstrap low", low, float(row["bootstrap_low"])),
                                     _check("Bootstrap high", high, float(row["bootstrap_high"])))
        _check("Maximum length/L", float(np.nanmax(mean / side)), float(row["max_length_over_L"]))

    maximum_mean_error = 0.0
    maximum_se_error = 0.0
    expected_mean_rows = sum(len(times) for times, _ in groups.values())
    if len(means_table) != expected_mean_rows:
        raise ValueError("Ensemble-length table has an unexpected number of rows")
    seen = set()
    for row in means_table:
        concentration, side, sweep = float(row["c"]), int(row["L"]), int(row["t"])
        key = (concentration, side, sweep)
        if key in seen:
            raise ValueError("Duplicate ensemble-length row")
        seen.add(key)
        times, trajectories = groups[(concentration, side)]
        positions = np.flatnonzero(times == sweep)
        if len(positions) != 1 or int(row["n"]) != len(trajectories):
            raise ValueError("Ensemble-length time or count mismatch")
        column = trajectories[:, int(positions[0])]
        mean = float(column.mean())
        se = float(column.std(ddof=1) / np.sqrt(len(column)))
        maximum_mean_error = max(maximum_mean_error, _check("Ensemble mean", mean, float(row["length"])))
        maximum_se_error = max(maximum_se_error, _check("Replica SE", se, float(row["standard_error"])))

    return {
        "campaign": str(folder),
        "campaign_manifest_sha256": sha(folder / "manifest.json"),
        "exponents_csv_sha256": sha(analysis / "exponents.csv"),
        "ensemble_lengths_csv_sha256": sha(analysis / "ensemble_lengths.csv"),
        "raw_file_hashes_checked": len(paths),
        "fit_rows_checked": len(fits),
        "ensemble_length_rows_checked": len(means_table),
        "maximum_absolute_slope_difference": maximum_fit_error,
        "maximum_absolute_bootstrap_endpoint_difference": maximum_interval_error,
        "maximum_absolute_ensemble_mean_difference": maximum_mean_error,
        "maximum_absolute_replica_se_difference": maximum_se_error,
        "absolute_tolerance": TOLERANCE,
        "boundary": "Checks the saved analysis recipe and arithmetic only; the fit window, cutoff, observable and model remain scientific choices.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; audit records are immutable")
    result = audit(args.folder)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
