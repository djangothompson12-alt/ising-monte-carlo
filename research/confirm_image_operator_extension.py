"""Run the fixed 4x image-operator holdout only after 128/128 extension runs.

See PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md. This does not change the dynamics.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from research.analyse_campaign import bootstrap_slope
from research.compare_estimators import paired_slopes
from research.imaging import image_length, observe
from research.imaging_benchmark import sha
from research.verify_study import verify


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = Path(__file__).with_name("PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md")
WINDOWS = ((1000, 20000), (1000, 200000))


def validate_complete(folder: Path) -> dict:
    manifest = json.loads((folder / "manifest.json").read_text())
    plan = manifest["identity"]["plan"]
    required = dict(sizes=[32, 64, 96, 128], concentrations=[0.5, 0.15],
                    replicas=16, max_sweeps=1_000_000, Jx=1.0, Jy=1.0,
                    T_final_over_tc=0.65)
    if any(plan.get(key) != value for key, value in required.items()):
        raise ValueError("Campaign does not match the fixed holdout protocol")
    status = json.loads((folder / "status.json").read_text())
    if status.get("state") != "complete" or status.get("completed") != 128 or status.get("total") != 128:
        raise ValueError("Holdout is forbidden until the entire 128/128 campaign completes")
    actual = {p.name for p in folder.glob("*.npz")}
    expected = {f"c{ci}_L{L}_rep{rep:03d}.npz"
                for ci in range(2) for L in required["sizes"] for rep in range(16)}
    if actual != expected:
        raise ValueError("Missing or unexpected raw campaign files")
    return plan


def seed_set(folder: Path) -> set[int]:
    seeds = set()
    for path in folder.glob("*.npz"):
        with np.load(path, allow_pickle=False) as archive:
            seeds.add(int(json.loads(archive["config"].item())["seed"]))
    return seeds


def measure_snapshot(snapshot: np.ndarray) -> tuple[dict, dict, float, float]:
    if snapshot.shape != (128, 128) or not np.all(np.isin(snapshot, (-1, 1))):
        raise ValueError("Holdout expects a 128×128 ±1 saved snapshot")
    native = image_length(snapshot, 1.0)
    binned_image = observe(snapshot, factor=4, threshold=0.0)
    binned = image_length(binned_image, 4.0)
    return native, binned, float(np.mean(snapshot == 1)), float(np.mean(binned_image == 1))


def shared_resolved(native: np.ndarray, binned: np.ndarray) -> np.ndarray:
    """Keep a checkpoint only if both directions resolve in every replica."""
    if native.shape != binned.shape or native.ndim != 3 or native.shape[-1] != 2:
        raise ValueError("Need paired (replica, time, direction) observations")
    return np.all(np.isfinite(native) & (native > 0)
                  & np.isfinite(binned) & (binned > 0), axis=(0, 2))


def primary_directional_verdict(fits: list[dict]) -> str:
    """Apply the protocol's two-composition primary-window sign rule only."""
    primary = {float(row["composition"]): row for row in fits
               if (int(row["nominal_t_min"]), int(row["nominal_t_max"])) == WINDOWS[0]}
    if set(primary) != {0.5, 0.15}:
        raise ValueError("Need both fixed primary-window composition rows")
    if any(primary[c]["status"] != "fit resolved"
           or not np.isfinite(float(primary[c]["delta_alpha"])) for c in primary):
        return "Primary directional repetition unresolved: at least one fixed-window fit could not be identified."
    if all(float(primary[c]["delta_alpha"]) < 0 for c in primary):
        return ("Primary point estimates are negative at both compositions: "
                "consistent in direction with the earlier selected effect, not blind confirmation.")
    return ("Directional repetition failed by the predeclared primary rule: "
            "at least one composition has a non-negative point estimate.")


