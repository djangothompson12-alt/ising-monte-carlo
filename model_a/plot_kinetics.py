"""
plot_kinetics.py
=================

Runs a non-equilibrium T_initial -> T_final quench through the Ising critical
point and produces a two-panel kinetics figure:

    (top)    Characteristic domain size L(t), extracted from the spatial spin
             autocorrelation function C(r, t), verifying the Lifshitz-Allen-Cahn
             domain-growth law L(t) ~ t^(1/2) with a log-log power-law fit.
    (bottom) Entropy production rate S_dot(t) = -(1/T) * <dE>/dt, from the
             energy change of accepted Metropolis moves, showing irreversible
             dissipation decay as domain walls annihilate.

Usage:
    python model_a/plot_kinetics.py
    (or: cd model_a && python plot_kinetics.py)
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
    """Write post-quench time, domain size, and entropy production rate (with
    standard errors) to CSV."""
    header = (
        "t_sweeps,domain_size,domain_size_err,"
        "entropy_production_rate,entropy_production_rate_err"
    )
    data = np.column_stack([
        result.t,
        result.domain_size,
        result.domain_size_err,
        result.entropy_production,
        result.entropy_production_err,
    ])
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.8f")


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


def plot_kinetics_and_entropy(
    result: QuenchResult,
    output_path: Path,
    config: QuenchConfig,
    alpha: float,
    A: float,
    mask: np.ndarray,
) -> Path:
    """Render the two-panel domain-growth + entropy-production kinetics figure.

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

    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(7, 10))

    t, L, L_err = result.t, result.domain_size, result.domain_size_err
    excluded = ~mask & np.isfinite(L)

    # --- Top panel: domain growth L(t), log-log, with power-law fit ---
    ax_top.errorbar(
        t[mask], L[mask], yerr=L_err[mask],
        fmt="o", ms=5, capsize=2.5, color="#1f4e79", zorder=3,
        label=f"Simulation ($L={config.L}$, {config.n_replicas} replicas)",
    )
    if np.any(excluded):
        ax_top.errorbar(
            t[excluded], L[excluded], yerr=L_err[excluded],
            fmt="o", ms=5, mfc="none", mec="#999999", ecolor="#999999", capsize=2.5, zorder=2,
            label="Excluded (transient / finite-size limit)",
        )

    t_fit = np.array([t[mask].min(), t[mask].max()])
    ax_top.plot(
        t_fit, A * t_fit**alpha, "--", color="#a63603", linewidth=1.6, zorder=2,
        label=rf"Linear regression fit: $L(t) \propto t^{{{alpha:.4f}}}$",
    )

    reference_A = L[mask][0] / (t[mask][0] ** LIFSHITZ_ALLEN_EXPONENT)
    ax_top.plot(
        t_fit, reference_A * t_fit**LIFSHITZ_ALLEN_EXPONENT, ":", color="#2e7d32",
        linewidth=1.6, zorder=1,
        label=r"Lifshitz-Allen-Cahn: $L(t) \propto t^{1/2}$",
    )

    ax_top.set_xscale("log")
    ax_top.set_yscale("log")
    ax_top.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax_top.set_ylabel(r"Domain size $L(t)$ (lattice units)")
    ax_top.set_title(rf"Domain Growth: fitted exponent $\alpha = {alpha:.4f}$ (prediction: $0.5$)")
    ax_top.legend(loc="upper left", fontsize=9)

    # --- Bottom panel: entropy production rate S_dot(t) ---
    Sdot, Sdot_err = result.entropy_production, result.entropy_production_err
    finite = np.isfinite(Sdot)

    ax_bottom.errorbar(
        t[finite], Sdot[finite], yerr=Sdot_err[finite],
        fmt="o-", ms=4, lw=1, capsize=2, color="#6a1b9a",
    )
    ax_bottom.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    ax_bottom.set_xscale("log")
    ax_bottom.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax_bottom.set_ylabel(r"Entropy production rate $\dot{S}(t)$ (per spin, $k_B$ units)")
    ax_bottom.set_title(
        r"Irreversible Entropy Production: $\dot{S}(t) = -\dfrac{1}{T}\dfrac{\langle \Delta E \rangle}{dt}$"
    )

    fig.suptitle(
        rf"Quench Kinetics: $T={config.T_initial} \to T={config.T_final}$", fontsize=14
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
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

    fig_path = FIGURES_DIR / "fig3_kinetics_entropy.png"
    plot_kinetics_and_entropy(result, fig_path, config, alpha, A, mask)
    print(f"Saved figure -> {fig_path}")


if __name__ == "__main__":
    main()
