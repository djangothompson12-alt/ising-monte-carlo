"""Plot regular-solution phase-diagram guides from Model B couplings.

This is a thermodynamic interpretation of the conserved Kawasaki model, not
an additional simulation.  With the lattice-gas identification ``c = (1+m)/2``,
an unlike bond costs 2 J_d more than a like bond in direction ``d``.  On the
square lattice this gives the Bragg--Williams regular-solution free energy

    f(c, T) = k_B T [c ln c + (1-c) ln(1-c)] + Omega c(1-c),
    Omega = 4 (Jx + Jy).

The spinodal is where d^2 f / dc^2 = 0:

    k_B T_s(c) = 8 (Jx + Jy) c(1-c).

The original figure plots the mean-field spinodal. A separate, newly derived
figure adds the symmetric regular-solution binodal via the common-tangent
condition f'(c)=0 at coexistence compositions c and 1-c. Neither curve is the
exact two-dimensional Ising coexistence curve or a measured Fe--Cr diagram.
The binodal distinguishes local stability from global two-phase preference
*within the Bragg--Williams approximation*; it does not establish a physical
nucleation mechanism in a simulated or real alloy. A separate comparison uses
the exact thermodynamic-limit spontaneous magnetisation of the zero-field
square-lattice Ising model to locate its coexistence compositions. That exact
result does not supply an exact spinodal or finite-time kinetics.
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
FULL_PHASE_OUTPUT_PATH = Path(__file__).parent / "figures" / "fig_regular_solution_binodal_spinodal.png"
EXACT_COMPARISON_OUTPUT_PATH = Path(__file__).parent / "figures" / "fig_exact_vs_meanfield_coexistence.png"
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


def regular_solution_free_energy(c: np.ndarray | float, T: float,
                                 Jx: float, Jy: float) -> np.ndarray:
    """Symmetric Bragg--Williams mixing free energy per site, with k_B=1."""
    fraction = np.asarray(c, dtype=float)
    if np.any((fraction < 0.0) | (fraction > 1.0)) or T < 0:
        raise ValueError("Composition must be within [0,1] and T nonnegative")
    with np.errstate(divide="ignore", invalid="ignore"):
        ideal = np.where(fraction > 0, fraction * np.log(fraction), 0.0)
        ideal += np.where(fraction < 1, (1-fraction) * np.log1p(-fraction), 0.0)
    return T * ideal + regular_solution_omega(Jx, Jy) * fraction * (1-fraction)


def regular_solution_chemical_potential(c: np.ndarray | float, T: float,
                                         Jx: float, Jy: float) -> np.ndarray:
    """Derivative of the symmetric mixing free energy for 0<c<1."""
    fraction = np.asarray(c, dtype=float)
    if np.any((fraction <= 0.0) | (fraction >= 1.0)) or T < 0:
        raise ValueError("Chemical potential requires 0<c<1 and T nonnegative")
    return T * np.log(fraction / (1-fraction)) + regular_solution_omega(Jx, Jy) * (1-2*fraction)


def binodal_temperature(c: np.ndarray | float, Jx: float, Jy: float) -> np.ndarray:
    """Symmetric regular-solution coexistence curve, in reduced temperature.

    Symmetry gives a horizontal common tangent between c and 1-c. Solving
    f'(c)=0 yields T_b=Omega(1-2c)/ln((1-c)/c), with a continuous
    T_b(1/2)=Omega/2 limit and zero-temperature endpoints. ``arctanh`` gives
    a numerically stable equivalent away from the critical composition.
    """
    fraction = np.asarray(c, dtype=float)
    if np.any((fraction < 0.0) | (fraction > 1.0)):
        raise ValueError("Composition must be within [0,1]")
    distance = np.abs(1.0 - 2.0 * fraction)
    omega = regular_solution_omega(Jx, Jy)
    with np.errstate(divide="ignore", invalid="ignore"):
        temperature = np.where(distance == 0.0, omega / 2.0,
                               omega * distance / (2.0 * np.arctanh(distance)))
    return temperature


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


def exact_spontaneous_magnetization(T: np.ndarray | float, Jx: float,
                                    Jy: float) -> np.ndarray:
    """Infinite-lattice zero-field 2D Ising magnetisation below exact Tc.

    Onsager--Yang: m0=[1-(sinh(2Jx/T)sinh(2Jy/T))^-2]^(1/8).
    At or above Tc it is zero. This is equilibrium, not Kawasaki kinetics.
    The code uses k_B=1 and positive ferromagnetic nearest-neighbour couplings.
    """
    temperature = np.asarray(T, dtype=float)
    if Jx <= 0 or Jy <= 0 or np.any(~np.isfinite(temperature)) or np.any(temperature < 0):
        raise ValueError("Positive couplings and finite nonnegative T are required")
    critical = anisotropic_critical_temperature(Jx, Jy)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        product = np.sinh(2.0 * Jx / temperature) * np.sinh(2.0 * Jy / temperature)
        radicand = 1.0 - product ** -2
        magnetization = np.maximum(radicand, 0.0) ** 0.125
    return np.where(temperature >= critical, 0.0, magnetization)


def exact_coexistence_compositions(T: np.ndarray | float, Jx: float,
                                   Jy: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (c_low,c_high)=(1∓m0)/2 for the infinite 2D lattice.

    At and above Tc, both values are 0.5 and there is no two-phase interval.
    Fixed-composition systems between the two values favour phase coexistence
    in the thermodynamic limit; finite systems can behave differently.
    """
    magnetization = exact_spontaneous_magnetization(T, Jx, Jy)
    return (1.0 - magnetization) / 2.0, (1.0 + magnetization) / 2.0


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
    assert np.isclose(binodal_temperature(0.5, 1.0, 1.0), 4.0)
    assert np.isclose(binodal_temperature(0.0, 1.0, 1.0), 0.0)
    for fraction in (0.06, 0.10, 0.15, 0.25, 0.40):
        coexistence = float(binodal_temperature(fraction, 1.0, 1.0))
        assert float(spinodal_temperature(fraction, 1.0, 1.0)) < coexistence
        assert np.isclose(regular_solution_chemical_potential(fraction, coexistence, 1.0, 1.0), 0.0)
        assert np.isclose(regular_solution_free_energy(fraction, coexistence, 1.0, 1.0),
                          regular_solution_free_energy(1.0-fraction, coexistence, 1.0, 1.0))


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


