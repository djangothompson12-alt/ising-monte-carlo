"""Static scientific figure for the post-hoc binning-stage analysis.

Point-estimate bars show an arithmetic decomposition on identical fit masks;
uncertainty intervals remain in the source CSVs and are not implied by bar size.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research.imaging_benchmark import sha


PAIRS = (("full", "block4_greyscale"),
         ("block4_greyscale", "block4_ties_plus"),
         ("full", "block4_ties_plus"))


def _load(path: Path) -> dict:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        key = (float(row["c"]), int(row["nominal_t_min"]), int(row["nominal_t_max"]),
               row["reference"], row["treatment"])
        if key in result:
            raise ValueError(f"Duplicate fit row: {key}")
        result[key] = row
    return result


def _component(table: dict, concentration: float, upper: int) -> tuple[float, float, float]:
    values = []
    for reference, treatment in PAIRS:
        key = (concentration, 1000, upper, reference, treatment)
        if key not in table:
            raise ValueError(f"Missing declared fit: {key}")
        values.append(float(table[key]["delta_alpha"]))
    if abs(values[0] + values[1] - values[2]) > 1e-12:
        raise ValueError("Stage contributions do not sum to total")
    return tuple(values)


def plot(main_csv: Path, repeat_csv: Path, output: Path) -> None:
    provenance = output.with_suffix(".json")
    if output.exists() or provenance.exists():
        raise FileExistsError("Choose new output paths; previous figure is immutable")
    main = _load(main_csv)
    repeat = _load(repeat_csv)
    panels = [
        ("1,000–20,000 sweeps", [("main · c=0.50", main, 0.5, 20000),
                                   ("main · c=0.15", main, 0.15, 20000),
                                   ("repeat · c=0.50", repeat, 0.5, 20000),
                                   ("repeat · c=0.15", repeat, 0.15, 20000)]),
        ("1,000–200,000 sweeps", [("main · c=0.50", main, 0.5, 200000),
                                    ("main · c=0.15", main, 0.15, 200000)]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for axis, (title, groups) in zip(axes, panels):
        for index, (label, table, concentration, upper) in enumerate(groups):
            greyscale, threshold, total = _component(table, concentration, upper)
            y = len(groups) - index - 1
            axis.barh(y, greyscale, height=0.55, color="#326b86",
                      label="4× greyscale averaging" if index == 0 else None)
            axis.barh(y, threshold, left=greyscale, height=0.55, color="#cc7940",
                      label="binary threshold" if index == 0 else None)
            axis.plot(total, y, marker="D", color="black", markersize=4,
                      label="total shift" if index == 0 else None)
        axis.set_yticks(range(len(groups)), [group[0] for group in groups[::-1]])
        axis.axvline(0, color="black", lw=1)
        axis.set(xlim=(-0.095, 0.02), xlabel="Change in fitted exponent, Δα", title=title)
        axis.grid(axis="x", alpha=0.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, ncol=3,
               loc="upper center", bbox_to_anchor=(0.5, 0.90))
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.15, top=0.75, wspace=0.36)
    fig.suptitle("Same trajectories; different observation stages and fit windows", y=0.98)
    fig.savefig(output, dpi=190)
    plt.close(fig)
    provenance.write_text(json.dumps({
        "status": "exploratory post-hoc figure; point estimates only",
        "main_csv_sha256": sha(main_csv), "repeat_csv_sha256": sha(repeat_csv),
        "source_sha256": sha(Path(__file__)),
        "interpretation": "Stage bars add within each cohort and fixed time mask; uncertainty is in paired_fits.csv.",
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main_csv", type=Path)
    parser.add_argument("repeat_csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plot(args.main_csv, args.repeat_csv, args.output)
    print(args.output)
