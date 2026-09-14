"""Exploratory dynamic-scaling diagnostics on complete archived Model B groups.

Plots raw and length-rescaled connected correlations and radial structure
factors. A dispersion score describes overlap on the available common range;
it is not a proof of dynamic scaling or a fitted exponent.
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

from research.metrology import spectrum


TARGET_SWEEPS = (1_000, 10_000, 100_000, 200_000)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlap_rms(curves: list[tuple[np.ndarray, np.ndarray]], logarithmic_y: bool = False,
                x_max: float | None = None) -> dict:
    """Describe curve disagreement over a common abscissa without shifting curves."""
    prepared = []
    for x, y in curves:
        x, y = np.asarray(x, float), np.asarray(y, float)
        valid = np.isfinite(x) & np.isfinite(y) & (x > 0)
        if logarithmic_y:
            valid &= y > 0
        x, y = x[valid], y[valid]
        if len(x) < 3 or np.any(np.diff(x) <= 0):
            return dict(x_min=float("nan"), x_max=float("nan"), rms=float("nan"), points=0)
        prepared.append((x, np.log(y) if logarithmic_y else y))
    if len(prepared) < 2:
        return dict(x_min=float("nan"), x_max=float("nan"), rms=float("nan"), points=0)
    lo = max(x[0] for x, _ in prepared)
    hi = min(x[-1] for x, _ in prepared)
    if x_max is not None:
        hi = min(hi, x_max)
    if not lo < hi:
        return dict(x_min=float(lo), x_max=float(hi), rms=float("nan"), points=0)
    common = np.geomspace(lo, hi, 100)
    values = np.asarray([np.interp(common, x, y) for x, y in prepared])
    dispersion = values - values.mean(axis=0)
    return dict(x_min=float(lo), x_max=float(hi),
                rms=float(np.sqrt(np.mean(dispersion**2))), points=len(common))


def radial_structure(snapshot: np.ndarray, bin_count: int = 48) -> tuple[np.ndarray, np.ndarray]:
    """Return nonzero radial Fourier power averaged in fixed q bins."""
    q, power = spectrum(snapshot)
    edges = np.linspace(0.0, 0.5, bin_count + 1)
    valid = (q > 0) & (q < edges[-1])
    weighted, _ = np.histogram(q[valid], bins=edges, weights=power[valid])
    counts, _ = np.histogram(q[valid], bins=edges)
    centres = 0.5 * (edges[:-1] + edges[1:])
    return centres[counts > 0], (weighted / np.maximum(counts, 1))[counts > 0]


def _selected_indices(times: np.ndarray) -> list[tuple[int, int]]:
    selected = []
    for target in TARGET_SWEEPS:
        if target > times[-1]:
            continue
        index = int(np.argmin(np.abs(np.log(times / target))))
        if abs(np.log(times[index] / target)) <= np.log(1.15) and index not in [i for _, i in selected]:
            selected.append((target, index))
    return selected


def analyse(folder: Path, output: Path, size: int = 128) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory for an immutable analysis")
    manifest_path = folder / "manifest.json"
    plan = json.loads(manifest_path.read_text())["identity"]["plan"]
    if size not in plan["sizes"]:
        raise ValueError(f"L={size} is not in the campaign plan")
    output.mkdir(parents=True)
    rows, scores, inputs = [], [], {}
    for ci, concentration in enumerate(plan["concentrations"]):
        paths = sorted(folder.glob(f"c{ci}_L{size}_rep*.npz"))
        if len(paths) != plan["replicas"]:
            raise ValueError(f"Expected {plan['replicas']} complete L={size}, c={concentration} replicas; found {len(paths)}")
        archives = []
        for path in paths:
            inputs[path.name] = sha256(path)
            with np.load(path, allow_pickle=False) as data:
                if int(data["t"][-1]) != plan["max_sweeps"]:
                    raise ValueError(f"Incomplete replica: {path}")
                archives.append((data["t"].copy(), data["lengths"].copy(),
                                 data["correlations"].copy(), data["snapshots"].copy()))
        times = archives[0][0]
        if any(not np.array_equal(item[0], times) for item in archives[1:]):
            raise ValueError("Replicas have mismatched checkpoint times")
        selected = _selected_indices(times)
        if len(selected) < 2:
            raise ValueError("Need at least two predeclared checkpoint times in the archive")
        fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout="constrained")
        c_curves, s_curves = [], []
        for target, index in selected:
            lengths = np.asarray([item[1][index].mean() for item in archives])
            if not np.all(np.isfinite(lengths)) or np.any(lengths <= 0):
                rows.append(dict(c=concentration, L=size, target_sweep=target,
                                 actual_sweep=int(times[index]), n=len(paths), length=float("nan"),
                                 length_se=float("nan"), status="unresolved_length"))
                continue
            ell = float(np.mean(lengths))
            ell_se = float(np.std(lengths, ddof=1) / np.sqrt(len(lengths)))
            corr = np.mean([item[2][index].mean(axis=0) for item in archives], axis=0)
            r = np.arange(len(corr), dtype=float)
            radial = [radial_structure(item[3][index]) for item in archives]
            q = radial[0][0]
            if any(not np.array_equal(q, item[0]) for item in radial[1:]):
                raise ValueError("Radial Fourier bins differ across replicas")
            sf = np.mean([item[1] for item in radial], axis=0)
            label = f"{int(times[index]):,} sweeps"
            axes[0, 0].plot(r, corr, label=label)
            axes[0, 1].plot(r / ell, corr, label=label)
            axes[1, 0].plot(q, sf, label=label)
            axes[1, 1].plot(q * ell, sf / ell**2, label=label)
            c_curves.append((r[1:] / ell, corr[1:]))
            s_curves.append((q * ell, sf / ell**2))
            rows.append(dict(c=concentration, L=size, target_sweep=target,
                             actual_sweep=int(times[index]), n=len(paths), length=ell,
                             length_se=ell_se, status="resolved"))
        for ax, xlabel, ylabel in zip(axes.flat,
                ("r (sites)", "r / ell", "q (cycles/site)", "q ell"),
                ("connected C", "connected C", "radial S(q)", "S(q) / ell²")):
            ax.set(xlabel=xlabel, ylabel=ylabel)
            ax.grid(alpha=0.2)
            ax.legend(fontsize=8)
        for ax in axes[1]:
            ax.set_xscale("log")
            ax.set_yscale("log")
        axes[0, 1].set_xlim(left=0, right=3)
        fig.suptitle(f"L={size}, c={concentration}, n={len(paths)}; no fitted shifts")
        figure_path = output / f"scaling_c{ci}_L{size}.png"
        fig.savefig(figure_path, dpi=180)
        plt.close(fig)
        scores.append(dict(c=concentration, L=size, n_times=len(c_curves),
                           correlation_overlap=overlap_rms(c_curves, x_max=3),
                           structure_overlap_log=overlap_rms(s_curves, logarithmic_y=True)))
    table = output / "selected_lengths.csv"
    with table.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (output / "overlap_scores.json").write_text(json.dumps(scores, indent=2) + "\n")
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        campaign_manifest_sha256=sha256(manifest_path),
        source_sha256=sha256(Path(__file__)), inputs_sha256=inputs,
        target_sweeps=TARGET_SWEEPS,
        correlation_score_range="0 < r/ell <= 3, matching the plotted panel",
        role="Exploratory shape comparison on an existing archive; scores describe overlap, not evidence of a universal growth exponent."),
        indent=2) + "\n")
    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=128)
    args = parser.parse_args()
    print(analyse(args.campaign, args.output, args.size))
