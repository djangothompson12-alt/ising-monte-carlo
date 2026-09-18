"""Exploratory known-growth control for the finite-image length estimator.

Square checkerboard domains have a prescribed width 2s at time t=s**3, so
their geometric width grows exactly as t**(1/3). This is *not* Kawasaki
dynamics, a realistic alloy image, or an independent replication. It tests
what the existing observation pipeline reports when the input growth is
known. The field of view, not the underlying pattern, changes across panels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from research.imaging import image_length, observe
from research.imaging_benchmark import sha, write_csv


SCALES = (6, 8, 12, 16, 24, 32)
FIELD_WIDTHS = (384, 768, 1536)
OPERATORS = {
    "native": dict(factor=1, sigma=0.0, threshold=0.0),
    "bin4_threshold": dict(factor=4, sigma=0.0, threshold=0.0),
    "bin8_threshold": dict(factor=8, sigma=0.0, threshold=0.0),
}


def prescribed_pattern(field_width: int, scale: int) -> np.ndarray:
    """Return alternating square domains of side 2*scale lattice sites."""
    if field_width < 4 * scale or field_width % (4 * scale):
        raise ValueError("Field width must contain whole 4s repeat cells")
    coordinates = np.arange(field_width, dtype=np.int32) // (2 * scale)
    return (2 * ((coordinates[:, None] + coordinates[None, :]) % 2) - 1).astype(np.int8)


def slope(times: np.ndarray, values: np.ndarray) -> float:
    if len(times) < 4 or np.any(times <= 0) or np.any(values <= 0) or not np.all(np.isfinite(values)):
        raise ValueError("Need at least four positive, resolved lengths")
    return float(np.polyfit(np.log(times), np.log(values), 1)[0])


def calculate() -> tuple[list[dict], list[dict]]:
    rows = []
    for width in FIELD_WIDTHS:
        for scale in SCALES:
            field = prescribed_pattern(width, scale)
            for name, operator in OPERATORS.items():
                observed = observe(field, **operator)
                factor = operator["factor"]
                measure = image_length(observed, pixel_size=float(factor))
                rows.append(dict(
                    field_width_sites=width, scale_sites=scale,
                    prescribed_domain_width_sites=2 * scale,
                    synthetic_time=scale ** 3, operator=name,
                    pixel_size_sites=factor, measured_length_sites=measure["length"],
                    length_x_sites=measure["length_x"], length_y_sites=measure["length_y"],
                    resolved=measure["resolved"], observed_plus_fraction=float((observed > 0).mean()),
                ))
    fits = []
    for width in FIELD_WIDTHS:
        for name in OPERATORS:
            subset = [r for r in rows if r["field_width_sites"] == width and r["operator"] == name]
            times = np.asarray([r["synthetic_time"] for r in subset], dtype=float)
            lengths = np.asarray([r["measured_length_sites"] for r in subset], dtype=float)
            fits.append(dict(field_width_sites=width, operator=name, points=len(subset),
                             prescribed_slope=slope(times, np.asarray([r["prescribed_domain_width_sites"] for r in subset], float)),
                             measured_slope=slope(times, lengths),
                             min_time=int(times.min()), max_time=int(times.max())))
    return rows, fits


def plot(rows: list[dict], fits: list[dict], output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), constrained_layout=True)
    for width in FIELD_WIDTHS:
        subset = [r for r in rows if r["field_width_sites"] == width and r["operator"] == "native"]
        t = [r["synthetic_time"] for r in subset]
        length = [r["measured_length_sites"] for r in subset]
        axes[0].loglog(t, length, "o-", label=f"field {width} sites")
    axes[0].set_xlabel("Constructed time $t=s^3$ (arbitrary units)")
    axes[0].set_ylabel("Measured correlation length (sites)")
    axes[0].set_title("Same imposed growth; different fields of view")
    axes[0].legend(fontsize=8)
    for index, name in enumerate(OPERATORS):
        selected = [fit for fit in fits if fit["operator"] == name]
        axes[1].plot([fit["field_width_sites"] for fit in selected],
                     [fit["measured_slope"] for fit in selected], "o-", label=name)
    axes[1].axhline(1 / 3, color="black", linestyle="--", linewidth=1,
                    label="imposed $1/3$")
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(FIELD_WIDTHS, [str(width) for width in FIELD_WIDTHS])
    axes[1].set_xlabel("Field width (sites)")
    axes[1].set_ylabel("Fitted image-length exponent")
    axes[1].set_title("Estimated slope versus known $1/3$")
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.grid(alpha=0.2)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def run(output: Path) -> None:
    if output.exists():
        raise FileExistsError("Choose a new output directory; existing results are not overwritten")
    rows, fits = calculate()
    output.mkdir(parents=True)
    write_csv(output / "measurements.csv", rows)
    write_csv(output / "fits.csv", fits)
    plot(rows, fits, output / "known_growth_control.png")
    (output / "provenance.json").write_text(json.dumps(dict(
        status="exploratory synthetic control; not preregistered or experimental validation",
        source_sha256=sha(Path(__file__)), imaging_sha256=sha(Path(__file__).with_name("imaging.py")),
        field_widths_sites=FIELD_WIDTHS, scales_sites=SCALES, operators=OPERATORS,
        prescribed_relation="domain width=2s; synthetic time=s^3; exact geometric exponent=1/3",
        replicate_count=0, uncertainty_intervals="none: deterministic input patterns",
    ), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
