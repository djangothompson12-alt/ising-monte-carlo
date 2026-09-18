"""Fixed-selection morphology illustration from completed Kawasaki archives.

Uses replica 000, L=128, c=0.50/0.15 and the exact saved times 1069/200000.
The image is illustrative: no trajectory was selected by appearance, and the
four panels are not four statistically independent measurements.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

from research.imaging_benchmark import sha


TIMES = (1069, 200000)
INPUT_NAMES = ("c0_L128_rep000.npz", "c1_L128_rep000.npz")


def selected_states(path: Path) -> tuple[dict, list[np.ndarray]]:
    with np.load(path, allow_pickle=False) as archive:
        config = json.loads(archive["config"].item())
        times = np.asarray(archive["t"])
        snapshots = np.asarray(archive["snapshots"])
        states = []
        for target in TIMES:
            positions = np.flatnonzero(times == target)
            if len(positions) != 1:
                raise ValueError(f"Missing or duplicate saved time {target}: {path}")
            state = snapshots[int(positions[0])]
            if state.shape != (128, 128) or not set(np.unique(state)).issubset({-1, 1}):
                raise ValueError(f"Unexpected lattice shape or spin value: {path}")
            if int(state.sum()) != int(archive["magnetization"]):
                raise ValueError(f"Conservation mismatch in {path}")
            states.append(state.copy())
        return config, states


def make(archive_root: Path, output: Path) -> None:
    provenance = output.with_suffix(".json")
    if output.exists() or provenance.exists():
        raise FileExistsError("Choose unused output paths; prior figures are immutable")
    images = []
    configs = []
    source_hashes = {}
    for name in INPUT_NAMES:
        source = archive_root / name
        config, states = selected_states(source)
        if config["L"] != 128 or config["Jx"] != 1 or config["Jy"] != 1:
            raise ValueError("This figure requires isotropic L=128 runs")
        images.append(states)
        configs.append(config)
        source_hashes[name] = sha(source)
    if [config["concentration"] for config in configs] != [0.5, 0.15]:
        raise ValueError("Unexpected composition order")
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 7.5), layout="constrained")
    palette = ListedColormap(["#4b6073", "#e5a846"])
    for row, (config, states) in enumerate(zip(configs, images)):
        for col, (time, state) in enumerate(zip(TIMES, states)):
            axis = axes[row, col]
            axis.imshow(state, cmap=palette, vmin=-1, vmax=1, interpolation="nearest", origin="lower")
            axis.set_title(f"c={config['concentration']:.2f}, t={time:,} sweeps", fontsize=11)
            axis.set_xticks([])
            axis.set_yticks([])
            axis.set_xlabel("128 × 128 sites; one fixed seeded run", fontsize=8)
    fig.suptitle("Conserved compositions; different morphologies over time", fontsize=14)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    provenance.write_text(json.dumps(dict(
        status="illustrative fixed first replica; not ensemble inference or experimental microscopy",
        source_sha256=sha(Path(__file__)), raw_npz_sha256=source_hashes,
        selection="replica 000 at both compositions; L=128; exact archived times 1069 and 200000",
        seed_by_composition={str(config["concentration"]): config["seed"] for config in configs},
        temperature_final=configs[0]["T_final"],
        legend="blue-grey is spin -1; amber is spin +1; no physical units or alloy phases implied",
    ), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    make(args.archive_root, args.output)