def render_report(fits: list[dict]) -> str:
    """Print every fixed holdout row and the protocol's primary sign verdict."""
    report = ["# Fixed image-operator holdout", "",
        "Read the protocol and paired_fits.csv before interpreting this figure.",
        "This was specified after an earlier observed effect; new seeds test directional repetition, not novelty or a physical growth law.",
        "All 128 dynamics trajectories were complete before any extension image was measured here.",
        "The bootstrap resamples whole paired trajectories. It does not include fitting-window or model uncertainty.",
        "", primary_directional_verdict(fits),
        "This sign rule uses the two 1,000–20,000-sweep point estimates only. "
        "A percentile interval crossing zero is reported as such, and the secondary window cannot rescue a failed primary test.",
        "", "| Composition | Nominal window | Actual window | Points | Native α | Binned α | Δα [95% interval] | Interval crosses zero? | Native +1 fraction | Binned +1 fraction | Fraction shift | Status |",
        "|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---|"]
    for row in fits:
        crosses_zero = (row["delta_low"] <= 0 <= row["delta_high"]
                        if np.all(np.isfinite([row["delta_low"], row["delta_high"]])) else None)
        report.append(f"| {row['composition']} | {row['nominal_t_min']}–{row['nominal_t_max']} | "
                      f"{row['actual_t_min']}–{row['actual_t_max']} | {row['retained_points']} | "
                      f"{row['native_alpha']:.3f} | {row['binned_alpha']:.3f} | "
                      f"{row['delta_alpha']:.3f} [{row['delta_low']:.3f}, {row['delta_high']:.3f}] | "
                      f"{'yes' if crosses_zero else 'no' if crosses_zero is not None else 'unresolved'} | "
                      f"{row['mean_native_fraction']:.4f} | {row['mean_binned_fraction']:.4f} | "
                      f"{row['mean_binned_fraction']-row['mean_native_fraction']:+.4f} | "
                      f"{row['status']} |")
    report.extend(("", "Unresolved directional length values across every saved checkpoint "
                   "are retained in per_replica_checkpoint.csv; the counts in paired_fits.csv "
                   "are over the full trajectory, not just one fit window. "
                   "Fraction means above use each row's fixed shared-resolved time mask.",
                   "The tie-to-+1 threshold may change apparent composition; no physical "
                   "phase fraction or microscope correction is inferred."))
    return "\n".join(report) + "\n"