def make_full_phase_figure(output_path: Path = FULL_PHASE_OUTPUT_PATH) -> Path:
    """Render the isotropic mean-field binodal and spinodal, preserving the old plot."""
    validate_mapping()
    _apply_publication_style()
    c = np.linspace(0.0001, 0.5, 900)
    spinodal = spinodal_temperature(c, 1.0, 1.0)
    binodal = binodal_temperature(c, 1.0, 1.0)
    final_temperature = 0.65 * anisotropic_critical_temperature(1.0, 1.0)
    unstable = CONCENTRATIONS[spinodal_temperature(CONCENTRATIONS, 1.0, 1.0) > final_temperature]
    metastable = CONCENTRATIONS[(spinodal_temperature(CONCENTRATIONS, 1.0, 1.0) < final_temperature)
                                & (binodal_temperature(CONCENTRATIONS, 1.0, 1.0) > final_temperature)]

    fig, ax = plt.subplots(figsize=(7.2, 5.0), constrained_layout=True)
    ax.fill_between(c, 0, spinodal, color="#c6dbef", alpha=0.75,
                    label="Locally unstable (mean field)")
    ax.fill_between(c, spinodal, binodal, color="#fdd0a2", alpha=0.65,
                    label="Metastable (mean field)")
    ax.plot(c, binodal, color="#ad4f00", lw=2.1, label="Binodal / coexistence")
    ax.plot(c, spinodal, color="#2171b5", lw=2.1, label="Spinodal / zero curvature")
    ax.axhline(final_temperature, color="#5b6269", lw=1.0, ls=":",
               label=rf"Isotropic finish: $0.65T_c={final_temperature:.3f}$")
    ax.scatter(unstable, np.full_like(unstable, final_temperature), s=49, marker="v",
               color="#08519c", zorder=5, label="Simulated finishes: unstable on this guide")
    ax.scatter(metastable, np.full_like(metastable, final_temperature), s=49, marker="D",
               color="#b34d00", zorder=5, label="Simulated finishes: metastable on this guide")
    for fraction in CONCENTRATIONS:
        ax.annotate(f"{fraction:.2f}", (fraction, final_temperature),
                    xytext=(0, 9), textcoords="offset points", ha="center", fontsize=7.6)
    ax.set(xlim=(0, 0.52), ylim=(0, 4.4),
           xlabel=r"Fraction of $+1$ sites, $c$", ylabel=r"Reduced temperature, $T$ ($J/k_B$)",
           title="Symmetric regular solution: coexistence versus instability")
    ax.legend(loc="lower right", fontsize=7.8)
    ax.text(0.02, 0.98,
            "Bragg–Williams approximation only; not exact 2D Ising or a Fe–Cr diagram.\n"
            "Metastability here does not prove a nucleation mechanism in the simulation.",
            transform=ax.transAxes, ha="left", va="top", fontsize=7.6,
            bbox={"facecolor": "white", "edgecolor": "0.7", "alpha": 0.92})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def make_exact_comparison_figure(output_path: Path = EXACT_COMPARISON_OUTPUT_PATH) -> Path:
    """Compare the exact 2D coexistence boundary with mean-field guides."""
    _apply_publication_style()
    exact_tc = anisotropic_critical_temperature(1.0, 1.0)
    temperature = np.linspace(0.0, exact_tc, 1200)
    low_composition, _ = exact_coexistence_compositions(temperature, 1.0, 1.0)
    composition = np.linspace(0.0, 0.5, 1200)
    final_temperature = 0.65 * exact_tc

    fig, ax = plt.subplots(figsize=(7.2, 5.0), constrained_layout=True)
    ax.fill_betweenx(temperature, low_composition, 0.5,
                     color="#dcebd9", alpha=0.75,
                     label="Two-phase equilibrium (exact, infinite 2D)")
    ax.plot(low_composition, temperature, color="#247a44", lw=2.3,
            label="Exact 2D coexistence boundary")
    ax.plot(composition, binodal_temperature(composition, 1.0, 1.0),
            color="#ad4f00", lw=1.8, ls="--", label="Regular-solution binodal (mean field)")
    ax.plot(composition, spinodal_temperature(composition, 1.0, 1.0),
            color="#2171b5", lw=1.6, ls=":", label="Regular-solution spinodal (mean field only)")
    ax.axhline(final_temperature, color="#505963", lw=1.1, ls="-.",
               label=rf"Study quench: $0.65T_c={final_temperature:.3f}$")
    ax.scatter(CONCENTRATIONS, np.full_like(CONCENTRATIONS, final_temperature),
               color="#443d70", marker="v", s=38, zorder=5, label="Studied compositions")
    for fraction in CONCENTRATIONS:
        ax.annotate(f"{fraction:.2f}", (fraction, final_temperature),
                    xytext=(0, 8), textcoords="offset points", ha="center", fontsize=7.5)
    ax.set(xlim=(0, 0.52), ylim=(0, 4.3),
           xlabel=r"Fraction of $+1$ sites, $c$", ylabel=r"Reduced temperature, $T$ ($J/k_B$)",
           title="Exact 2D coexistence versus the regular-solution approximation")
    ax.legend(loc="upper left", fontsize=7.7)
    ax.text(0.98, 0.04,
            "Exact green boundary is infinite-lattice equilibrium, not a kinetic prediction.\n"
            "No exact spinodal is inferred; neither curve is a measured alloy diagram.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5,
            bbox={"facecolor": "white", "edgecolor": "0.7", "alpha": 0.93})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    path = make_figure()
    full_path = make_full_phase_figure()
    comparison_path = make_exact_comparison_figure()
    print("Validated: Omega=8J and T_s(0.5)=4J for isotropic J=1.")
    print(f"Saved -> {path}")
    print(f"Saved -> {full_path}")
    print(f"Saved -> {comparison_path}")
