"""Make two compact paper-facing figures from completed, archived CSV results.

Figure 1 uses the periodic Model B engine's connected-correlation length.
Figure 2 uses a separate non-periodic finite-image estimator. Their y values
must not be interpreted as if the underlying observables were identical.
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


WINDOW_STARTS = (2, 100, 1000)
COMPOSITIONS = (0.5, 0.15)


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def one(rows: list[dict], **criteria: object) -> dict:
    found = [row for row in rows if all(
        (float(row[key]) == float(value) if key in ("c", "L", "t_min", "t_max") else row[key] == str(value))
        for key, value in criteria.items())]
    if len(found) != 1:
        raise ValueError(f"Expected exactly one row for {criteria}; found {len(found)}")
    return found[0]


def window_rows(table: list[dict]) -> list[dict]:
    selected = []
    for c in COMPOSITIONS:
        for start in WINDOW_STARTS:
            row = one(table, c=c, L=128, t_min=start, t_max=200000)
            if int(row["n"]) != 8 or not (float(row["bootstrap_low"]) <= float(row["alpha"]) <= float(row["bootstrap_high"])):
                raise ValueError("Unexpected main-study count or interval")
            selected.append(row)
    return selected


def observation_rows(main: list[dict], repeat: list[dict]) -> list[tuple[str, dict]]:
    selected = []
    for cohort, rows, expected_n in (("original", main, 8), ("new seeds", repeat, 4)):
        for c in COMPOSITIONS:
            row = one(rows, c=c, L=128, condition="bin4", t_min=1000, t_max=20000)
            if int(row["n"]) != expected_n or not (
                float(row["delta_low"]) <= float(row["delta_vs_full"]) <= float(row["delta_high"])
            ):
                raise ValueError("Unexpected observation-study count or interval")
            selected.append((cohort, row))
    return selected


def plot_window(rows: list[dict], output: Path) -> None:
    fig, axis = plt.subplots(figsize=(6.2, 4.2), layout="constrained")
    for c, color in ((0.5, "#26637a"), (0.15, "#b35632")):
        subset = [r for r in rows if float(r["c"]) == c]
        xs = [int(r["t_min"]) for r in subset]
        ys = [float(r["alpha"]) for r in subset]
        lo = [y-float(r["bootstrap_low"]) for y, r in zip(ys, subset)]
        hi = [float(r["bootstrap_high"])-y for y, r in zip(ys, subset)]
        axis.errorbar(xs, ys, yerr=[lo, hi], fmt="o-", capsize=3,
                      color=color, label=f"+1 fraction {c:g}; 8 runs")
    axis.axhline(1/3, color="black", linestyle="--", linewidth=1,
                 label="late-time 1/3 guide")
    axis.set_xscale("log")
    axis.set_xticks(WINDOW_STARTS, [str(value) for value in WINDOW_STARTS])
    axis.set(xlabel="Nominal first sweep in fit (last sweep: 200,000)",
             ylabel="Effective exponent from periodic Model B length",
             title="The same runs give different finite-window slopes")
    axis.set_ylim(0.16, 0.35)
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_observation(selected: list[tuple[str, dict]], output: Path) -> None:
    fig, axis = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
    labels = []
    for index, (cohort, row) in enumerate(selected):
        value = float(row["delta_vs_full"])
        lower = float(row["delta_low"])
        upper = float(row["delta_high"])
        color = "#26637a" if cohort == "original" else "#b35632"
        axis.errorbar(value, index, xerr=[[value-lower], [upper-value]],
                      fmt="o", capsize=4, color=color)
        labels.append(f"{cohort}, c={float(row['c']):g}, n={row['n']}")
    axis.axvline(0, color="black", linewidth=1)
    axis.set_yticks(range(len(labels)), labels)
    axis.invert_yaxis()
    axis.set(xlabel="Change in fitted image exponent, 4× bin + threshold minus full image",
             title="Same snapshots; image processing changes the fit")
    axis.grid(axis="x", alpha=0.2)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def make(main_exponents: Path, original_images: Path, repeat_images: Path,
         window_output: Path, observation_output: Path) -> None:
    provenance = observation_output.with_suffix(".json")
    if any(path.exists() for path in (window_output, observation_output, provenance)):
        raise FileExistsError("Choose unused outputs; do not replace a previously reviewed figure")
    windows = window_rows(load_rows(main_exponents))
    observations = observation_rows(load_rows(original_images), load_rows(repeat_images))
    window_output.parent.mkdir(parents=True, exist_ok=True)
    observation_output.parent.mkdir(parents=True, exist_ok=True)
    plot_window(windows, window_output)
    plot_observation(observations, observation_output)
    provenance.write_text(json.dumps(dict(
        status="paper-facing redrawing of completed results; no new simulations or fits",
        input_sha256={str(path): sha(path) for path in (main_exponents, original_images, repeat_images)},
        source_sha256=sha(Path(__file__)),
        window_method="periodic connected Model B half-height length; 500 whole-replica bootstrap draws",
        observation_method="non-periodic finite-image half-height length; paired whole-replica bootstrap; nominal 1000–20000 sweeps",
        warning="Do not compare absolute exponents across the two figures as identical observables; windows overlap; the repeat has a different time grid and four replicas per composition.",
        window_rows=windows, observation_rows=[dict(cohort=cohort, **row) for cohort, row in observations],
    ), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-exponents", type=Path, required=True)
    parser.add_argument("--original-images", type=Path, required=True)
    parser.add_argument("--repeat-images", type=Path, required=True)
    parser.add_argument("--window-output", type=Path, required=True)
    parser.add_argument("--observation-output", type=Path, required=True)
    args = parser.parse_args()
    make(args.main_exponents, args.original_images, args.repeat_images,
         args.window_output, args.observation_output)