def analyse(folder: Path, output: Path, prior_folders: tuple[Path, Path]) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory; preserve previous results")
    plan = validate_complete(folder)
    audit = verify(folder)
    if audit["replicas"] != 128 or audit["unique_seeds"] != 128:
        raise ValueError("Raw campaign integrity audit did not pass")
    prior_seeds = set()
    for prior in prior_folders:
        prior_seeds.update(seed_set(prior))
    new_seeds = seed_set(folder)
    if new_seeds & prior_seeds:
        raise ValueError("New campaign shares random seeds with an earlier ensemble")

    observations: list[dict] = []
    groups = {}
    input_hashes = {}
    for ci, composition in enumerate(plan["concentrations"]):
        times = None
        native_replicas, binned_replicas = [], []
        phase_native, phase_binned = [], []
        for replica in range(16):
            path = folder / f"c{ci}_L128_rep{replica:03d}.npz"
            input_hashes[path.name] = sha(path)
            with np.load(path, allow_pickle=False) as archive:
                config = json.loads(archive["config"].item())
                t = np.asarray(archive["t"])
                snapshots = np.asarray(archive["snapshots"])
                if (config["L"] != 128 or config["concentration"] != composition
                        or len(t) != len(snapshots) or int(t[-1]) != 1_000_000
                        or np.any(snapshots.sum(axis=(1, 2)) != int(archive["magnetization"]))):
                    raise ValueError(f"Malformed or non-conserving holdout replica: {path.name}")
                if times is not None and not np.array_equal(t, times):
                    raise ValueError("Checkpoints differ within a holdout group")
                times = t
                native_directional, binned_directional = [], []
                native_fractions, binned_fractions = [], []
                for sweep, snapshot in zip(t, snapshots):
                    native, binned, native_fraction, binned_fraction = measure_snapshot(snapshot)
                    native_directional.append((native["length_x"], native["length_y"]))
                    binned_directional.append((binned["length_x"], binned["length_y"]))
                    native_fractions.append(native_fraction)
                    binned_fractions.append(binned_fraction)
                    observations.append(dict(file=path.name, seed=config["seed"],
                        composition=composition, L=128, sweep=int(sweep),
                        native_x=native["length_x"], native_y=native["length_y"],
                        native_length=native["length"],
                        binned_x=binned["length_x"], binned_y=binned["length_y"],
                        binned_length=binned["length"],
                        native_phase_fraction=native_fraction,
                        binned_phase_fraction=binned_fraction))
            native_replicas.append(native_directional)
            binned_replicas.append(binned_directional)
            phase_native.append(native_fractions)
            phase_binned.append(binned_fractions)
        groups[composition] = (np.asarray(times), np.asarray(native_replicas),
                               np.asarray(binned_replicas), np.asarray(phase_native),
                               np.asarray(phase_binned))

    fits = []
    for composition, (times, native, binned, fraction_native, fraction_binned) in groups.items():
        resolved = shared_resolved(native, binned)
        native_lengths = native.mean(axis=2)
        binned_lengths = binned.mean(axis=2)
        for lower, upper in WINDOWS:
            mask = resolved & (times >= lower) & (times <= upper)
            n_alpha, n_low, n_high = bootstrap_slope(times, native_lengths, mask, seed=912, draws=500)
            b_alpha, b_low, b_high, delta, d_low, d_high = paired_slopes(
                times, binned_lengths, native_lengths, mask, draws=500)
            fits.append(dict(composition=composition, n_replicas=16,
                nominal_t_min=lower, nominal_t_max=upper,
                actual_t_min=int(times[mask][0]) if mask.any() else "",
                actual_t_max=int(times[mask][-1]) if mask.any() else "",
                retained_points=int(mask.sum()),
                unresolved_native_values=int(np.count_nonzero(~np.isfinite(native))),
                unresolved_binned_values=int(np.count_nonzero(~np.isfinite(binned))),
                native_alpha=n_alpha, native_low=n_low, native_high=n_high,
                binned_alpha=b_alpha, binned_low=b_low, binned_high=b_high,
                delta_alpha=delta, delta_low=d_low, delta_high=d_high,
                mean_native_fraction=float(fraction_native[:, mask].mean()) if mask.any() else float("nan"),
                mean_binned_fraction=float(fraction_binned[:, mask].mean()) if mask.any() else float("nan"),
                status="fit resolved" if np.all(np.isfinite([n_alpha, b_alpha, delta])) else "fit unresolved"))

    output.mkdir(parents=True)
    for name, rows in (("per_replica_checkpoint.csv", observations), ("paired_fits.csv", fits)):
        with (output / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    source_paths = [Path(__file__), PROTOCOL, ROOT / "research/imaging.py",
                    ROOT / "research/compare_estimators.py", ROOT / "research/analyse_campaign.py",
                    ROOT / "research/verify_study.py"]
    provenance = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status="complete-campaign new-seed image-operator holdout, not blind first discovery",
        campaign_manifest_sha256=sha(folder / "manifest.json"),
        campaign_status_sha256=sha(folder / "status.json"),
        input_sha256=input_hashes,
        prior_manifest_sha256={str(path): sha(path / "manifest.json") for path in prior_folders},
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in source_paths},
        windows=WINDOWS, independent_units="seeded full trajectories", bootstrap_draws=500,
        full_campaign_audit=audit)
    (output / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n")
    fig, axis = plt.subplots(figsize=(7.2, 4.5), layout="constrained")
    for index, composition in enumerate((0.5, 0.15)):
        selected = [row for row in fits if row["composition"] == composition]
        for window_index, row in enumerate(selected):
            y = index * 2.5 + window_index
            if np.all(np.isfinite([row["delta_alpha"], row["delta_low"], row["delta_high"]])):
                color = "#1b6d7a" if index == 0 else "#a05b28"
                # Percentile intervals need not contain the original point
                # estimate; draw both faithfully instead of assuming a
                # non-negative errorbar distance on each side.
                axis.hlines(y, row["delta_low"], row["delta_high"], color=color, lw=2)
                axis.plot(row["delta_alpha"], y, "o", color=color)
    axis.axvline(0, ls=":", color="#333333")
    axis.set_yticks([0, 1, 2.5, 3.5],
                   ["50:50, 1k–20k", "50:50, 1k–200k",
                    "15:85, 1k–20k", "15:85, 1k–200k"])
    axis.set_xlabel("4× bin + threshold minus native image exponent")
    axis.set_title("New-seed holdout; whole-trajectory bootstrap")
    axis.grid(axis="x", alpha=0.2)
    fig.savefig(output / "holdout_delta_alpha.png", dpi=180)
    plt.close(fig)
    (output / "REPORT.md").write_text(render_report(fits))
    return output / "paired_fits.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-main", type=Path, default=ROOT / "research/runs/overnight")
    parser.add_argument("--prior-repeat", type=Path, default=ROOT / "research/runs/imaging_validation")
    args = parser.parse_args()
    print(analyse(args.campaign, args.output, (args.prior_main, args.prior_repeat)))
