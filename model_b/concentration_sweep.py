"""
concentration_sweep.py
=======================

Tests the concentration-dependence prediction for conserved-order-parameter
(Model B / Kawasaki) coarsening from Bray's review [Adv. Phys. 43, 357
(1994)]: "the growth law is independent of the volume fraction of the
phases, but the scaling functions are not." Concretely:

  1. Domain-growth exponent universality. Isotropic (Jx = Jy = 1) Kawasaki
     quenches are run at a range of initial up-spin concentrations, from the
     critical, bicontinuous 50/50 quench down into the dilute, off-critical
     droplet/nucleation regime (below the ~15% volume fraction Bray cites as
     where the minority phase becomes disconnected droplets). L(t) ~ t^alpha
     is fitted at each concentration; the prediction under test is that
     alpha stays pinned near the Lifshitz-Slyozov value 1/3 across the whole
     range, even though the *morphology* changes qualitatively from a
     continuous interconnected network to isolated droplets.
  2. Droplet-size-distribution morphology. At the most dilute concentration,
     the actual droplet-size distribution is extracted at late time (via
     periodic connected-component labelling, pooling many independent
     replicas) and compared, after rescaling by the sample mean radius, to
     the closed-form Lifshitz-Slyozov-Wagner distribution g(u) for u = R/Rc.
     That closed form was originally derived in d = 3 with volume (R^3)
     conservation; here it is used as a *qualitative* reference shape (in
     particular its hallmark hard cutoff at u = 1.5, absent from generic
     unimodal distributions like a log-normal), not a claim that the d = 2
     lattice distribution must match its exponents exactly -- see the
     docstring of `kawasaki_engine.lsw_scaling_function` and the manuscript
     methods section for the caveat.

Anisotropy (Jx != Jy) is deliberately held fixed at 1 here so the
concentration effect isn't conflated with the directional-growth effect
already studied in `plot_kawasaki_kinetics.py`.

Usage:
    python model_b/concentration_sweep.py
    (or: cd model_b && python concentration_sweep.py)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from kawasaki_engine import (
    KawasakiConfig,
    KawasakiResult,
    droplet_size_distribution,
    lsw_scaling_function,
    run_quench_kinetics,
    run_quench_to_snapshot,
)

FIGURES_DIR = Path(__file__).parent / "figures"
RESULTS_DIR = Path(__file__).parent / "results"

#: Predicted growth exponent for conserved (Model B) order-parameter dynamics.
LIFSHITZ_SLYOZOV_EXPONENT = 1.0 / 3.0

#: Sweeps to discard as pre-domain-formation transient (matches the other kinetics scripts).
FIT_T_MIN = 2.0

#: Fraction of r_max = L/2 beyond which C(r,t)=0.5 crossings become unreliable.
FIT_L_MAX_FRACTION_OF_R_MAX = 0.3

#: Up-spin concentrations swept, from critical (bicontinuous) to dilute
#: (isolated droplets). 0.15 and below sit under Bray's ~15% volume-fraction
#: threshold for disconnected droplet morphology.
CONCENTRATIONS: list[float] = [0.50, 0.35, 0.25, 0.15, 0.10, 0.06]

#: Concentration singled out for the droplet-size-distribution vs. LSW comparison.
DILUTE_CONCENTRATION_FOR_LSW = 0.06

#: Independent replicas pooled for droplet-size-distribution statistics
#: (separate from, and larger than, n_replicas in SWEEP_CONFIG, since this
#: only needs final-snapshot morphology, not the full correlation-function
#: time series).
N_SNAPSHOT_REPLICAS = 30

#: Minimum droplet size (lattice sites) kept in the LSW comparison --
#: excludes single-site thermal noise rather than genuine coarsened droplets.
MIN_DROPLET_SIZE = 4

#: Shared simulation scale for every concentration in the sweep.
SWEEP_CONFIG_KWARGS = dict(
    L=96, Jx=1.0, Jy=1.0, n_replicas=12, max_sweeps=8000, n_time_samples=26,
    eq_sweeps_initial=150,
)


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
            "legend.fontsize": 8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "mathtext.fontset": "cm",
        }
    )


def fit_power_law(
    t: np.ndarray, L: np.ndarray, t_min: float = FIT_T_MIN, L_max: float | None = None,
) -> tuple[float, float, np.ndarray]:
    """Fit log L = alpha * log t + log A by least squares over the genuine
    scaling regime -- same methodology as `plot_kawasaki_kinetics.py`."""
    mask = np.isfinite(L) & (L > 0) & (t > t_min)
    if L_max is not None:
        mask &= L <= L_max
    if mask.sum() < 2:
        return float("nan"), float("nan"), mask
    alpha, log_A = np.polyfit(np.log(t[mask]), np.log(L[mask]), 1)
    return alpha, float(np.exp(log_A)), mask


def run_sweep() -> dict[float, KawasakiResult]:
    """Run the isotropic Kawasaki quench at each concentration in CONCENTRATIONS."""
    results: dict[float, KawasakiResult] = {}
    for c in CONCENTRATIONS:
        print(f"  concentration={c:.2f} ...", flush=True)
        config = KawasakiConfig(concentration=c, seed=123, **SWEEP_CONFIG_KWARGS)
        results[c] = run_quench_kinetics(config)
    return results


def save_exponent_csv(
    concentrations: list[float], alphas: np.ndarray, alpha_errs: np.ndarray, path: Path
) -> None:
    header = "concentration,fitted_exponent,fitted_exponent_stderr"
    data = np.column_stack([concentrations, alphas, alpha_errs])
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.6f")


def save_droplet_sizes_csv(sizes: np.ndarray, path: Path) -> None:
    np.savetxt(path, sizes, header="droplet_size_lattice_sites", comments="", fmt="%d")


def plot_exponent_universality(
    results: dict[float, KawasakiResult],
    fits: dict[float, tuple[float, float, np.ndarray]],
    concentrations: list[float],
    alphas: np.ndarray,
    alpha_errs: np.ndarray,
    output_path: Path,
) -> Path:
    """Two-panel figure: (left) L(t) collapse at every concentration with the
    t^(1/3) reference; (right) fitted exponent vs. concentration against the
    concentration-independent prediction."""
    _apply_publication_style()
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 5.5))

    cmap = plt.cm.viridis(np.linspace(0.05, 0.9, len(concentrations)))
    for c, color in zip(concentrations, cmap):
        result = results[c]
        alpha, A, mask = fits[c]
        L = 0.5 * (result.domain_size_x + result.domain_size_y)
        L_err = 0.5 * (result.domain_size_x_err + result.domain_size_y_err)
        ax_left.errorbar(
            result.t[mask], L[mask], yerr=L_err[mask], fmt="o", ms=4, capsize=1.5,
            color=color, zorder=3, label=rf"$c={c:.2f}$ ($\alpha={alpha:.3f}$)",
        )

    t_ref = np.array([FIT_T_MIN, SWEEP_CONFIG_KWARGS["max_sweeps"]])
    ref_result = results[0.50]
    ref_alpha, ref_A, ref_mask = fits[0.50]
    ref_L = 0.5 * (ref_result.domain_size_x + ref_result.domain_size_y)
    reference_A = ref_L[ref_mask][0] / (ref_result.t[ref_mask][0] ** LIFSHITZ_SLYOZOV_EXPONENT)
    ax_left.plot(
        t_ref, reference_A * t_ref**LIFSHITZ_SLYOZOV_EXPONENT, "k--", linewidth=1.6, zorder=1,
        label=r"Lifshitz-Slyozov: $L(t)\propto t^{1/3}$",
    )
    ax_left.set_xscale("log")
    ax_left.set_yscale("log")
    ax_left.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax_left.set_ylabel(r"Domain size $L(t)$ (lattice units)")
    ax_left.set_title("Domain growth across concentrations")
    ax_left.legend(loc="upper left", fontsize=7)

    ax_right.errorbar(
        concentrations, alphas, yerr=alpha_errs, fmt="o", ms=7, capsize=3,
        color="#1f4e79", zorder=3,
    )
    ax_right.axhline(
        LIFSHITZ_SLYOZOV_EXPONENT, color="#2e7d32", linestyle=":", linewidth=1.8,
        label=r"Lifshitz-Slyozov prediction: $1/3$ (concentration-independent)",
    )
    ax_right.axvline(
        0.15, color="#999999", linestyle="--", linewidth=1.0,
        label="Bray's disconnected-droplet threshold ($c \\lesssim 0.15$)",
    )
    ax_right.set_xlabel("Initial concentration $c$ (fraction of $+1$ spins)")
    ax_right.set_ylabel(r"Fitted growth exponent $\alpha$")
    ax_right.set_title("Growth exponent vs. concentration")
    ax_right.legend(loc="lower left", fontsize=8)
    ax_right.set_ylim(0.0, 0.6)

    fig.suptitle(
        "Model B (Kawasaki): domain-growth exponent is pinned by the conservation "
        "law, not by concentration",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_lsw_comparison(sizes: np.ndarray, concentration: float, output_path: Path) -> Path:
    """Histogram the measured droplet-radius distribution (rescaled by its
    own sample mean) against the closed-form LSW scaling function."""
    _apply_publication_style()

    radii = np.sqrt(sizes / np.pi)
    u_measured = radii / radii.mean()

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.hist(
        u_measured, bins=24, range=(0, 3.0), density=True, color="#1f4e79", alpha=0.6,
        edgecolor="white", linewidth=0.5,
        label=rf"Simulated droplets ($c={concentration:.2f}$, $n={len(sizes)}$)",
    )
    u_theory = np.linspace(0, 1.499, 400)
    ax.plot(
        u_theory, lsw_scaling_function(u_theory), "k-", linewidth=2.0,
        label="Lifshitz-Slyozov-Wagner theory $g(u)$",
    )
    ax.axvline(1.5, color="#a63603", linestyle="--", linewidth=1.2, label=r"LSW hard cutoff $u=3/2$")
    ax.set_xlabel(r"Rescaled droplet radius $u = R / \langle R \rangle$")
    ax.set_ylabel("Probability density")
    ax.set_title("Droplet-size distribution vs. LSW theory (dilute, off-critical quench)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_xlim(0, 3.0)

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    print("Running concentration sweep (Model B, isotropic Jx=Jy=1)...")
    results = run_sweep()

    r_max = SWEEP_CONFIG_KWARGS["L"] // 2
    L_max = FIT_L_MAX_FRACTION_OF_R_MAX * r_max

    fits: dict[float, tuple[float, float, np.ndarray]] = {}
    alphas = np.empty(len(CONCENTRATIONS))
    alpha_errs = np.empty(len(CONCENTRATIONS))
    for i, c in enumerate(CONCENTRATIONS):
        result = results[c]
        L = 0.5 * (result.domain_size_x + result.domain_size_y)
        alpha, A, mask = fit_power_law(result.t, L, L_max=L_max)
        fits[c] = (alpha, A, mask)
        alphas[i] = alpha
        print(f"  c={c:.2f}: alpha = {alpha:.4f} ({int(mask.sum())} pts used)")

    print("Estimating exponent uncertainty via error propagation through the log-log fit...")
    for i, c in enumerate(CONCENTRATIONS):
        # Re-deriving per-replica L(t) for a replica-resampling bootstrap
        # would require plumbing the raw replica array out of
        # run_quench_kinetics; instead, propagate the already-reported
        # standard error on L(t) itself through the log-log fit by
        # resampling L(t) within its error bars and refitting alpha.
        result = results[c]
        L = 0.5 * (result.domain_size_x + result.domain_size_y)
        L_err = 0.5 * (result.domain_size_x_err + result.domain_size_y_err)
        alpha, A, mask = fits[c]
        if mask.sum() >= 3:
            # Weighted-least-squares-style propagation: perturb log L within
            # its standard error and refit, repeated, to get alpha's std.
            rng = np.random.default_rng(hash(c) % (2**32))
            t_fit = result.t[mask]
            L_fit = L[mask]
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

    fig1_path = FIGURES_DIR / "fig_concentration_exponent_universality.png"
    plot_exponent_universality(results, fits, CONCENTRATIONS, alphas, alpha_errs, fig1_path)
    print(f"Saved figure -> {fig1_path}")

    print(
        f"\nDroplet-size-distribution vs. LSW theory at c={DILUTE_CONCENTRATION_FOR_LSW} "
        f"({N_SNAPSHOT_REPLICAS} pooled replicas)..."
    )
    lsw_config = KawasakiConfig(
        concentration=DILUTE_CONCENTRATION_FOR_LSW, seed=999, **SWEEP_CONFIG_KWARGS
    )
    target_sweep = SWEEP_CONFIG_KWARGS["max_sweeps"]
    all_sizes = []
    for rep in range(N_SNAPSHOT_REPLICAS):
        lattice = run_quench_to_snapshot(lsw_config, seed=lsw_config.seed + rep, target_sweep=target_sweep)
        sizes = droplet_size_distribution(lattice)
        all_sizes.append(sizes[sizes >= MIN_DROPLET_SIZE])
    all_sizes = np.concatenate(all_sizes)
    print(f"  pooled {len(all_sizes)} droplets (size >= {MIN_DROPLET_SIZE} sites)")

    save_droplet_sizes_csv(all_sizes, RESULTS_DIR / "droplet_sizes_dilute_quench.csv")
    fig2_path = FIGURES_DIR / "fig_droplet_size_distribution_lsw.png"
    plot_lsw_comparison(all_sizes, DILUTE_CONCENTRATION_FOR_LSW, fig2_path)
    print(f"Saved figure -> {fig2_path}")

    print("\nSummary:")
    for c, a, ae in zip(CONCENTRATIONS, alphas, alpha_errs):
        print(f"  c={c:.2f}: alpha = {a:.4f} +/- {ae:.4f}")
    print(f"  Lifshitz-Slyozov prediction: {LIFSHITZ_SLYOZOV_EXPONENT:.4f} (concentration-independent)")


if __name__ == "__main__":
    main()
