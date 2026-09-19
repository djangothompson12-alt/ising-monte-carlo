"""Paired conservation-aware image audit on the completed new-seed extension.

This measures archived snapshots only. It never advances or changes a lattice.
Read CONSERVATION_AWARE_HOLDOUT_PROTOCOL_2026-09-19.md before interpreting it.
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
from research.confirm_image_operator_extension import validate_complete
from research.imaging import block_average, image_length
from research.imaging_benchmark import sha


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = Path(__file__).with_name("CONSERVATION_AWARE_HOLDOUT_PROTOCOL_2026-09-19.md")
WINDOWS = ((1000, 20000), (1000, 200000))
OPERATORS = ("native", "integrated", "segmented")


def measure_snapshot(snapshot: np.ndarray) -> dict:
    """Return directional lengths and phase fractions for the fixed operators."""
    if snapshot.shape != (128, 128) or not np.all(np.isin(snapshot, (-1, 1))):
        raise ValueError("Expected one 128x128 saved +/-1 snapshot")
    integrated = block_average(snapshot, 4)
    segmented = np.where(integrated >= 0, 1.0, -1.0)
    native_fraction = float(np.mean(snapshot > 0))
    integrated_fraction = float((np.mean(integrated) + 1.0) / 2.0)
    if not np.isclose(integrated_fraction, native_fraction, rtol=0, atol=1e-15):
        raise ValueError("Linear block integration did not preserve phase fraction")
    fields = {
        "native": (snapshot, 1.0),
        "integrated": (integrated, 4.0),
        "segmented": (segmented, 4.0),
    }
    result = {name: image_length(field, spacing)
              for name, (field, spacing) in fields.items()}
    result["native_fraction"] = native_fraction
    result["integrated_fraction"] = integrated_fraction
    result["segmented_fraction"] = float(np.mean(segmented > 0))
    result["tie_fraction"] = float(np.mean(integrated == 0))
    return result


def shared_resolved(values: dict[str, np.ndarray]) -> np.ndarray:
    """Keep times where both axes resolve for every operator and trajectory."""
    arrays = [values[name] for name in OPERATORS]
    if any(array.ndim != 3 or array.shape[-1] != 2 for array in arrays):
        raise ValueError("Expected (replica, time, direction) arrays")
    if any(array.shape != arrays[0].shape for array in arrays[1:]):
        raise ValueError("Operator arrays are not paired")
    stacked = np.stack(arrays)
    return np.all(np.isfinite(stacked) & (stacked > 0), axis=(0, 1, 3))


def _prior_holdout(path: Path) -> dict[tuple[str, int], dict[str, tuple[float, float]]]:
    rows = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            rows[(row["file"], int(row["sweep"]))] = {
                "native": (float(row["native_x"]), float(row["native_y"])),
                "segmented": (float(row["binned_x"]), float(row["binned_y"])),
            }
    return rows


def _same_or_nan(left: float, right: float) -> bool:
    return bool((np.isnan(left) and np.isnan(right))
                or np.isclose(left, right, rtol=0, atol=1e-12))


def directional_verdict(fits: list[dict]) -> str:
    selected = [row for row in fits
                if row["comparison"] == "segmented-minus-integrated"
                and row["nominal_t_min"] == WINDOWS[0][0]
                and row["nominal_t_max"] == WINDOWS[0][1]]
    if len(selected) != 2 or any(not np.isfinite(row["delta_alpha"]) for row in selected):
        return "Primary directional repeat unresolved."
    if all(row["delta_alpha"] < 0 for row in selected):
        return ("The segmentation-stage point estimate was negative at both compositions, "
                "consistent in direction with the earlier selected effect; this is not a blind discovery.")
    return ("The predeclared directional repeat failed: at least one composition had a "
            "non-negative segmentation-stage point estimate.")


def _report(fits: list[dict], fraction_rows: list[dict]) -> str:
    lines = [
        "# Conservation-aware observation audit", "",
        "This is a transparent new-seed mechanism audit designed after the broad image effect was known.",
        "It separates mean-preserving pixel integration from composition-changing binary segmentation.",
        "It is not a microscope calibration, an alloy validation, a new growth law or a blind novelty claim.",
        "", directional_verdict(fits), "",
        "| c | Window | Comparison | Reference alpha | Treatment alpha | Delta alpha [95% interval] | Crosses zero? | Points | Actual range |",
        "|---:|---|---|---:|---:|---|---|---:|---|",
    ]
    for row in fits:
        crosses = (row["delta_low"] <= 0 <= row["delta_high"]
                   if np.all(np.isfinite([row["delta_low"], row["delta_high"]])) else None)
        lines.append(
            f"| {row['composition']:.2f} | {row['nominal_t_min']}-{row['nominal_t_max']} | "
            f"{row['comparison']} | {row['reference_alpha']:.3f} | "
            f"{row['treatment_alpha']:.3f} | {row['delta_alpha']:.3f} "
            f"[{row['delta_low']:.3f}, {row['delta_high']:.3f}] | "
            f"{'yes' if crosses else 'no' if crosses is not None else 'unresolved'} | "
            f"{row['retained_points']} | {row['actual_t_min']}-{row['actual_t_max']} |")
    lines.extend(["", "## Apparent conservation check", "",
                  "The integrated partial-volume field preserved the native fraction at every checkpoint.",
                  "The binary segmentation did not have that guarantee:", "",
                  "| c | Mean native +1 fraction | Mean integrated equivalent | Mean segmented +1 fraction | Mean segmented shift | Mean exact-tie fraction |",
                  "|---:|---:|---:|---:|---:|---:|"])
    for row in fraction_rows:
        lines.append(f"| {row['composition']:.2f} | {row['mean_native_fraction']:.6f} | "
                     f"{row['mean_integrated_fraction']:.6f} | {row['mean_segmented_fraction']:.6f} | "
                     f"{row['mean_segmented_shift']:+.6f} | {row['mean_tie_fraction']:.6f} |")
    lines.extend(["", "All uncertainty intervals resample complete paired trajectories. The common resolved-time mask",
                  "is stricter than a separate fit for each operator, so the alphas here need not match other tables.",
                  "The broad observation that image processing affects measured kinetics predates this project."])
    return "\n".join(lines) + "\n"


def analyse(campaign: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory; previous results are immutable")
    plan = validate_complete(campaign)
    earlier_path = campaign / "image_holdout_v1" / "per_replica_checkpoint.csv"
    earlier = _prior_holdout(earlier_path)
    observations: list[dict] = []
    groups: dict[float, dict] = {}
    hashes = {}
    checked = 0
    for ci, composition in enumerate(plan["concentrations"]):
        group = {"times": None, "operators": {name: [] for name in OPERATORS},
                 "fractions": []}
        for replica in range(16):
            path = campaign / f"c{ci}_L128_rep{replica:03d}.npz"
            hashes[path.name] = sha(path)
            with np.load(path, allow_pickle=False) as archive:
                config = json.loads(archive["config"].item())
                times = np.asarray(archive["t"])
                snapshots = np.asarray(archive["snapshots"])
                if (config["concentration"] != composition or config["L"] != 128
                        or snapshots.shape != (len(times), 128, 128)
                        or np.any(snapshots.sum(axis=(1, 2)) != int(archive["magnetization"]))):
                    raise ValueError(f"Malformed or non-conserving replica: {path.name}")
                if group["times"] is None:
                    group["times"] = times.copy()
                elif not np.array_equal(group["times"], times):
                    raise ValueError("Checkpoint grids differ within a composition")
                trajectories = {name: [] for name in OPERATORS}
                for sweep, snapshot in zip(times, snapshots):
                    measured = measure_snapshot(snapshot)
                    previous = earlier[(path.name, int(sweep))]
                    native_now = (measured["native"]["length_x"], measured["native"]["length_y"])
                    segmented_now = (measured["segmented"]["length_x"], measured["segmented"]["length_y"])
                    if not all(_same_or_nan(a, b) for a, b in zip(native_now, previous["native"])):
                        raise ValueError(f"Native remeasurement differs from fixed holdout: {path.name}, {sweep}")
                    if not all(_same_or_nan(a, b) for a, b in zip(segmented_now, previous["segmented"])):
                        raise ValueError(f"Segmented remeasurement differs from fixed holdout: {path.name}, {sweep}")
                    checked += 4
                    for name in OPERATORS:
                        trajectories[name].append((measured[name]["length_x"], measured[name]["length_y"]))
                    fractions = dict(native=measured["native_fraction"],
                                     integrated=measured["integrated_fraction"],
                                     segmented=measured["segmented_fraction"],
                                     tie=measured["tie_fraction"])
                    group["fractions"].append(fractions)
                    observations.append(dict(
                        file=path.name, seed=config["seed"], composition=composition,
                        sweep=int(sweep),
                        native_x=native_now[0], native_y=native_now[1],
                        integrated_x=measured["integrated"]["length_x"],
                        integrated_y=measured["integrated"]["length_y"],
                        segmented_x=measured["segmented"]["length_x"],
                        segmented_y=measured["segmented"]["length_y"],
                        native_fraction=fractions["native"],
                        integrated_fraction=fractions["integrated"],
                        segmented_fraction=fractions["segmented"],
                        segmented_fraction_shift=fractions["segmented"] - fractions["native"],
                        exact_tie_fraction=fractions["tie"]))
                for name in OPERATORS:
                    group["operators"][name].append(trajectories[name])
        groups[float(composition)] = group

    fits: list[dict] = []
    fraction_rows: list[dict] = []
    for composition, group in groups.items():
        times = group["times"]
        directional = {name: np.asarray(values) for name, values in group["operators"].items()}
        lengths = {name: values.mean(axis=2) for name, values in directional.items()}
        common = shared_resolved(directional)
        fraction_rows.append(dict(
            composition=composition,
            mean_native_fraction=float(np.mean([row["native"] for row in group["fractions"]])),
            mean_integrated_fraction=float(np.mean([row["integrated"] for row in group["fractions"]])),
            mean_segmented_fraction=float(np.mean([row["segmented"] for row in group["fractions"]])),
            mean_segmented_shift=float(np.mean([row["segmented"] - row["native"] for row in group["fractions"]])),
            mean_tie_fraction=float(np.mean([row["tie"] for row in group["fractions"]]))))
        for lower, upper in WINDOWS:
            mask = common & (times >= lower) & (times <= upper)
            native_alpha = bootstrap_slope(times, lengths["native"], mask, seed=912, draws=500)[0]
            comparisons = (("integrated-minus-native", "native", "integrated"),
                           ("segmented-minus-integrated", "integrated", "segmented"),
                           ("segmented-minus-native", "native", "segmented"))
            for label, reference, treatment in comparisons:
                alpha, low, high, delta, delta_low, delta_high = paired_slopes(
                    times, lengths[treatment], lengths[reference], mask, draws=500)
                reference_alpha = (native_alpha if reference == "native" else
                                   bootstrap_slope(times, lengths[reference], mask, seed=912, draws=500)[0])
                fits.append(dict(
                    composition=composition, n_replicas=16, comparison=label,
                    reference=reference, treatment=treatment,
                    nominal_t_min=lower, nominal_t_max=upper,
                    actual_t_min=int(times[mask][0]) if mask.any() else "",
                    actual_t_max=int(times[mask][-1]) if mask.any() else "",
                    retained_points=int(mask.sum()), reference_alpha=reference_alpha,
                    treatment_alpha=alpha, treatment_low=low, treatment_high=high,
                    delta_alpha=delta, delta_low=delta_low, delta_high=delta_high,
                    unresolved_native=int(np.count_nonzero(~np.isfinite(directional["native"]))),
                    unresolved_integrated=int(np.count_nonzero(~np.isfinite(directional["integrated"]))),
                    unresolved_segmented=int(np.count_nonzero(~np.isfinite(directional["segmented"])))))

    output.mkdir(parents=True)
    for name, rows in (("per_checkpoint.csv", observations),
                       ("paired_fits.csv", fits),
                       ("phase_fraction_summary.csv", fraction_rows)):
        with (output / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    sources = [Path(__file__), PROTOCOL, ROOT / "research/imaging.py",
               ROOT / "research/compare_estimators.py", ROOT / "research/analyse_campaign.py"]
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        status="new-seed mechanism audit designed after the image effect was known",
        campaign_manifest_sha256=sha(campaign / "manifest.json"),
        previous_holdout_csv_sha256=sha(earlier_path),
        input_sha256=hashes, source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources},
        windows=WINDOWS, bootstrap_draws=500, independent_units="seeded full trajectories",
        earlier_directional_values_rechecked=checked), indent=2) + "\n")
    (output / "REPORT.md").write_text(_report(fits, fraction_rows))

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), layout="constrained")
    colors = {0.5: "#1b6d7a", 0.15: "#a05b28"}
    primary = [row for row in fits if row["nominal_t_max"] == 20000]
    labels = ["integration - native", "segmentation - integration", "segmentation - native"]
    for ci, composition in enumerate((0.5, 0.15)):
        selected = [row for row in primary if row["composition"] == composition]
        for index, row in enumerate(selected):
            axes[ci].hlines(index, row["delta_low"], row["delta_high"], color=colors[composition], lw=2)
            axes[ci].plot(row["delta_alpha"], index, "o", color=colors[composition])
        axes[ci].axvline(0, color="#333333", ls=":")
        axes[ci].set_yticks(range(3), labels)
        axes[ci].set_title(f"c={composition:.2f}; 1,000-20,000 sweeps")
        axes[ci].set_xlabel("paired effective-exponent difference")
        axes[ci].grid(axis="x", alpha=0.2)
    fig.suptitle("Conservation-aware image pipeline audit (16 paired trajectories)")
    fig.savefig(output / "conservation_aware_deltas.png", dpi=180)
    plt.close(fig)
    return output / "REPORT.md"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(analyse(arguments.campaign, arguments.output))
