"""
visualizer.py
=============

Publication-quality figure generation for the 2D Ising Monte Carlo engine.

Produces two figures:
    fig1_phase_transitions.png -- |M|, E, Cv, chi vs. T (4-panel)
    fig2_spin_domains.png      -- lattice snapshots in the ferromagnetic,
                                   critical, and paramagnetic regimes
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from ising_engine import SimulationConfig, SweepResult, T_CRITICAL, sample_snapshot

_SPIN_CMAP = ListedColormap(["#1f4e79", "#f2f2f2"])  # -1 -> dark blue, +1 -> light


def _apply_publication_style() -> None:
    """Configure matplotlib rcParams for clean, publication-ready figures."""
    plt.rcParams.update(
        {
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "font.family": "serif",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 12,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "legend.frameon": False,
            "legend.fontsize": 10,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "axes.spines.top": True,
            "axes.spines.right": True,
            "mathtext.fontset": "cm",
        }
    )


def plot_phase_transitions(
    result: SweepResult,
    output_path: str | Path,
    T_c: float = T_CRITICAL,
) -> Path:
    """Render the 4-panel phase-transition figure (|M|, E, Cv, chi vs. T).

    Args:
        result: Output of `ising_engine.run_temperature_sweep`.
        output_path: Destination PNG path.
        T_c: Critical temperature to mark with a vertical dashed line.

    Returns:
        The resolved output path.
    """
    _apply_publication_style()
    output_path = Path(output_path)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    T = result.temperatures

    panels = [
        (axes[0, 0], result.magnetization, result.magnetization_err,
         r"Magnetization $\langle |M| \rangle$", "#1f4e79"),
        (axes[0, 1], result.energy, result.energy_err,
         r"Energy per spin $\langle E \rangle / J$", "#a63603"),
        (axes[1, 0], result.specific_heat, None,
         r"Specific Heat $C_v$", "#2e7d32"),
        (axes[1, 1], result.susceptibility, None,
         r"Susceptibility $\chi$", "#6a1b9a"),
    ]

    for ax, y, yerr, ylabel, color in panels:
        if yerr is not None:
            ax.errorbar(T, y, yerr=yerr, fmt="o-", ms=4, lw=1.2, capsize=2, color=color)
        else:
            ax.plot(T, y, "o-", ms=4, lw=1.2, color=color)
        ax.axvline(T_c, color="black", linestyle="--", linewidth=1, alpha=0.7)
        ax.set_xlabel(r"Temperature $T$ $(k_B = J = 1)$")
        ax.set_ylabel(ylabel)

    axes[0, 0].text(
        T_c, axes[0, 0].get_ylim()[1] * 0.95, r"$T_c \approx 2.269$",
        rotation=90, va="top", ha="right", fontsize=9, color="black",
    )

    fig.suptitle(
        r"2D Ising Model: Thermodynamic Observables vs. Temperature "
        r"($H = -J\sum_{\langle i,j\rangle}\sigma_i\sigma_j$)",
        fontsize=13,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_spin_domains(
    config: SimulationConfig,
    output_path: str | Path,
    temperatures: tuple[float, float, float] = (1.5, 2.27, 3.5),
    labels: tuple[str, str, str] = ("Ferromagnetic", "Critical", "Paramagnetic"),
    seed: int = 2026,
) -> Path:
    """Render equilibrium spin-lattice snapshots at three representative temperatures.

    Args:
        config: Simulation parameters (lattice size, equilibration length, coupling).
        output_path: Destination PNG path.
        temperatures: The three temperatures to snapshot.
        labels: Phase labels corresponding to each temperature.
        seed: Base random seed for reproducibility.

    Returns:
        The resolved output path.
    """
    _apply_publication_style()
    output_path = Path(output_path)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))

    for ax, T, label, offset in zip(axes, temperatures, labels, range(len(temperatures))):
        lattice = sample_snapshot(T, config, seed=seed + offset)
        ax.imshow(lattice, cmap=_SPIN_CMAP, vmin=-1, vmax=1, interpolation="nearest")
        ax.set_title(f"{label}\n" + r"$T = %.2f$" % T)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.8)

    fig.suptitle(
        rf"Equilibrium Spin Configurations, $L = {config.L}$"
        r" ($\sigma_i = \pm 1$; dark $= -1$, light $= +1$)",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path
