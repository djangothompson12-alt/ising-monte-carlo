"""Compare existing image-observation effects with an independent seed ensemble.

The original 64-replica campaign is the exploratory discovery set; the fresh
eight-replica L=128 campaign is a limited holdout check. This script does not
learn a universal correction or choose a safe pixel threshold.
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


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def _operator_scale(condition: str) -> tuple[str, float]:
    if condition.startswith("bin"):
        return "block_width", float(condition[3:])
    if condition.startswith("blur"):
        return "blur_sigma", float(condition[4:].split("_")[0])
    if condition.startswith("crop"):
        return "field_width", float(condition[4:])
    return "unscaled", float("nan")


def analyse(original: Path, fresh: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory")
    sources = {"original": original, "fresh": fresh}
    rows = []
    hashes = {}
    for ensemble, folder in sources.items():
        fit_path, obs_path = folder / "paired_fits.csv", folder / "observations.csv"
        hashes[ensemble] = {name: _hash(path) for name, path in ((fit_path.name, fit_path), (obs_path.name, obs_path))}
        fits = [row for row in _csv(fit_path) if row["condition"] != "periodic_engine" and int(row["L"]) == 128
                and int(row["t_min"]) == 1000 and int(row["t_max"]) == 20000]
        observations = _csv(obs_path)
        for fit in fits:
            concentration = float(fit["c"])
            end = int(fit["used_t_max"])
            condition = fit["condition"]
            if not np.isfinite(float(fit["delta_vs_full"])):
                continue
            relevant = [row for row in observations if float(row["c"]) == concentration
                        and int(row["L"]) == 128 and int(row["t"]) == end]
            full = [float(row["length"]) for row in relevant if row["condition"] == "full"]
            observed = [row for row in relevant if row["condition"] == condition]
            if len(full) != int(fit["n"]) or not observed:
                raise ValueError(f"Missing matched end-point observations for {ensemble}, c={concentration}, {condition}")
            mean_full = float(np.mean(full))
            phase_fraction = float(np.mean([float(row["phase_fraction"]) for row in observed]))
            kind, scale = _operator_scale(condition)
            rows.append(dict(ensemble=ensemble, c=concentration, L=128, n=int(fit["n"]),
                             condition=condition, kind=kind, scale_sites=scale,
                             used_t_min=int(fit["used_t_min"]), used_t_max=end,
                             full_length_sites_end=mean_full,
                             length_over_scale_end=mean_full / scale if np.isfinite(scale) else float("nan"),
                             phase_fraction_end=phase_fraction,
                             phase_fraction_bias_end=phase_fraction - concentration,
                             alpha=float(fit["alpha"]), delta_vs_full=float(fit["delta_vs_full"]),
                             delta_low=float(fit["delta_low"]), delta_high=float(fit["delta_high"]),
                             unresolved_fraction=float(fit["unresolved_fraction"])))
    output.mkdir(parents=True)
    table = output / "reliability_map.csv"
    with table.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    lookup = {(row["ensemble"], row["c"], row["condition"]): row for row in rows}
    paired = []
    for c in sorted({row["c"] for row in rows}):
        for condition in sorted({row["condition"] for row in rows}):
            before = lookup.get(("original", c, condition))
            after = lookup.get(("fresh", c, condition))
            if before is None or after is None:
                continue
            paired.append(dict(c=c, condition=condition,
                               original_delta=before["delta_vs_full"], fresh_delta=after["delta_vs_full"],
                               fresh_minus_original=after["delta_vs_full"] - before["delta_vs_full"],
                               same_sign=(np.sign(after["delta_vs_full"]) == np.sign(before["delta_vs_full"]))
                               if before["delta_vs_full"] != 0 and after["delta_vs_full"] != 0 else None,
                               original_n=before["n"], fresh_n=after["n"]))
    with (output / "holdout_comparison.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(paired[0]))
        writer.writeheader(); writer.writerows(paired)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), layout="constrained")
    for ax, kind, title in zip(axes,
            ("block_width", "blur_sigma", "field_width"),
            ("Block averaging + threshold", "Gaussian blur + threshold", "Finite observation window")):
        for c, color in ((0.5, "tab:blue"), (0.15, "tab:orange")):
            for ensemble, marker in (("original", "o"), ("fresh", "x")):
                subset = [row for row in rows if row["kind"] == kind and row["c"] == c and row["ensemble"] == ensemble]
                ax.scatter([row["length_over_scale_end"] for row in subset],
                           [row["delta_vs_full"] for row in subset],
                           label=f"c={c}, {ensemble}", color=color, marker=marker, s=50)
        ax.axhline(0, color="black", ls=":")
        ax.set(xlabel="Full-image length / operator scale at window end", ylabel="Fitted exponent change", title=title)
        ax.grid(alpha=0.2)
    axes[0].legend(fontsize=7)
    fig.suptitle("Exploratory observation sensitivity; × = independent-seed holdout")
    fig.savefig(output / "reliability_map.png", dpi=180)
    plt.close(fig)
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=_hash(Path(__file__)),
        inputs_sha256=hashes, fit_window="nominal 1,000–20,000 sweeps; actual retained endpoints shown in CSV",
        original_role="exploratory discovery ensemble", fresh_role="four-replica-per-composition holdout",
        caveats=["Block width, blur sigma and field width are different operators; x positions are not interchangeable.",
                 "No fitted universal reliability threshold or correction is inferred.",
                 "A held-out simulation is not experimental validation."]), indent=2) + "\n")
    (output / "REPORT.md").write_text(
        "# Measurement-reliability map (exploratory)\n\n"
        "The original and fresh-seed campaigns are shown separately. Each plotted point is a **paired fitted-exponent change**, not an independent growth law. The x coordinate is the full-image characteristic length divided by the declared operator's scale at the final retained checkpoint. Block size, Gaussian sigma and field width have different physical meanings and cannot be pooled into one universal resolution rule.\n\n"
        "The original ensemble was inspected before this map was designed. The fresh ensemble is a small independent-seed repeat, not a preregistered prospective external validation set. No safe pixel threshold, microscope-independent correction or real-alloy prediction is claimed. Phase-fraction bias, unresolved fractions and every source value are in the CSV files.\n"
    )
    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("fresh", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(analyse(args.original, args.fresh, args.output))
