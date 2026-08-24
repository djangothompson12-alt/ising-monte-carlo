"""
plot_kinetics.py
=================

Runs a non-equilibrium T_initial -> T_final quench through the Ising critical
point, extracts the characteristic domain size L(t) from the spatial spin
autocorrelation function C(r, t), and verifies the Lifshitz-Allen-Cahn
domain-growth law L(t) ~ t^(1/2) with a log-log power-law fit.

Usage:
    python plot_kinetics.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ising_engine import QuenchConfig, QuenchResult, run_quench_kinetics
from visualizer import _apply_publication_style

RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = Path(__file__).parent / "figures"

#: Predicted growth exponent for non-conserved (Model A) order-parameter dynamics.
LIFSHITZ_ALLEN_EXPONENT = 0.5

#: Sweeps to discard as pre-domain-formation transient (lattice-discreteness dominated).
FIT_T_MIN = 2.0

#: Fraction of r_max = L/2 beyond which C(r,t)=0.5 crossings become unreliable and the
#: periodic lattice's finite size measurably slows apparent domain growth.
FIT_L_MAX_FRACTION_OF_R_MAX = 0.3


def save_quench_csv(result: QuenchResult, path: Path) -> None:
    """Write post-quench time, domain size, and its standard error to CSV."""
    header = "t_sweeps,domain_size,domain_size_err"
    data = np.column_stack([result.t, result.domain_size, result.domain_size_err])
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.6f")


def fit_power_law(
    t: np.ndarray,
    L: np.ndarray,
    t_min: float = FIT_T_MIN,
    L_max: float | None = None,
) -> tuple[float, float, np.ndarray]:
    """Fit log L = alpha * log t + log A by least squares over the genuine scaling regime.

    Two classes of points are excluded from the fit: the pre-domain-formation
    transient (t <= t_min, dominated by lattice discreteness rather than
    curvature-driven coarsening), and late times where L(t) has grown large
    enough relative to r_max = L/2 that the C(r,t)=0.5 crossing becomes
    unreliable and periodic-image effects measurably slow the apparent growth.

    Args:
        t: Sweep-time values.
        L: Extracted domain sizes (may contain NaN where C(r,t) never crossed 0.5).
        t_min: Sweep counts at or below this are excluded as transient.
        L_max: Domain sizes above this are excluded as finite-size-limited.
            If None, no upper cutoff is applied.

    Returns:
        (alpha, A, mask): fitted growth exponent, prefactor, and the boolean
        mask of time points used in the fit.
    """
    mask = np.isfinite(L) & (L > 0) & (t > t_min)
    if L_max is not None:
        mask &= L <= L_max
    alpha, log_A = np.polyfit(np.log(t[mask]), np.log(L[mask]), 1)
    return alpha, float(np.exp(log_A)), mask


def plot_domain_growth(
    result: QuenchResult,
    output_path: Path,
    config: QuenchConfig,
    alpha: float,
    A: float,
    mask: np.ndarray,
) -> Path:
    """Render the publication-quality log-log L(t) vs. t domain-growth plot.

    Args:
        result: Output of `ising_engine.run_quench_kinetics`.
        output_path: Destination PNG path.
        config: The quench configuration used to produce `result`.
        alpha: Fitted power-law growth exponent.
        A: Fitted power-law prefactor.
        mask: Boolean mask of time points included in the fit (from `fit_power_law`).

    Returns:
        The resolved output path.
    """
    _apply_publication_style()

    fig, ax = plt.subplots(figsize=(7, 6))

    t, L, L_err = result.t, result.domain_size, result.domain_size_err
    excluded = ~mask & np.isfinite(L)

    ax.errorbar(
        t[mask], L[mask], yerr=L_err[mask],
        fmt="o", ms=5, capsize=2.5, color="#1f4e79", zorder=3,
        label=f"Simulation ($L={config.L}$, {config.n_replicas} replicas)",
    )
    if np.any(excluded):
        ax.errorbar(
            t[excluded], L[excluded], yerr=L_err[excluded],
            fmt="o", ms=5, mfc="none", mec="#999999", ecolor="#999999", capsize=2.5, zorder=2,
            label="Excluded (transient / finite-size limit)",
        )

    t_fit = np.array([t[mask].min(), t[mask].max()])
    ax.plot(
        t_fit, A * t_fit**alpha, "--", color="#a63603", linewidth=1.6, zorder=2,
        label=rf"Fit: $L(t) \propto t^{{{alpha:.3f}}}$",
    )

    reference_A = L[mask][0] / (t[mask][0] ** LIFSHITZ_ALLEN_EXPONENT)
    ax.plot(
        t_fit, reference_A * t_fit**LIFSHITZ_ALLEN_EXPONENT, ":", color="#2e7d32",
        linewidth=1.6, zorder=1,
        label=r"Lifshitz-Allen-Cahn: $L(t) \propto t^{1/2}$",
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax.set_ylabel(r"Characteristic domain size $L(t)$ (lattice units)")
    ax.set_title(
        rf"Domain Growth Kinetics: Quench $T={config.T_initial} \to T={config.T_final}$"
        "\n" rf"Fitted exponent $\alpha = {alpha:.3f}$ (Lifshitz-Allen-Cahn prediction: $0.5$)"
    )
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    """Run the quench, save the kinetics data, and generate the scaling plot."""
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    config = QuenchConfig()
    print(
        f"Quench kinetics: T={config.T_initial} -> T={config.T_final}, "
        f"L={config.L}, {config.n_replicas} replicas, {config.max_sweeps} sweeps"
    )
    print("Running quench simulation (JIT-compiling on first call)...")
    result = run_quench_kinetics(config)

    csv_path = RESULTS_DIR / "quench_kinetics.csv"
    save_quench_csv(result, csv_path)
    print(f"Saved -> {csv_path}")

    r_max = config.L // 2
    L_max = FIT_L_MAX_FRACTION_OF_R_MAX * r_max
    alpha, A, mask = fit_power_law(result.t, result.domain_size, t_min=FIT_T_MIN, L_max=L_max)
    n_used = int(mask.sum())
    print(
        f"Fitted growth exponent: alpha = {alpha:.4f} "
        f"(Lifshitz-Allen-Cahn prediction: {LIFSHITZ_ALLEN_EXPONENT}), "
        f"using {n_used}/{len(result.t)} time points"
    )

    fig_path = FIGURES_DIR / "fig3_domain_growth.png"
    plot_domain_growth(result, fig_path, config, alpha, A, mask)
    print(f"Saved figure -> {fig_path}")


if __name__ == "__main__":
    main()
