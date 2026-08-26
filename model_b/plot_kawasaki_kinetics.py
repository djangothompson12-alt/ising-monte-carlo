"""
plot_kawasaki_kinetics.py
==========================

Standalone launcher for the anisotropic Kawasaki (Model B, conserved order
parameter) quench: runs the simulation, saves the raw kinetics data, and
generates a two-panel publication-style figure -- directional domain growth
L_x(t) / L_y(t) with a Lifshitz-Slyozov t^(1/3) power-law fit on top, and the
entropy production rate S_dot(t) below.

This script and `kawasaki_engine.py` are fully self-contained and do not
import from, modify, or depend on any file outside `model_b/`.

Usage:
    python model_b/plot_kawasaki_kinetics.py
    (or: cd model_b && python plot_kawasaki_kinetics.py)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from kawasaki_engine import (
    KawasakiConfig,
    KawasakiResult,
    anisotropic_critical_temperature,
    run_quench_kinetics,
)

FIGURES_DIR = Path(__file__).parent / "figures"
RESULTS_DIR = Path(__file__).parent / "results"

#: Predicted growth exponent for conserved (Model B) order-parameter dynamics.
LIFSHITZ_SLYOZOV_EXPONENT = 1.0 / 3.0

#: Sweeps to discard as pre-domain-formation transient.
FIT_T_MIN = 2.0

#: Fraction of r_max = L/2 beyond which C(r,t)=0.5 crossings become unreliable.
FIT_L_MAX_FRACTION_OF_R_MAX = 0.3


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
            "legend.fontsize": 9,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "mathtext.fontset": "cm",
        }
    )


def save_kinetics_csv(result: KawasakiResult, path: Path) -> None:
    """Write post-quench time, directional domain sizes, and entropy
    production rate (with standard errors) to CSV."""
    header = (
        "t_sweeps,domain_size_x,domain_size_x_err,"
        "domain_size_y,domain_size_y_err,"
        "entropy_production_rate,entropy_production_rate_err"
    )
    data = np.column_stack([
        result.t,
        result.domain_size_x,
        result.domain_size_x_err,
        result.domain_size_y,
        result.domain_size_y_err,
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
    """Fit log L = alpha * log t + log A by least squares over the genuine
    scaling regime (see model_a/plot_kinetics.py for the same methodology
    applied to Model A).

    Returns:
        (alpha, A, mask): fitted growth exponent, prefactor, and the boolean
        mask of time points used in the fit.
    """
    mask = np.isfinite(L) & (L > 0) & (t > t_min)
    if L_max is not None:
        mask &= L <= L_max
    if mask.sum() < 2:
        return float("nan"), float("nan"), mask
    alpha, log_A = np.polyfit(np.log(t[mask]), np.log(L[mask]), 1)
    return alpha, float(np.exp(log_A)), mask


def plot_anisotropic_kinetics(
    result: KawasakiResult,
    output_path: Path,
    config: KawasakiConfig,
    alpha_x: float,
    A_x: float,
    mask_x: np.ndarray,
    alpha_y: float,
    A_y: float,
    mask_y: np.ndarray,
) -> Path:
    """Render the two-panel directional domain-growth + entropy-production figure."""
    _apply_publication_style()

    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(7, 10))

    t = result.t

    # --- Top panel: L_x(t) and L_y(t), log-log, with independent power-law fits ---
    ax_top.errorbar(
        t[mask_x], result.domain_size_x[mask_x], yerr=result.domain_size_x_err[mask_x],
        fmt="o", ms=5, capsize=2.5, color="#1f4e79", zorder=3,
        label=rf"$L_x(t)$ ($J_x={config.Jx}$)",
    )
    ax_top.errorbar(
        t[mask_y], result.domain_size_y[mask_y], yerr=result.domain_size_y_err[mask_y],
        fmt="s", ms=5, capsize=2.5, color="#a63603", zorder=3,
        label=rf"$L_y(t)$ ($J_y={config.Jy}$)",
    )

    if np.isfinite(alpha_x):
        t_fit_x = np.array([t[mask_x].min(), t[mask_x].max()])
        ax_top.plot(
            t_fit_x, A_x * t_fit_x**alpha_x, "--", color="#1f4e79", linewidth=1.4, zorder=2,
            label=rf"Fit: $L_x \propto t^{{{alpha_x:.3f}}}$",
        )
    if np.isfinite(alpha_y):
        t_fit_y = np.array([t[mask_y].min(), t[mask_y].max()])
        ax_top.plot(
            t_fit_y, A_y * t_fit_y**alpha_y, "--", color="#a63603", linewidth=1.4, zorder=2,
            label=rf"Fit: $L_y \propto t^{{{alpha_y:.3f}}}$",
        )

    t_ref = np.array([max(1.0, t.min()), t.max()])
    ref_anchor_t = t[mask_x][0] if np.any(mask_x) else t[0]
    ref_anchor_L = result.domain_size_x[mask_x][0] if np.any(mask_x) else result.domain_size_x[0]
    reference_A = ref_anchor_L / (ref_anchor_t ** LIFSHITZ_SLYOZOV_EXPONENT)
    ax_top.plot(
        t_ref, reference_A * t_ref**LIFSHITZ_SLYOZOV_EXPONENT, ":", color="#2e7d32",
        linewidth=1.6, zorder=1, label=r"Lifshitz-Slyozov: $L(t) \propto t^{1/3}$",
    )

    ax_top.set_xscale("log")
    ax_top.set_yscale("log")
    ax_top.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax_top.set_ylabel(r"Domain size (lattice units)")
    ax_top.set_title(
        rf"Anisotropic Domain Growth: $\alpha_x = {alpha_x:.3f}$, $\alpha_y = {alpha_y:.3f}$"
        "\n" r"(Model B / conserved-order-parameter prediction: $1/3$)"
    )
    ax_top.legend(loc="upper left", fontsize=8)

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
        r"Irreversible Entropy Production (Kawasaki exchange dynamics)"
    )

    fig.suptitle(
        rf"Model B Quench: $T_i={config.T_initial:.3f} \to T_f={config.T_final:.3f}$"
        rf"  ($T_c(J_x,J_y) \approx {anisotropic_critical_temperature(config.Jx, config.Jy):.3f}$)",
        fontsize=13,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    """Run the anisotropic Kawasaki quench, save the kinetics data, and plot."""
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    config = KawasakiConfig()
    tc = anisotropic_critical_temperature(config.Jx, config.Jy)
    print(
        f"Model B (Kawasaki) quench: Jx={config.Jx}, Jy={config.Jy}, "
        f"T_c(Jx,Jy)={tc:.4f}, {config.temperatures_str()}"
    )
    print(
        f"L={config.L}, {config.n_replicas} replicas, {config.max_sweeps} sweeps"
    )
    print("Running quench simulation (JIT-compiling on first call)...")
    result = run_quench_kinetics(config)

    csv_path = RESULTS_DIR / "kawasaki_kinetics.csv"
    save_kinetics_csv(result, csv_path)
    print(f"Saved -> {csv_path}")

    r_max = config.L // 2
    L_max = FIT_L_MAX_FRACTION_OF_R_MAX * r_max
    alpha_x, A_x, mask_x = fit_power_law(result.t, result.domain_size_x, L_max=L_max)
    alpha_y, A_y, mask_y = fit_power_law(result.t, result.domain_size_y, L_max=L_max)
    print(
        f"Fitted growth exponents: alpha_x = {alpha_x:.4f} ({int(mask_x.sum())}/{len(result.t)} pts), "
        f"alpha_y = {alpha_y:.4f} ({int(mask_y.sum())}/{len(result.t)} pts) "
        f"(Lifshitz-Slyozov prediction: {LIFSHITZ_SLYOZOV_EXPONENT:.4f})"
    )

    fig_path = FIGURES_DIR / "fig_anisotropic_kinetics.png"
    plot_anisotropic_kinetics(
        result, fig_path, config, alpha_x, A_x, mask_x, alpha_y, A_y, mask_y
    )
    print(f"Saved figure -> {fig_path}")


if __name__ == "__main__":
    main()
