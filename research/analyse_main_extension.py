"""Analyse the complete, prospective 0.65 Tc four-size campaign.

Every comparison uses fixed time windows and whole-replica uncertainty. The
ell/L < 0.15 filter is a declared sensitivity only, never the primary fit.
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

from research.analyse_campaign import bootstrap_slope, fit_slope


WINDOWS = ((1_000, 20_000), (1_000, 200_000), (20_000, 200_000),
           (20_000, 1_000_000), (200_000, 1_000_000))
LENGTH_FRACTION = 0.15


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(folder: Path, plan: dict) -> tuple[dict, dict]:
    expected = {f"c{ci}_L{L}_rep{rep:03d}.npz"
                for rep in range(plan["replicas"])
                for ci in range(len(plan["concentrations"]))
                for L in plan["sizes"]}
    present = {p.name for p in folder.glob("*.npz")}
    if expected != present:
        raise ValueError(f"Campaign incomplete or unexpected NPZ: {len(expected-present)} missing, {len(present-expected)} unexpected")
    groups, hashes = {}, {}
    for ci, c in enumerate(plan["concentrations"]):
        for L in plan["sizes"]:
            paths = [folder / f"c{ci}_L{L}_rep{rep:03d}.npz" for rep in range(plan["replicas"])]
            runs = []
            for path in paths:
                with np.load(path, allow_pickle=False) as data:
                    t = np.asarray(data["t"], dtype=int)
                    lengths = np.asarray(data["lengths"], dtype=float)
                if t[-1] != plan["max_sweeps"] or lengths.shape != (len(t), 2):
                    raise ValueError(f"Incomplete or malformed replica: {path}")
                runs.append((t, lengths))
                hashes[path.name] = sha(path)
            if any(not np.array_equal(run[0], runs[0][0]) for run in runs[1:]):
                raise ValueError(f"Time checkpoints differ in c{ci}, L{L}")
            groups[(ci, L)] = (runs[0][0], np.asarray([r[1] for r in runs]))
    return groups, hashes


def analyse(folder: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Use a new output directory")
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    plan = manifest["identity"]["plan"]
    if (plan["sizes"] != [32, 64, 96, 128] or
            plan["concentrations"] != [0.5, 0.15] or
            plan["max_sweeps"] != 1_000_000 or plan["replicas"] != 16 or
            plan["T_final_over_tc"] != 0.65):
        raise ValueError("Input does not match the frozen main-extension protocol")
    groups, hashes = _inventory(folder, plan)
    output.mkdir(parents=True)
    records, values = [], []
    for ci, c in enumerate(plan["concentrations"]):
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), layout="constrained")
        for L in plan["sizes"]:
            t, directional = groups[(ci, L)]
            trajectory = directional.mean(axis=2)
            # Preserve unresolved values: no nanmean or changing replica count.
            resolved = np.all(np.isfinite(directional) & (directional > 0), axis=(0, 2))
            mean = np.mean(trajectory, axis=0)
            se = np.std(trajectory, axis=0, ddof=1) / np.sqrt(len(trajectory))
            for j, sweep in enumerate(t):
                values.append(dict(composition=c, L=L, sweep=int(sweep),
                                   n_replicas=len(trajectory), resolved_all=bool(resolved[j]),
                                   resolved_x=int(np.count_nonzero(np.isfinite(directional[:, j, 0]) & (directional[:, j, 0] > 0))),
                                   resolved_y=int(np.count_nonzero(np.isfinite(directional[:, j, 1]) & (directional[:, j, 1] > 0))),
                                   mean_length_x=float(np.mean(directional[:, j, 0])),
                                   mean_length_y=float(np.mean(directional[:, j, 1])),
                                   mean_length=float(mean[j]), standard_error=float(se[j]),
                                   length_over_L=float(mean[j]/L)))
            axes[0].plot(t[resolved], mean[resolved], label=f"L={L}")
            axes[0].fill_between(t[resolved], (mean-se)[resolved], (mean+se)[resolved], alpha=.12)
            axes[1].plot(t[resolved], (mean/L)[resolved], label=f"L={L}")
            local = []
            for j in range(len(t)):
                mask = resolved & (t >= t[max(0, j-4)]) & (t <= t[min(len(t)-1, j+4)])
                local.append(fit_slope(t, mean, mask, min_span=2))
            axes[2].plot(t, local, label=f"L={L}")
            for lower, upper in WINDOWS:
                for method, fraction_filter in (("primary_unfiltered", False),
                                                ("ell_over_L_below_0.15_sensitivity", True)):
                    mask = resolved & (t >= lower) & (t <= upper)
                    if fraction_filter:
                        mask &= mean / L < LENGTH_FRACTION
                    alpha, lo, hi = bootstrap_slope(t, trajectory, mask, seed=20260913, draws=500)
                    records.append(dict(composition=c, L=L, method=method,
                                        nominal_t_min=lower, nominal_t_max=upper,
                                        used_t_min=int(t[mask][0]) if mask.any() else "",
                                        used_t_max=int(t[mask][-1]) if mask.any() else "",
                                        n_replicas=len(trajectory), n_points=int(mask.sum()),
                                        alpha=alpha, bootstrap_low=lo, bootstrap_high=hi,
                                        max_length_over_L=float(np.max((mean/L)[mask])) if mask.any() else ""))
        axes[0].set(xscale="log", yscale="log", xlabel="Sweeps after quench", ylabel="Mean length (sites)", title="Growth (replica SE)")
        axes[1].set(xscale="log", ylabel=r"$\ell/L$", xlabel="Sweeps after quench", title="Domain fraction")
        axes[1].axhline(LENGTH_FRACTION, ls=":", color="black", label="0.15 sensitivity cut")
        axes[2].set(xscale="log", xlabel="Sweeps after quench", ylabel="Local effective slope", title="Moving nine-point log fit")
        axes[2].axhline(1/3, ls=":", color="black", label="1/3 reference")
        for axis in axes:
            axis.grid(alpha=.2)
            axis.legend(fontsize=8)
        fig.suptitle(f"Model B, c={c}; 16 independent replicas per size")
        fig.savefig(output / f"main_extension_c{ci}.png", dpi=180)
        plt.close(fig)
    for filename, rows in (("fit_windows.csv", records), ("ensemble_lengths.csv", values)):
        with (output / filename).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
        campaign_manifest_sha256=sha(manifest_path), input_sha256=hashes,
        primary_windows=WINDOWS, sensitivity_length_fraction=LENGTH_FRACTION,
        bootstrap_unit="whole independent replica", bootstrap_draws=500,
        interpretation="Finite-window effective slopes. A size effect must be assessed at matched times; visual curve overlap alone is insufficient."), indent=2) + "\n")
    return output / "fit_windows.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(analyse(args.campaign_folder, args.output))
