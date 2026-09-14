"""Plot the regular-solution spinodal implied by the Model B Ising couplings.

This is a thermodynamic interpretation of the conserved Kawasaki model, not
an additional simulation.  With the lattice-gas identification ``c = (1+m)/2``,
an unlike bond costs 2 J_d more than a like bond in direction ``d``.  On the
square lattice this gives the Bragg--Williams regular-solution free energy

    f(c, T) = k_B T [c ln c + (1-c) ln(1-c)] + Omega c(1-c),
    Omega = 4 (Jx + Jy).

The spinodal is where d^2 f / dc^2 = 0:

    k_B T_s(c) = 8 (Jx + Jy) c(1-c).

The script deliberately plots the mean-field regular-solution spinodal, not
the exact two-dimensional Ising coexistence curve.  Its role is to locate the
simulated quenches relative to the materials-science distinction between an
infinitesimally unstable mixture and an off-critical, nucleation-dominated
mixture.
"""

from __future__ import annotations

import os
from pathlib import Path

# Keep Matplotlib's cache with the project when the user home directory is
# unavailable (e.g. in a sandboxed CI or agent session).
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).parent / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_PATH = Path(__file__).parent / "figures" / "fig_regular_solution_spinodal.png"
CONCENTRATIONS = np.array([0.50, 0.35, 0.25, 0.15, 0.10, 0.06])


def regular_solution_omega(Jx: float, Jy: float) -> float:
    """Return Omega for the square-lattice Ising-to-regular-solution map.

    Temperatures and couplings use the repository convention k_B = 1.
    """
    return 4.0 * (Jx + Jy)


def spinodal_temperature(c: np.ndarray | float, Jx: float, Jy: float) -> np.ndarray:
    """Bragg--Williams spinodal temperature T_s(c), in the code's J/k_B units."""
    c_array = np.asarray(c, dtype=float)
    return 2.0 * regular_solution_omega(Jx, Jy) * c_array * (1.0 - c_array)


def anisotropic_critical_temperature(Jx: float, Jy: float) -> float:
    """Numerically solve the exact Onsager criticality condition.

    This small local implementation keeps the plotting script runnable with
    NumPy and Matplotlib alone; it matches the function in the Model B engine.
    """
    lo, hi = 0.05 * min(Jx, Jy), 50.0 * max(Jx, Jy)
    for _ in range(100):
        midpoint = 0.5 * (lo + hi)
        with np.errstate(over="ignore"):
            condition = np.sinh(2.0 * Jx / midpoint) * np.sinh(2.0 * Jy / midpoint) - 1.0
        if condition > 0.0:
            lo = midpoint
        else:
            hi = midpoint
    return 0.5 * (lo + hi)


def _apply_publication_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "legend.frameon": True,
            "legend.fontsize": 8.5,
        }
    )


def _plot_quench_arrow(ax: plt.Axes, c: float, T_initial: float, T_final: float, color: str, label: str) -> None:
    """Draw a labelled vertical quench arrow without obscuring the spinodal."""
    ax.annotate(
        "",
        xy=(c, T_final),
        xytext=(c, T_initial),
        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.8},
        zorder=5,
    )
    ax.scatter([c], [T_initial], marker="o", s=38, facecolor="white", edgecolor=color, lw=1.4, zorder=6)
    ax.scatter([c], [T_final], marker="v", s=42, color=color, zorder=6, label=label)


def validate_mapping() -> None:
    """Numerically check the limiting identities used in the manuscript."""
    assert np.isclose(regular_solution_omega(1.0, 1.0), 8.0)
    assert np.isclose(spinodal_temperature(0.5, 1.0, 1.0), 4.0)
    assert np.isclose(spinodal_temperature(0.5, 1.0, 0.5), 3.0)
    assert np.isclose(spinodal_temperature(0.0, 1.0, 1.0), 0.0)
    assert np.isclose(spinodal_temperature(1.0, 1.0, 1.0), 0.0)


