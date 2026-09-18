"""Independently recalculate the declared main-extension tables from raw NPZs.

This is an arithmetic/provenance audit, not a second physical model or an
independent experiment. It does not import the production analysis functions.
Run only after the 128-file campaign and declared analysis have completed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


WINDOWS = ((1_000, 20_000), (1_000, 200_000), (20_000, 200_000),
           (20_000, 1_000_000), (200_000, 1_000_000))
METHODS = ("primary_unfiltered", "ell_over_L_below_0.15_sensitivity")
TOLERANCE = 1e-10


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal_number(actual: float, recorded: float) -> bool:
    return bool((np.isnan(actual) and np.isnan(recorded)) or
                (np.isfinite(actual) and np.isfinite(recorded) and
                 np.isclose(actual, recorded, rtol=0, atol=TOLERANCE)))


def check_number(label: str, actual: float, recorded: str | float) -> float:
    value = float(recorded)
    if not equal_number(actual, value):
        raise ValueError(f"{label}: raw recomputation {actual} differs from table {value}")
    return abs(actual - value) if np.isfinite(actual) else 0.0


def slope(times: np.ndarray, lengths: np.ndarray, mask: np.ndarray) -> float:
    """Ordinary unweighted log-log slope, written without numpy.polyfit."""
    keep = mask & np.isfinite(lengths) & (lengths > 0) & (times > 0)
    if keep.sum() < 4 or times[keep][-1] / times[keep][0] < 5:
        return float("nan")
    x, y = np.log(times[keep]), np.log(lengths[keep])
    x0 = x - x.mean()
    return float(np.dot(x0, y - y.mean()) / np.dot(x0, x0))


def slope_interval(times: np.ndarray, trajectories: np.ndarray,
                   mask: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(20260913)
    draws = np.asarray([
        slope(times, trajectories[rng.integers(len(trajectories), size=len(trajectories))].mean(axis=0), mask)
        for _ in range(500)
    ])
    if np.isfinite(draws).sum() < 450:
        return float("nan"), float("nan")
    low, high = np.nanpercentile(draws, (2.5, 97.5))
    return float(low), float(high)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def audit(campaign: Path, analysis: Path) -> dict:
    manifest_path, status_path = campaign / "manifest.json", campaign / "status.json"
    manifest, status = json.loads(manifest_path.read_text()), json.loads(status_path.read_text())
    plan = manifest["identity"]["plan"]
    if (status.get("state") != "complete" or status.get("completed") != 128 or
            plan["sizes"] != [32, 64, 96, 128] or
            plan["concentrations"] != [0.5, 0.15] or
            plan["replicas"] != 16 or plan["max_sweeps"] != 1_000_000 or
            plan["T_final_over_tc"] != 0.65):
        raise ValueError("Not the completed, frozen 0.65 Tc extension")

    provenance = json.loads((analysis / "manifest.json").read_text())
    if provenance["campaign_manifest_sha256"] != digest(manifest_path):
        raise ValueError("Analysis manifest points to a different campaign")
    paths = {p.name: p for p in campaign.glob("*.npz")}
    expected = {f"c{ci}_L{side}_rep{rep:03d}.npz"
                for ci in range(2) for side in plan["sizes"] for rep in range(16)}
    if set(paths) != expected or set(provenance["input_sha256"]) != expected:
        raise ValueError("Raw-file inventory or analysis provenance is incomplete")
    for name in expected:
        if digest(paths[name]) != provenance["input_sha256"][name]:
            raise ValueError(f"Raw file changed after analysis: {name}")

    groups: dict[tuple[float, int], tuple[np.ndarray, np.ndarray]] = {}
    for ci, concentration in enumerate(plan["concentrations"]):
        for side in plan["sizes"]:
            times, runs = None, []
            for rep in range(16):
                with np.load(paths[f"c{ci}_L{side}_rep{rep:03d}.npz"], allow_pickle=False) as raw:
                    t = np.asarray(raw["t"], dtype=int)
                    lengths = np.asarray(raw["lengths"], dtype=float)
                if lengths.shape != (len(t), 2) or t[-1] != 1_000_000:
                    raise ValueError("Incomplete or malformed raw trajectory")
                if times is not None and not np.array_equal(times, t):
                    raise ValueError("Checkpoint grid differs within a condition")
                times = t
                runs.append(lengths)
            groups[(float(concentration), side)] = (times, np.asarray(runs))

    errors: dict[str, float] = {}

    def compare(field: str, actual: float, recorded: str | float) -> None:
        errors[field] = max(errors.get(field, 0.0), check_number(field, actual, recorded))

    means = read_csv(analysis / "ensemble_lengths.csv")
    expected_means = {(c, side, int(t)) for (c, side), (times, _) in groups.items() for t in times}
    seen = set()
    for row in means:
        key = (float(row["composition"]), int(row["L"]), int(row["sweep"]))
        if key not in expected_means or key in seen or int(row["n_replicas"]) != 16:
            raise ValueError("Unexpected or duplicate ensemble row")
        seen.add(key)
        t, directional = groups[key[:2]]
        j = int(np.flatnonzero(t == key[2])[0])
        both = directional[:, j, :]
        resolved = np.isfinite(both) & (both > 0)
        if (row["resolved_all"] != str(bool(np.all(resolved))) or
                int(row["resolved_x"]) != int(resolved[:, 0].sum()) or
                int(row["resolved_y"]) != int(resolved[:, 1].sum())):
            raise ValueError("Resolved-length count differs from raw data")
        per_run = both.mean(axis=1)
        average = float(per_run.mean())
        compare("mean_length_x", float(both[:, 0].mean()), row["mean_length_x"])
        compare("mean_length_y", float(both[:, 1].mean()), row["mean_length_y"])
        compare("mean_length", average, row["mean_length"])
        compare("standard_error", float(per_run.std(ddof=1) / 4), row["standard_error"])
        compare("length_over_L", average / key[1], row["length_over_L"])
    if seen != expected_means:
        raise ValueError("Missing ensemble rows")

    fits = read_csv(analysis / "fit_windows.csv")
    expected_fits = {(c, side, lower, upper, method)
                     for (c, side) in groups for lower, upper in WINDOWS for method in METHODS}
    seen = set()
    for row in fits:
        key = (float(row["composition"]), int(row["L"]),
               int(row["nominal_t_min"]), int(row["nominal_t_max"]), row["method"])
        if key not in expected_fits or key in seen or int(row["n_replicas"]) != 16:
            raise ValueError("Unexpected or duplicate fit row")
        seen.add(key)
        times, directional = groups[key[:2]]
        per_run = directional.mean(axis=2)
        average = per_run.mean(axis=0)
        resolved = np.all(np.isfinite(directional) & (directional > 0), axis=(0, 2))
        mask = resolved & (times >= key[2]) & (times <= key[3])
        if key[4] == METHODS[1]:
            mask &= average / key[1] < 0.15
        actual_first = str(int(times[mask][0])) if mask.any() else ""
        actual_last = str(int(times[mask][-1])) if mask.any() else ""
        if (int(row["n_points"]) != int(mask.sum()) or
                row["used_t_min"] != actual_first or row["used_t_max"] != actual_last):
            raise ValueError("Fit time mask differs from frozen rule")
        compare("alpha", slope(times, average, mask), row["alpha"])
        low, high = slope_interval(times, per_run, mask)
        compare("bootstrap_low", low, row["bootstrap_low"])
        compare("bootstrap_high", high, row["bootstrap_high"])
        if mask.any():
            compare("max_length_over_L", float(np.max((average / key[1])[mask])),
                    row["max_length_over_L"])
        elif row["max_length_over_L"] != "":
            raise ValueError("Unresolved fit has a recorded maximum length")
    if seen != expected_fits:
        raise ValueError("Missing fit rows")

    matched = read_csv(analysis / "matched_size_ratios.csv")
    expected_ratios = {(c, side, int(t))
                       for c in plan["concentrations"] for side in (32, 64, 96)
                       for t in groups[(float(c), 128)][0]}
    seen = set()
    ratio_draws: dict[tuple[float, int], tuple[np.ndarray, np.ndarray]] = {}
    for ci, c in enumerate(plan["concentrations"]):
        for side in (32, 64, 96):
            t_small, small = groups[(float(c), side)]
            t_ref, ref = groups[(float(c), 128)]
            if not np.array_equal(t_small, t_ref):
                raise ValueError("Size groups lack matched checkpoints")
            small_lengths, ref_lengths = small.mean(axis=2), ref.mean(axis=2)
            rng = np.random.default_rng(20260917 + 100 * ci + side)
            small_idx = rng.integers(16, size=(500, 16))
            ref_idx = rng.integers(16, size=(500, 16))
            ratio_draws[(float(c), side)] = (small_lengths[small_idx].mean(axis=1),
                                              ref_lengths[ref_idx].mean(axis=1))
    for row in matched:
        key = (float(row["composition"]), int(row["L"]), int(row["sweep"]))
        if key not in expected_ratios or key in seen or int(row["reference_L"]) != 128 or \
                int(row["n_small"]) != 16 or int(row["n_reference"]) != 16:
            raise ValueError("Unexpected or duplicate matched-size row")
        seen.add(key)
        times, small = groups[key[:2]]
        _, ref = groups[(key[0], 128)]
        j = int(np.flatnonzero(times == key[2])[0])
        small_resolved = bool(np.all(np.isfinite(small[:, j, :]) & (small[:, j, :] > 0)))
        ref_resolved = bool(np.all(np.isfinite(ref[:, j, :]) & (ref[:, j, :] > 0)))
        resolved = small_resolved and ref_resolved
        if (row["status"] != ("resolved" if resolved else "unresolved") or
                row["resolved_small"] != str(small_resolved) or
                row["resolved_reference"] != str(ref_resolved)):
            raise ValueError("Matched-size missingness differs from raw data")
        small_mean = float(small[:, j, :].mean(axis=1).mean())
        ref_mean = float(ref[:, j, :].mean(axis=1).mean())
        compare("mean_small", small_mean, row["mean_small"])
        compare("mean_reference", ref_mean, row["mean_reference"])
        if resolved:
            compare("difference_sites", small_mean - ref_mean, row["difference_sites"])
            compare("ratio", small_mean / ref_mean, row["ratio"])
            small_boot, ref_boot = ratio_draws[key[:2]]
            low, high = np.percentile(small_boot[:, j] / ref_boot[:, j], (2.5, 97.5))
            compare("ratio_low", float(low), row["ratio_low"])
            compare("ratio_high", float(high), row["ratio_high"])
        else:
            for name in ("difference_sites", "ratio", "ratio_low", "ratio_high"):
                compare(name, float("nan"), row[name])
    if seen != expected_ratios:
        raise ValueError("Missing matched-size rows")

    return {
        "audit_source_sha256": digest(Path(__file__)),
        "campaign_manifest_sha256": digest(manifest_path),
        "analysis_manifest_sha256": digest(analysis / "manifest.json"),
        "analysis_table_sha256": {
            name: digest(analysis / name)
            for name in ("ensemble_lengths.csv", "fit_windows.csv", "matched_size_ratios.csv")
        },
        "raw_files_checked": len(paths),
        "ensemble_rows_checked": len(means),
        "fit_rows_checked": len(fits),
        "matched_size_rows_checked": len(matched),
        "maximum_absolute_differences": errors,
        "absolute_tolerance": TOLERANCE,
        "boundary": "Independent table arithmetic and raw-byte identity only; not proof of a growth law, finite-size onset, or physical alloy validity.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new audit output; do not overwrite a prior result")
    result = audit(args.campaign, args.analysis)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
