"""
concentration_sweep.py
=======================

Control/contrast experiment for `model_b/concentration_sweep.py`. Runs the
same range of initial up-spin concentrations through Model A's non-conserved
(single-spin-flip Metropolis) dynamics and fits the domain-growth exponent
at each one.

The comparison this sets up in the manuscript: curvature-driven, non-
conserved coarsening is governed by the same "domain collapses in time R^2"
argument regardless of which phase is in the minority (Bray, Adv. Phys. 43,
357 (1994), sec. 2.5), so the growth exponent is expected to stay pinned
near the Lifshitz-Allen-Cahn value 1/2 across concentration here too -- but
for a qualitatively different reason than Model B's conservation-law
argument, and with a qualitatively different fate: because single-spin-flip
dynamics does not conserve magnetization, an off-critical minority phase
here is transient and is eventually absorbed entirely (no stable droplet
population survives, unlike Model B's topologically protected minority
phase), which caps how long the measurable power-law regime lasts the more
dilute the initial concentration is.

Usage:
    python model_a/concentration_sweep.py
    (or: cd model_a && python concentration_sweep.py)
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

FIT_T_MIN = 2.0
FIT_L_MAX_FRACTION_OF_R_MAX = 0.3

#: Same concentrations as model_b/concentration_sweep.py, for a like-for-like comparison.
CONCENTRATIONS: list[float] = [0.50, 0.35, 0.25, 0.15, 0.10, 0.06]

SWEEP_CONFIG_KWARGS = dict(
    L=128, J=1.0, T_initial=5.0, T_final=1.5, n_replicas=10, max_sweeps=2500,
    n_time_samples=24, eq_sweeps_initial=100,
)


def fit_power_law(
    t: np.ndarray, L: np.ndarray, t_min: float = FIT_T_MIN, L_max: float | None = None,
) -> tuple[float, float, np.ndarray]:
    """Same methodology as model_a/plot_kinetics.py's fit_power_law."""
    mask = np.isfinite(L) & (L > 0) & (t > t_min)
    if L_max is not None:
        mask &= L <= L_max
    if mask.sum() < 2:
        return float("nan"), float("nan"), mask
    alpha, log_A = np.polyfit(np.log(t[mask]), np.log(L[mask]), 1)
    return alpha, float(np.exp(log_A)), mask


def run_sweep() -> dict[float, QuenchResult]:
    results: dict[float, QuenchResult] = {}
    for c in CONCENTRATIONS:
        print(f"  concentration={c:.2f} ...", flush=True)
        config = QuenchConfig(concentration=c, seed=123, **SWEEP_CONFIG_KWARGS)
        results[c] = run_quench_kinetics(config)
    return results


def save_exponent_csv(
    concentrations: list[float], alphas: np.ndarray, alpha_errs: np.ndarray, path: Path
) -> None:
    header = "concentration,fitted_exponent,fitted_exponent_stderr"
    data = np.column_stack([concentrations, alphas, alpha_errs])
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.6f")