def make_figure(output_path: Path = OUTPUT_PATH) -> Path:
    """Render the spinodal and mark the actual conserved-model quench paths."""
    validate_mapping()
    _apply_publication_style()

    isotropic_tc = anisotropic_critical_temperature(1.0, 1.0)
    anisotropic_tc = anisotropic_critical_temperature(1.0, 0.5)
    isotropic_T_initial, isotropic_T_final = 3.0 * isotropic_tc, 0.65 * isotropic_tc
    anisotropic_T_initial, anisotropic_T_final = 3.0 * anisotropic_tc, 0.65 * anisotropic_tc
    c = np.linspace(0.001, 0.999, 800)

    fig, ax = plt.subplots(figsize=(7.2, 4.9), constrained_layout=True)
    ax.fill_between(c, 0, spinodal_temperature(c, 1.0, 1.0), color="#c6dbef", alpha=0.55,
                    label="Isotropic Model B: spinodally unstable region")
    ax.plot(c, spinodal_temperature(c, 1.0, 1.0), color="#2171b5", lw=2.2,
            label=r"Isotropic spinodal: $T_s=16c(1-c)$")
    ax.plot(c, spinodal_temperature(c, 1.0, 0.5), color="#cb181d", lw=2.0, ls="--",
            label=r"Anisotropic baseline: $T_s=12c(1-c)$")

    # The six composition-sweep runs all share the same isotropic temperature path.
    ax.scatter(CONCENTRATIONS, np.full_like(CONCENTRATIONS, isotropic_T_initial), marker="o", s=28,
               facecolor="white", edgecolor="#084594", lw=1.1, zorder=5,
               label=r"Composition sweep: $\circ$ start, $\blacktriangledown$ finish")
    ax.scatter(CONCENTRATIONS, np.full_like(CONCENTRATIONS, isotropic_T_final), marker="v", s=34,
               color="#084594", zorder=5)
    ax.annotate("quench", xy=(0.035, isotropic_T_final), xytext=(0.035, isotropic_T_initial),
                ha="center", va="center", rotation=90, color="#084594", fontsize=8)
    ax.annotate("", xy=(0.055, isotropic_T_final), xytext=(0.055, isotropic_T_initial),
                arrowprops={"arrowstyle": "->", "color": "#084594", "lw": 1.4})

    _plot_quench_arrow(
        ax, 0.50, anisotropic_T_initial, anisotropic_T_final, "#a50f15",
        "Anisotropic kinetic quench",
    )
    ax.annotate(rf"$T_i={isotropic_T_initial:.3f}\to T_f={isotropic_T_final:.3f}$", xy=(0.06, 5.45),
                ha="center", va="center", rotation=90, color="#084594", fontsize=7.5)
    ax.annotate(rf"$T_i={anisotropic_T_initial:.3f}\to T_f={anisotropic_T_final:.3f}$", xy=(0.487, 3.0),
                ha="right", va="center", rotation=90, color="#a50f15", fontsize=7.5)

    ax.annotate("inside mean-field\nspinodal", xy=(0.29, 0.72), ha="center", color="#08519c", fontsize=9)
    ax.annotate("positive free-energy curvature\n(metastability also requires the binodal)", xy=(0.13, 3.35), ha="center",
                color="#4d4d4d", fontsize=8.5)
    ax.set(xlim=(0, 0.52), ylim=(0, 7.2), xlabel=r"A-atom concentration, $c$ (fraction of $+1$ spins)",
           ylabel=r"Temperature, $T$ ($J/k_B$)",
           title="Regular-solution spinodal mapped from the Ising coupling")
    ax.legend(loc="upper right", handlelength=2.3, fontsize=7.7)
    ax.text(
        0.99, 0.02,
        r"Bragg--Williams guide only: its $T_c^{\mathrm{RS}}=4J$ is not the exact"
        "\n"
        r"2D Ising $T_c=2.269J$. Model A is not plotted: composition is not conserved.",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=7.6,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "0.7", "alpha": 0.92},
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    path = make_figure()
    print("Validated: Omega=8J and T_s(0.5)=4J for isotropic J=1.")
    print(f"Saved -> {path}")
