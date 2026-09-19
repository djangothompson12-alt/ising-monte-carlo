"""Post-result, four-observable robustness audit of the completed extension.

The frozen protocol is FULL_EXTENSION_OBSERVABLE_ROBUSTNESS_PROTOCOL_2026-09-19.md.
This does not choose a uniquely correct domain radius or test a real alloy.
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
from research.metrology import snapshot_measures


MEASURES = ("threshold_05", "positive_lobe", "spectral_moment",
            "inverse_interface_proxy")
WINDOWS = ((1_000, 20_000), (1_000, 200_000), (20_000, 200_000),
           (20_000, 1_000_000), (200_000, 1_000_000))
MATCHED_TIMES = (207_231, 1_000_000)
DRAWS = 2_000
PROTOCOL = Path(__file__).with_name(
    "FULL_EXTENSION_OBSERVABLE_ROBUSTNESS_PROTOCOL_2026-09-19.md")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def common_resolved_mask(values: np.ndarray) -> np.ndarray:
    """Require all replicas and all estimators at a checkpoint."""
    if values.ndim != 3 or values.shape[2] != len(MEASURES):
        raise ValueError("Expected replica x checkpoint x estimator values")
    return np.all(np.isfinite(values) & (values > 0), axis=(0, 2))


def paired_fits(times: np.ndarray, values: np.ndarray, mask: np.ndarray,
                *, seed: int, draws: int = DRAWS) -> list[dict]:
    """Fit every estimator with paired whole-trajectory bootstrap draws."""
    if (values.ndim != 3 or values.shape[1] != len(times)
            or values.shape[2] != len(MEASURES) or len(values) < 2
            or mask.shape != times.shape or draws < 1):
        raise ValueError("Malformed paired-fit inputs")
    estimates = np.asarray([
        fit_slope(times, values[:, :, j].mean(axis=0), mask)
        for j in range(len(MEASURES))
    ])
    rng = np.random.default_rng(seed)
    sampled = np.empty((draws, len(MEASURES)), dtype=float)
    for draw in range(draws):
        indices = rng.integers(len(values), size=len(values))
        means = values[indices].mean(axis=0)
        sampled[draw] = [fit_slope(times, means[:, j], mask)
                         for j in range(len(MEASURES))]
    rows = []
    for j, measure in enumerate(MEASURES):
        valid = np.isfinite(sampled[:, j])
        difference = sampled[:, j] - sampled[:, 0]
        valid_difference = np.isfinite(difference)
        low, high = (np.percentile(sampled[valid, j], [2.5, 97.5])
                     if valid.sum() >= .9 * draws else (np.nan, np.nan))
        delta_low, delta_high = (
            np.percentile(difference[valid_difference], [2.5, 97.5])
            if valid_difference.sum() >= .9 * draws else (np.nan, np.nan))
        rows.append(dict(
            estimator=measure, alpha=float(estimates[j]),
            bootstrap_low=float(low), bootstrap_high=float(high),
            delta_vs_threshold=float(estimates[j] - estimates[0]),
            delta_low=float(delta_low), delta_high=float(delta_high),
        ))
    return rows


def matched_ratio(smaller: np.ndarray, reference: np.ndarray, *, seed: int,
                  draws: int = DRAWS) -> list[dict]:
    """Compare estimator means at one time, resampling sizes independently."""
    if (smaller.ndim != 2 or reference.ndim != 2
            or smaller.shape[1] != len(MEASURES)
            or reference.shape[1] != len(MEASURES)
            or min(len(smaller), len(reference)) < 2 or draws < 1):
        raise ValueError("Malformed matched-ratio inputs")
    rng = np.random.default_rng(seed)
    small_indices = rng.integers(len(smaller), size=(draws, len(smaller)))
    ref_indices = rng.integers(len(reference), size=(draws, len(reference)))
    rows = []
    for j, measure in enumerate(MEASURES):
        resolved = bool(np.all(np.isfinite(smaller[:, j]) & (smaller[:, j] > 0))
                        and np.all(np.isfinite(reference[:, j]) & (reference[:, j] > 0)))
        if resolved:
            ratio = float(smaller[:, j].mean() / reference[:, j].mean())
            draws_ratio = (smaller[small_indices, j].mean(axis=1)
                           / reference[ref_indices, j].mean(axis=1))
            low, high = np.percentile(draws_ratio, [2.5, 97.5])
        else:
            ratio = low = high = float("nan")
        rows.append(dict(estimator=measure, ratio=ratio,
                         ratio_low=float(low), ratio_high=float(high),
                         status="resolved" if resolved else "unresolved"))
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _format(value: float) -> str:
    return f"{value:.3f}" if np.isfinite(value) else "unresolved"


def analyse(folder: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory")
    manifest_path = folder / "manifest.json"
    status_path = folder / "status.json"
    manifest = json.loads(manifest_path.read_text())
    status = json.loads(status_path.read_text())
    plan = manifest["identity"]["plan"]
    if (plan["sizes"] != [32, 64, 96, 128]
            or plan["concentrations"] != [0.5, 0.15]
            or plan["replicas"] != 16 or plan["max_sweeps"] != 1_000_000
            or plan["T_final_over_tc"] != 0.65
            or status.get("state") != "complete" or status.get("completed") != 128):
        raise ValueError("Input is not the complete frozen 0.65 Tc extension")
    expected = {f"c{ci}_L{L}_rep{rep:03d}.npz"
                for ci in range(2) for L in plan["sizes"]
                for rep in range(plan["replicas"])}
    present = {path.name for path in folder.glob("*.npz")}
    if present != expected:
        raise ValueError("Raw-file inventory is incomplete or unexpected")

    groups: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}
    raw_rows: list[dict] = []
    hashes: dict[str, str] = {}
    for ci, composition in enumerate(plan["concentrations"]):
        for L in plan["sizes"]:
            replicas = []
            reference_time = None
            for replica in range(plan["replicas"]):
                path = folder / f"c{ci}_L{L}_rep{replica:03d}.npz"
                hashes[path.name] = sha(path)
                with np.load(path, allow_pickle=False) as data:
                    times = np.asarray(data["t"], dtype=int)
                    snapshots = np.asarray(data["snapshots"], dtype=np.int8)
                    correlations = np.asarray(data["correlations"], dtype=float)
                    lengths = np.asarray(data["lengths"], dtype=float)
                    magnetisation = int(data["magnetization"])
                if (snapshots.shape != (len(times), L, L)
                        or correlations.shape[:2] != (len(times), 2)
                        or lengths.shape != (len(times), 2)
                        or times[-1] != plan["max_sweeps"]):
                    raise ValueError(f"Malformed trajectory: {path.name}")
                sums = snapshots.sum(axis=(1, 2))
                if not np.all(sums == magnetisation):
                    raise ValueError(f"Composition conservation failed: {path.name}")
                if reference_time is None:
                    reference_time = times
                elif not np.array_equal(times, reference_time):
                    raise ValueError(f"Checkpoint mismatch: {path.name}")
                measured = [snapshot_measures(snapshot, correlation)
                            for snapshot, correlation in zip(snapshots, correlations)]
                values = np.asarray([[item[name] for name in MEASURES]
                                     for item in measured], dtype=float)
                np.testing.assert_allclose(values[:, 0], lengths.mean(axis=1),
                                           atol=1e-12, equal_nan=True)
                replicas.append(values)
                for sweep, item in zip(times, measured):
                    raw_rows.append(dict(file=path.name, composition=composition,
                                         L=L, replica=replica, sweep=int(sweep), **item))
            groups[(ci, L)] = (reference_time, np.asarray(replicas))

    fit_rows: list[dict] = []
    for ci, composition in enumerate(plan["concentrations"]):
        for L in plan["sizes"]:
            times, values = groups[(ci, L)]
            resolved = common_resolved_mask(values)
            for window_index, (lower, upper) in enumerate(WINDOWS):
                mask = resolved & (times >= lower) & (times <= upper)
                fits = paired_fits(times, values, mask,
                                   seed=20260919 + ci * 1000 + L * 10 + window_index)
                for row in fits:
                    row.update(composition=composition, L=L,
                               nominal_t_min=lower, nominal_t_max=upper,
                               used_t_min=int(times[mask][0]) if mask.any() else "",
                               used_t_max=int(times[mask][-1]) if mask.any() else "",
                               n_points=int(mask.sum()), n_replicas=len(values),
                               unresolved_values=int(np.count_nonzero(
                                   ~np.isfinite(values[:, :, MEASURES.index(row["estimator"])]))))
                    fit_rows.append(row)

    ratio_rows: list[dict] = []
    for ci, composition in enumerate(plan["concentrations"]):
        reference_times, reference_values = groups[(ci, 128)]
        for L in (32, 64, 96):
            times, values = groups[(ci, L)]
            if not np.array_equal(times, reference_times):
                raise ValueError("Matched-size groups have different checkpoints")
            for target in MATCHED_TIMES:
                matches = np.flatnonzero(times == target)
                if len(matches) != 1:
                    raise ValueError(f"Missing exact matched checkpoint {target}")
                index = int(matches[0])
                rows = matched_ratio(values[:, index, :], reference_values[:, index, :],
                                     seed=20260919 + ci * 1000 + L + index)
                for row in rows:
                    row.update(composition=composition, L=L, reference_L=128,
                               sweep=target, n_small=len(values),
                               n_reference=len(reference_values))
                    ratio_rows.append(row)

    output.mkdir(parents=True)
    _write_csv(output / "per_checkpoint.csv", raw_rows)
    _write_csv(output / "paired_fits.csv", fit_rows)
    _write_csv(output / "matched_size_ratios.csv", ratio_rows)

    for ci, composition in enumerate(plan["concentrations"]):
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), layout="constrained")
        for estimator in MEASURES:
            early = [row for row in fit_rows if row["composition"] == composition
                     and row["estimator"] == estimator
                     and row["nominal_t_min"] == 1_000
                     and row["nominal_t_max"] == 200_000]
            broad = [row for row in fit_rows if row["composition"] == composition
                     and row["estimator"] == estimator
                     and row["nominal_t_min"] == 20_000
                     and row["nominal_t_max"] == 1_000_000]
            late_ratios = [row for row in ratio_rows
                           if row["composition"] == composition
                           and row["estimator"] == estimator
                           and row["sweep"] == 1_000_000]
            axes[0].plot([row["L"] for row in early], [row["alpha"] for row in early],
                         "o-", label=estimator)
            axes[1].plot([row["L"] for row in broad], [row["alpha"] for row in broad],
                         "o-", label=estimator)
            axes[2].plot([row["L"] for row in late_ratios],
                         [row["ratio"] for row in late_ratios], "o-", label=estimator)
        for axis, title in zip(axes, ("1,000–200,000-sweep slopes",
                                      "20,000–1,000,000-sweep slopes",
                                      "Length ratio to L=128 at 1,000,000 sweeps")):
            axis.set(xlabel="Lattice size L", title=title)
            axis.grid(alpha=.2)
        axes[0].set_ylabel("Effective exponent")
        axes[1].set_ylabel("Effective exponent")
        axes[2].set_ylabel("Matched-time ratio")
        axes[0].axhline(1 / 3, color="black", ls=":", label="1/3 guide")
        axes[1].axhline(1 / 3, color="black", ls=":", label="1/3 guide")
        axes[2].axhline(1, color="black", ls=":", label="equal to L=128")
        axes[0].legend(fontsize=7)
        fig.suptitle(f"Post-result observable robustness audit, c={composition}")
        fig.savefig(output / f"observable_robustness_c{ci}.png", dpi=180)
        plt.close(fig)

    report = [
        "# Full-extension observable robustness audit", "",
        "This is a post-result robustness audit under the frozen protocol, not a blind discovery test.",
        "Every within-group fit uses one common checkpoint mask across all four observables and all 16 trajectories.",
        "The estimators are different morphology proxies, not four calibrated measurements of one true radius.",
        "", "## All paired fit rows", "",
        "| c | L | estimator | nominal window | actual window | points | alpha [95%] | delta from half-height [95%] | unresolved values |",
        "|---:|---:|---|---|---|---:|---|---|---:|",
    ]
    for row in fit_rows:
        actual = (f'{row["used_t_min"]}–{row["used_t_max"]}'
                  if row["used_t_min"] != "" else "unresolved")
        report.append(
            f'| {row["composition"]} | {row["L"]} | {row["estimator"]} | '
            f'{row["nominal_t_min"]}–{row["nominal_t_max"]} | {actual} | '
            f'{row["n_points"]} | {_format(row["alpha"])} '
            f'[{_format(row["bootstrap_low"])}, {_format(row["bootstrap_high"])}] | '
            f'{_format(row["delta_vs_threshold"])} '
            f'[{_format(row["delta_low"])}, {_format(row["delta_high"])}] | '
            f'{row["unresolved_values"]} |')
    report += ["", "## All matched-size rows", "",
               "| c | sweep | L/128 | estimator | ratio [95%] | status |",
               "|---:|---:|---:|---|---|---|"]
    for row in ratio_rows:
        report.append(
            f'| {row["composition"]} | {row["sweep"]} | {row["L"]}/128 | '
            f'{row["estimator"]} | {_format(row["ratio"])} '
            f'[{_format(row["ratio_low"])}, {_format(row["ratio_high"])}] | '
            f'{row["status"]} |')
    report += ["", "## Boundary", "",
               "The tables report sensitivity of finite-window measurements. They do not select an asymptotic law, establish a unique finite-size onset, validate a real alloy or make any estimator a particle radius."]
    (output / "REPORT.md").write_text("\n".join(report) + "\n")
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        campaign_manifest_sha256=sha(manifest_path),
        campaign_status_sha256=sha(status_path), input_sha256=hashes,
        source_sha256={
            "research/analyse_extension_observable_robustness.py": sha(Path(__file__)),
            "research/FULL_EXTENSION_OBSERVABLE_ROBUSTNESS_PROTOCOL_2026-09-19.md": sha(PROTOCOL),
            "research/metrology.py": sha(Path(__file__).with_name("metrology.py")),
            "research/analyse_campaign.py": sha(Path(__file__).with_name("analyse_campaign.py")),
        },
        measures=MEASURES, windows=WINDOWS, matched_times=MATCHED_TIMES,
        bootstrap_draws=DRAWS, bootstrap_unit="whole independent trajectory",
        fit_comparison="paired trajectory indices within each composition-size group",
        size_comparison="independent trajectory resampling between sizes",
        interpretation="Post-result observable robustness; not a new blind discovery or calibrated radius",
    ), indent=2) + "\n")
    return output / "REPORT.md"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    print(analyse(arguments.campaign, arguments.output))