def plot_exponent_vs_concentration(
    results: dict[float, QuenchResult],
    fits: dict[float, tuple[float, float, np.ndarray]],
    concentrations: list[float],
    alphas: np.ndarray,
    alpha_errs: np.ndarray,
    output_path: Path,
) -> Path:
    _apply_publication_style()
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 5.5))

    cmap = plt.cm.plasma(np.linspace(0.05, 0.85, len(concentrations)))
    for c, color in zip(concentrations, cmap):
        result = results[c]
        alpha, A, mask = fits[c]
        ax_left.errorbar(
            result.t[mask], result.domain_size[mask], yerr=result.domain_size_err[mask],
            fmt="o", ms=4, capsize=1.5, color=color, zorder=3,
            label=rf"$c={c:.2f}$ ($\alpha={alpha:.3f}$)",
        )

    ref_result = results[0.50]
    ref_alpha, ref_A, ref_mask = fits[0.50]
    t_ref = np.array([FIT_T_MIN, SWEEP_CONFIG_KWARGS["max_sweeps"]])
    reference_A = (
        ref_result.domain_size[ref_mask][0] / (ref_result.t[ref_mask][0] ** LIFSHITZ_ALLEN_EXPONENT)
    )
    ax_left.plot(
        t_ref, reference_A * t_ref**LIFSHITZ_ALLEN_EXPONENT, "k--", linewidth=1.6, zorder=1,
        label=r"Lifshitz-Allen-Cahn: $L(t)\propto t^{1/2}$",
    )
    ax_left.set_xscale("log")
    ax_left.set_yscale("log")
    ax_left.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax_left.set_ylabel(r"Domain size $L(t)$ (lattice units)")
    ax_left.set_title("Domain growth across concentrations")
    ax_left.legend(loc="upper left", fontsize=7)

    ax_right.errorbar(
        concentrations, alphas, yerr=alpha_errs, fmt="o", ms=7, capsize=3, color="#a63603", zorder=3,
    )
    ax_right.axhline(
        LIFSHITZ_ALLEN_EXPONENT, color="#2e7d32", linestyle=":", linewidth=1.8,
        label=r"Lifshitz-Allen-Cahn prediction: $1/2$",
    )
    ax_right.set_xlabel("Initial concentration $c$ (fraction of $+1$ spins)")
    ax_right.set_ylabel(r"Fitted growth exponent $\alpha$")
    ax_right.set_title("Growth exponent vs. concentration")
    ax_right.legend(loc="lower left", fontsize=8)
    ax_right.set_ylim(0.0, 0.8)

    fig.suptitle(
        "Model A (non-conserved): curvature-driven coarsening is also concentration-independent",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    print("Running concentration sweep (Model A, Metropolis single-spin-flip)...")
    results = run_sweep()

    r_max = SWEEP_CONFIG_KWARGS["L"] // 2
    L_max = FIT_L_MAX_FRACTION_OF_R_MAX * r_max

    fits: dict[float, tuple[float, float, np.ndarray]] = {}
    alphas = np.empty(len(CONCENTRATIONS))
    alpha_errs = np.empty(len(CONCENTRATIONS))
    for i, c in enumerate(CONCENTRATIONS):
        result = results[c]
        alpha, A, mask = fit_power_law(result.t, result.domain_size, L_max=L_max)
        fits[c] = (alpha, A, mask)
        alphas[i] = alpha
        print(f"  c={c:.2f}: alpha = {alpha:.4f} ({int(mask.sum())} pts used)")

        L_err = result.domain_size_err
        if mask.sum() >= 3:
            rng = np.random.default_rng(hash(c) % (2**32))
            t_fit = result.t[mask]
            L_fit = result.domain_size[mask]
            L_err_fit = np.where(L_err[mask] > 0, L_err[mask], 0.05 * L_fit)
            boot_alphas = []
            for _ in range(300):
                L_sample = np.clip(L_fit + rng.normal(0, L_err_fit), 1e-6, None)
                a, _ = np.polyfit(np.log(t_fit), np.log(L_sample), 1)
                boot_alphas.append(a)
            alpha_errs[i] = float(np.std(boot_alphas))
        else:
            alpha_errs[i] = float("nan")

    save_exponent_csv(
        CONCENTRATIONS, alphas, alpha_errs, RESULTS_DIR / "concentration_exponent_sweep.csv"
    )
    print(f"Saved -> {RESULTS_DIR / 'concentration_exponent_sweep.csv'}")

    fig_path = FIGURES_DIR / "fig_concentration_exponent.png"
    plot_exponent_vs_concentration(results, fits, CONCENTRATIONS, alphas, alpha_errs, fig_path)
    print(f"Saved figure -> {fig_path}")

    print("\nSummary:")
    for c, a, ae in zip(CONCENTRATIONS, alphas, alpha_errs):
        print(f"  c={c:.2f}: alpha = {a:.4f} +/- {ae:.4f}")
    print(f"  Lifshitz-Allen-Cahn prediction: {LIFSHITZ_ALLEN_EXPONENT:.4f} (concentration-independent)")


if __name__ == "__main__":
    main()
