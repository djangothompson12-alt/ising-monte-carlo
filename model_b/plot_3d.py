"""Render orthogonal slices of a cubic 3D Model B quench.

Example: ``python model_b/plot_3d.py --L 32 --sweeps 200``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

# This script writes a file; forcing a non-interactive backend makes it work
# on headless machines and avoids opening a desktop window during batch runs.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from model_b.kawasaki_3d_engine import CubicKawasakiConfig, run_quench_snapshot_3d
except ModuleNotFoundError:  # Direct execution from model_b/.
    from kawasaki_3d_engine import CubicKawasakiConfig, run_quench_snapshot_3d


def plot_orthogonal_slices(volume, title: str, output: Path) -> None:
    """Save central xy, xz and yz slices of a ``(z, y, x)`` spin volume."""
    mid = volume.shape[0] // 2
    slices = (volume[mid, :, :], volume[:, mid, :], volume[:, :, mid])
    labels = ("xy (z = centre)", "xz (y = centre)", "yz (x = centre)")
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.4), constrained_layout=True)
    for ax, plane, label in zip(axes, slices, labels):
        ax.imshow(plane, cmap="coolwarm", vmin=-1, vmax=1, interpolation="nearest")
        ax.set_title(label)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(title)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--L", type=int, default=32)
    parser.add_argument("--sweeps", type=int, default=200)
    parser.add_argument("--equilibrate", type=int, default=100)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--concentration", type=float, default=0.5)
    parser.add_argument("--Jx", type=float, default=1.0)
    parser.add_argument("--Jy", type=float, default=1.0)
    parser.add_argument("--Jz", type=float, default=1.0)
    parser.add_argument("--T-initial", type=float, default=8.0)
    parser.add_argument("--T-final", type=float, default=3.0)
    parser.add_argument("--out", type=Path, default=Path("model_b/figures/model_b_3d_slices.png"))
    args = parser.parse_args()
    config = CubicKawasakiConfig(
        L=args.L, Jx=args.Jx, Jy=args.Jy, Jz=args.Jz,
        T_initial=args.T_initial, T_final=args.T_final,
        concentration=args.concentration, eq_sweeps_initial=args.equilibrate, seed=args.seed,
    )
    volume = run_quench_snapshot_3d(config, args.sweeps)
    plot_orthogonal_slices(
        volume,
        f"3D Model B: L={args.L}, c={args.concentration:g}, t={args.sweeps} sweeps",
        args.out,
    )
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
