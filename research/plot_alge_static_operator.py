"""Plot the fixed Al–Ge image-operator audit without hiding failed planes.

This is a descriptive display of correlated slices from one specimen, not a
growth curve or an inferential comparison between annealing stages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE = ROOT / "research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv"
DEFAULT_SUMMARY = ROOT / "research/results/alge_static_operator_2026-09-18/summary.json"
DEFAULT_OUTPUT = ROOT / "figures/fig_alge_fixed_plane_audit.png"
STAGES = (15, 105, 195, 315)
TARGET_Z = tuple(round(12.0 + 0.6 * i, 1) for i in range(11))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_fixed_rows(path: Path) -> dict[int, list[dict]]:
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source))
    by_stage: dict[int, list[dict]] = {stage: [] for stage in STAGES}
    for row in rows:
        stage = int(row["minutes"])
        if stage not in by_stage:
            raise ValueError(f"Unexpected stage: {stage}")
        by_stage[stage].append(row)
    if len(rows) != 44 or any(len(by_stage[stage]) != 11 for stage in STAGES):
        raise ValueError("Expected exactly 11 preselected rows per stage")
    for stage, stage_rows in by_stage.items():
        stage_rows.sort(key=lambda row: float(row["target_z_um"]))
        actual_z = [round(float(row["target_z_um"]), 1) for row in stage_rows]
        if actual_z != list(TARGET_Z):
            raise ValueError(f"Stage {stage} has unexpected or duplicate z planes")
        for row in stage_rows:
            ratio = float(row["ratio_altered_to_native"])
            resolved = row["measurement_status"] == "resolved"
            if resolved != (math.isfinite(ratio) and ratio > 0):
                raise ValueError(f"Resolution flag and ratio disagree at {stage} min")
    return by_stage


def make_figure(by_stage: dict[int, list[dict]], summary: dict, output: Path) -> None:
    fig, (ax_status, ax_ratio) = plt.subplots(
        1, 2, figsize=(10.8, 5.0), gridspec_kw={"width_ratios": [1, 1.65]}
    )
    resolved = np.array(
        [[row["measurement_status"] == "resolved" for row in by_stage[stage]]
         for stage in STAGES], dtype=int
    ).T
    # One square is one fixed physical-z plane. Blue = both lengths resolved.
    from matplotlib.colors import ListedColormap

    ax_status.imshow(
        resolved, aspect="auto", origin="lower", interpolation="nearest",
        cmap=ListedColormap(["#e4b168", "#287b86"]), vmin=0, vmax=1
    )
    ax_status.set_xticks(
        range(4),
        [f"{stage}\n{int(resolved[:, i].sum())}/11"
         for i, stage in enumerate(STAGES)],
    )
    ax_status.set_yticks(range(11), [str(z) for z in TARGET_Z])
    ax_status.set_xlabel("Annealing time (min)")
    ax_status.set_ylabel("Declared z coordinate (µm)*")
    ax_status.set_title("Every fixed plane (blue=resolved; count below)", loc="left",
                        fontsize=10, fontweight="bold")

    for i, stage in enumerate(STAGES):
        rows = by_stage[stage]
        for j, row in enumerate(rows):
            ratio = float(row["ratio_altered_to_native"])
            if not math.isfinite(ratio):
                continue
            # Horizontal displacement only distinguishes the 11 correlated planes.
            xpos = i + (j - 5) * 0.042
            face = "#287b86" if stage >= 195 else "white"
            ax_ratio.scatter(
                xpos, ratio, s=34, facecolors=face, edgecolors="#287b86",
                linewidths=1.1, zorder=3
            )
        entry = next(item for item in summary["stages"] if item["minutes"] == stage)
        if entry["status"] == "all fixed planes resolved":
            ax_ratio.plot(
                [i - 0.28, i + 0.28], [entry["median_ratio"]] * 2,
                color="#b04235", lw=2.2, zorder=4
            )
    ax_ratio.axhline(1.0, color="#46535c", ls="--", lw=1)
    ax_ratio.set_xlim(-0.48, 3.48)
    ax_ratio.set_ylim(0.8, 1.5)
    ax_ratio.set_xticks(range(4), [str(stage) for stage in STAGES])
    ax_ratio.set_xlabel("Annealing time (min)")
    ax_ratio.set_ylabel("4× / native static length (unitless)")
    ax_ratio.set_title("Resolved planes only", loc="left", fontsize=11, fontweight="bold")
    ax_ratio.text(
        0.02, 0.97, "Red bars: median only where all 11 planes resolved",
        transform=ax_ratio.transAxes, va="top", fontsize=8, color="#44545c"
    )
    fig.suptitle("Image resolution changes a static Al–Ge length; early stages fail the fixed test",
                 x=0.04, ha="left", fontsize=12, fontweight="bold")
    fig.text(
        0.04, 0.01,
        "One published specimen; neighbouring slices are correlated. *z follows TIFF lower-bound + page-index convention, not verified registration. "
        "No kinetic exponent or hardness prediction.",
        fontsize=7.5, color="#44545c"
    )
    fig.tight_layout(rect=[0.02, 0.14, 0.98, 0.88], w_pad=2.3)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    by_stage = load_fixed_rows(args.table)
    summary = json.loads(args.summary.read_text())
    for entry in summary["stages"]:
        count = sum(row["measurement_status"] == "resolved"
                    for row in by_stage[entry["minutes"]])
        if count != entry["eligible_resolved_planes"]:
            raise ValueError("Summary/row resolved counts disagree")
    make_figure(by_stage, summary, args.output)
    provenance = {
        "source_sha256": sha(Path(__file__)),
        "table_sha256": sha(args.table),
        "summary_sha256": sha(args.summary),
        "source": "Fell 2023, DOI 10.17632/hj9njz3rxp.1, CC BY 4.0",
        "status": "descriptive static observation audit; no independent-specimen uncertainty or growth fit",
        "figure": args.output.name,
    }
    args.output.with_suffix(".json").write_text(
        json.dumps(provenance, indent=2, allow_nan=False) + "\n"
    )
    print(args.output)


if __name__ == "__main__":
    main()
