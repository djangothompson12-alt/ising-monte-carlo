"""Post-result paired audit of fitting-window sensitivity in the completed campaign.

The windows and original length/L filter match analyse_campaign.py. This audit
was designed after the original exponent table was seen, so it is not a new
prospective hypothesis test. Whole trajectories, not checkpoints, are the
bootstrap units. No running campaign data are read.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from research.analyse_campaign import fit_slope
from research.imaging_benchmark import sha


ROOT = Path(__file__).resolve().parents[1]
WINDOW_STARTS = (2, 100, 1000)
END = 200_000


def paired_window_fit(times: np.ndarray, trajectories: np.ndarray, width: int,
                      *, draws: int = 5000, seed: int = 91826) -> list[dict]:
    """Compare each earlier start with 1,000 sweeps on the same trajectories."""
    if trajectories.ndim != 2 or trajectories.shape[1] != len(times) or len(trajectories) < 2:
        raise ValueError("Need at least two complete trajectories with shared checkpoints")
    if width <= 0 or draws < 100:
        raise ValueError("Width must be positive and at least 100 draws are required")
    mean = np.mean(trajectories, axis=0)
    masks = {start: (times >= start) & (times <= END) & (mean / width < 0.15)
             for start in WINDOW_STARTS}
    late = fit_slope(times, mean, masks[1000])
    rng = np.random.default_rng(seed)
    indices = rng.integers(len(trajectories), size=(draws, len(trajectories)))
    results = []
    for early_start in (2, 100):
        early = fit_slope(times, mean, masks[early_start])
        differences = []
        for selection in indices:
            sample_mean = np.mean(trajectories[selection], axis=0)
            differences.append(fit_slope(times, sample_mean, masks[1000])
                               - fit_slope(times, sample_mean, masks[early_start]))
        differences = np.asarray(differences)
        finite = differences[np.isfinite(differences)]
        low, high = (np.percentile(finite, [2.5, 97.5]) if len(finite) >= .9 * draws
                     else (float("nan"), float("nan")))
        results.append(dict(early_start=early_start, late_start=1000,
            nominal_end=END, early_actual_start=int(times[masks[early_start]][0])
                if masks[early_start].any() else "",
            early_actual_end=int(times[masks[early_start]][-1])
                if masks[early_start].any() else "",
            late_actual_start=int(times[masks[1000]][0])
                if masks[1000].any() else "",
            late_actual_end=int(times[masks[1000]][-1])
                if masks[1000].any() else "",
            early_points=int(masks[early_start].sum()), late_points=int(masks[1000].sum()),
            early_alpha=early, late_alpha=late, delta_late_minus_early=late - early,
            delta_low=float(low), delta_high=float(high),
            valid_bootstrap_draws=int(len(finite)), total_bootstrap_draws=draws))
    return results


def run(folder: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory to preserve previous analyses")
    manifest = json.loads((folder / "manifest.json").read_text())
    plan = manifest["identity"]["plan"]
    if (plan["max_sweeps"] != END or plan["replicas"] != 8
            or plan["sizes"] != [32, 64, 96, 128]
            or plan["concentrations"] != [0.5, 0.15]
            or plan["Jx"] != 1 or plan["Jy"] != 1):
        raise ValueError("This post-result audit is only for the completed original campaign")
    status = json.loads((folder / "status.json").read_text())
    if status.get("state") != "complete" or status.get("completed") != 64:
        raise ValueError("The original 64-run campaign is not complete")
    rows = []
    hashes = {}
    for ci, composition in enumerate(plan["concentrations"]):
        paths = [folder / f"c{ci}_L128_rep{rep:03d}.npz" for rep in range(8)]
        trajectories = []
        times = None
        for path in paths:
            hashes[path.name] = sha(path)
            with np.load(path, allow_pickle=False) as archive:
                config = json.loads(archive["config"].item())
                expected_temperature = .65 * 2 / np.log(1 + np.sqrt(2))
                if (config["L"] != 128 or config["concentration"] != composition
                        or not np.isclose(config["T_final"], expected_temperature,
                                          rtol=0, atol=1e-12)):
                    raise ValueError(f"Unexpected run identity or quench temperature: {path.name}")
                checkpoint = np.asarray(archive["t"])
                if times is not None and not np.array_equal(checkpoint, times):
                    raise ValueError("Checkpoints differ within a group")
                times = checkpoint
                values = np.asarray(archive["lengths"])
                if values.shape != (len(times), 2):
                    raise ValueError(f"Unexpected directional length shape: {path.name}")
                trajectories.append(np.mean(values, axis=1))
        for result in paired_window_fit(times, np.asarray(trajectories), 128):
            rows.append(dict(composition=composition, L=128, n_replicas=8, **result))
    output.mkdir(parents=True)
    csv_path = output / "paired_window_differences.csv"
    with csv_path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    provenance = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status="post-result paired sensitivity analysis, not prospective confirmation",
        input_manifest_sha256=sha(folder / "manifest.json"),
        input_status_sha256=sha(folder / "status.json"),
        input_sha256=hashes,
        source_sha256={"research/paired_window_sensitivity.py": sha(Path(__file__)),
            "research/analyse_campaign.py": sha(ROOT / "research/analyse_campaign.py")},
        independent_units="eight complete seeded trajectories per composition",
        uncertainty="5000 paired whole-trajectory bootstrap draws; conditional on each fixed original fit mask")
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return csv_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.campaign, args.output))
