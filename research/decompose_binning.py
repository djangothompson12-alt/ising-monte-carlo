"""Post-hoc separation of block averaging, thresholding and exact-zero ties.

See BINNING_DECOMPOSITION_PROTOCOL.md. This is observation analysis only; it
never advances an Ising lattice or changes either engine's correlation rule.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from research.compare_estimators import paired_slopes
from research.imaging import block_average, image_length
from research.imaging_benchmark import sha, write_csv


CONDITIONS = ("full", "block4_greyscale", "block4_ties_plus", "block4_ties_minus")
ANALYSIS_SOURCES = (
    "decompose_binning.py", "imaging.py", "metrology.py",
    "compare_estimators.py", "analyse_campaign.py", "imaging_benchmark.py",
)
PAIRS = (
    ("full", "block4_greyscale"),
    ("block4_greyscale", "block4_ties_plus"),
    ("block4_greyscale", "block4_ties_minus"),
    ("block4_ties_minus", "block4_ties_plus"),
    ("full", "block4_ties_plus"),
)


def threshold_block(block: np.ndarray, *, ties_plus: bool) -> np.ndarray:
    """Return binary coarse image with an explicit exact-zero convention."""
    if block.ndim != 2 or not np.isfinite(block).all():
        raise ValueError("Expected a finite 2D block image")
    foreground = block >= 0 if ties_plus else block > 0
    return np.where(foreground, 1.0, -1.0)


def _previous_lengths(path: Path) -> dict[tuple[str, int, str], float]:
    previous = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["condition"] in ("full", "bin4") and row["crop_id"] == "full":
                key = (row["file"], int(row["t"]), row["condition"])
                if key in previous:
                    raise ValueError(f"Duplicate earlier observation: {key}")
                previous[key] = float(row["length"])
    return previous


def _checked_previous(previous: dict, file: str, sweep: int, condition: str, length: float) -> None:
    key = (file, sweep, condition)
    if key not in previous:
        raise ValueError(f"Missing earlier observation: {key}")
    old = previous[key]
    if not ((np.isnan(old) and np.isnan(length)) or np.isclose(old, length, rtol=0, atol=1e-12)):
        raise ValueError(f"Earlier observation differs at {key}: {old} vs {length}")


def analyse(folder: Path, previous_csv: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Use a new output directory; prior results are immutable")
    plan = json.loads((folder / "manifest.json").read_text())["identity"]["plan"]
    if 128 not in plan["sizes"]:
        raise ValueError("This declared comparison requires L=128")
    files = sorted(folder.glob("c*_L128_rep*.npz"))
    if len(files) != plan["replicas"] * len(plan["concentrations"]):
        raise ValueError("Incomplete or unexpected L=128 replica inventory")
    previous = _previous_lengths(previous_csv)
    groups: dict[float, dict] = {}
    rows = []
    previous_checks = 0
    for path in files:
        with np.load(path, allow_pickle=False) as archive:
            config = json.loads(str(archive["config"]))
            concentration = float(config["concentration"])
            times = archive["t"]
            snapshots = archive["snapshots"]
            if snapshots.shape != (len(times), 128, 128):
                raise ValueError(f"Unexpected snapshots in {path.name}")
            group = groups.setdefault(concentration, {"times": times.copy(), "replicas": []})
            if not np.array_equal(group["times"], times):
                raise ValueError("Checkpoint grids differ within a composition")
            trajectories = {name: [] for name in CONDITIONS}
            for sweep, snapshot in zip(times, snapshots):
                block = block_average(snapshot, 4)
                ties_plus = threshold_block(block, ties_plus=True)
                ties_minus = threshold_block(block, ties_plus=False)
                if not np.isclose(np.mean(ties_plus > 0) - np.mean(ties_minus > 0),
                                  np.mean(block == 0), rtol=0, atol=1e-15):
                    raise ValueError("Exact-zero tie fraction does not match mask-fraction difference")
                fields = {
                    "full": (snapshot, 1),
                    "block4_greyscale": (block, 4),
                    "block4_ties_plus": (ties_plus, 4),
                    "block4_ties_minus": (ties_minus, 4),
                }
                lengths = {name: image_length(field, spacing)["length"]
                           for name, (field, spacing) in fields.items()}
                _checked_previous(previous, path.name, int(sweep), "full", lengths["full"])
                _checked_previous(previous, path.name, int(sweep), "bin4", lengths["block4_ties_plus"])
                previous_checks += 2
                for name in CONDITIONS:
                    trajectories[name].append(lengths[name])
                rows.append({
                    "file": path.name, "c": concentration, "t": int(sweep),
                    "full_length_sites": lengths["full"],
                    "block4_greyscale_length_sites": lengths["block4_greyscale"],
                    "block4_ties_plus_length_sites": lengths["block4_ties_plus"],
                    "block4_ties_minus_length_sites": lengths["block4_ties_minus"],
                    "full_fraction": float(np.mean(snapshot > 0)),
                    "block4_ties_plus_fraction": float(np.mean(ties_plus > 0)),
                    "block4_ties_minus_fraction": float(np.mean(ties_minus > 0)),
                    "exact_zero_block_fraction": float(np.mean(block == 0)),
                })
            group["replicas"].append(trajectories)
        print(f"Measured {path.name}", flush=True)

    fits = []
    for concentration, group in sorted(groups.items()):
        times = group["times"]
        arrays = {name: np.asarray([replica[name] for replica in group["replicas"]])
                  for name in CONDITIONS}
        stacked = np.stack([arrays[name] for name in CONDITIONS])
        shared = np.all(np.isfinite(stacked) & (stacked > 0), axis=(0, 1))
        windows = [(1000, 20000)]
        if plan["max_sweeps"] >= 200000:
            windows.append((1000, 200000))
        for lower, upper in windows:
            mask = shared & (times >= lower) & (times <= upper)
            for reference, treatment in PAIRS:
                alpha, low, high, delta, delta_low, delta_high = paired_slopes(
                    times, arrays[treatment], arrays[reference], mask
                )
                fits.append({
                    "c": concentration, "L": 128, "n": len(group["replicas"]),
                    "reference": reference, "treatment": treatment,
                    "nominal_t_min": lower, "nominal_t_max": upper,
                    "retained_points": int(mask.sum()),
                    "used_t_min": int(times[mask][0]) if mask.any() else "",
                    "used_t_max": int(times[mask][-1]) if mask.any() else "",
                    "alpha_treatment": alpha, "alpha_low": low, "alpha_high": high,
                    "delta_alpha": delta, "delta_low": delta_low, "delta_high": delta_high,
                })
            # All five comparisons share the same time mask, so the two
            # sequential point-estimate deltas must add to the total shift.
            current = fits[-len(PAIRS):]
            if all(np.isfinite(row["delta_alpha"]) for row in current):
                if not np.isclose(current[0]["delta_alpha"] + current[1]["delta_alpha"],
                                  current[-1]["delta_alpha"], rtol=0, atol=1e-12):
                    raise ValueError("Binning/threshold decomposition did not add to total shift")

    output.mkdir(parents=True)
    write_csv(output / "per_snapshot.csv", rows)
    write_csv(output / "paired_fits.csv", fits)
    sources = Path(__file__).parent
    (output / "manifest.json").write_text(json.dumps({
        "status": "post-hoc exploratory after original observation study",
        "campaign_manifest_sha256": sha(folder / "manifest.json"),
        "original_observations_sha256": sha(previous_csv),
        "input_files": {path.name: sha(path) for path in files},
        "analysis_source_sha256": sha(Path(__file__)),
        "protocol_sha256": sha(sources / "BINNING_DECOMPOSITION_PROTOCOL.md"),
        "sources": {name: sha(sources / name) for name in ANALYSIS_SOURCES},
        "replicas": len(files), "earlier_length_values_rechecked": previous_checks,
        "pixel_spacing": "1 original site for full; 4 original sites for coarse fields",
        "uncertainty": "500 paired whole-replica bootstrap resamples, fixed shared resolved-time mask",
    }, indent=2) + "\n")
    return {"replicas": len(files), "previous_length_values_rechecked": previous_checks,
            "fit_rows": len(fits), "results": str(output / "paired_fits.csv")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("earlier_observations_csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyse(args.folder, args.earlier_observations_csv, args.output), indent=2))
