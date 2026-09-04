"""
comparative_analysis.py
========================

Side-by-side comparison of the domain-growth scaling laws from Model A
(non-conserved order parameter, Metropolis single-spin-flip dynamics) and
Model B (conserved order parameter, Kawasaki spin-exchange dynamics):
Lifshitz-Allen-Cahn L(t) ~ t^(1/2) for Model A vs. Lifshitz-Slyozov
L(t) ~ t^(1/3) for Model B, plotted on matching log-log axes so the two
different growth exponents are directly visually comparable.

Reads the CSV output each model's own kinetics script already produces --
does not re-run either simulation itself:
    model_a/results/quench_kinetics.csv    (from model_a/plot_kinetics.py)
    model_b/results/kawasaki_kinetics.csv  (from model_b/plot_kawasaki_kinetics.py)

If both models' concentration-sweep CSVs are also present --
    model_a/results/concentration_exponent_sweep.csv (from model_a/concentration_sweep.py)
    model_b/results/concentration_exponent_sweep.csv (from model_b/concentration_sweep.py)
-- this also produces the paper's unifying "phase diagram" figure: fitted
growth exponent vs. concentration for both dynamics side by side, testing
whether the exponent is set by the conservation law alone (Hohenberg-
Halperin Model A/B classification) rather than by composition/morphology.
That comparison is skipped (with a note, not an error) if those CSVs don't
exist yet, since it's an optional addition to the core comparison above.

Run the relevant scripts first if the CSVs don't exist yet.

Usage:
    python comparative_analysis.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
MODEL_A_CSV = ROOT / "model_a" / "results" / "quench_kinetics.csv"
MODEL_B_CSV = ROOT / "model_b" / "results" / "kawasaki_kinetics.csv"
MODEL_A_CONCENTRATION_CSV = ROOT / "model_a" / "results" / "concentration_exponent_sweep.csv"
MODEL_B_CONCENTRATION_CSV = ROOT / "model_b" / "results" / "concentration_exponent_sweep.csv"
FIGURES_DIR = ROOT / "figures"

#: Sweeps to discard as pre-domain-formation transient, matching both
#: models' own kinetics scripts' FIT_T_MIN convention.
FIT_T_MIN = 2.0

#: Predicted growth exponents (see model_a/plot_kinetics.py and
#: model_b/plot_kawasaki_kinetics.py for the per-model derivations).
LIFSHITZ_ALLEN_CAHN_EXPONENT = 0.5      # Model A: non-conserved order parameter
LIFSHITZ_SLYOZOV_EXPONENT = 1.0 / 3.0   # Model B: conserved order parameter


def _apply_publication_style() -> None:
    """Matplotlib rcParams matching model_a/visualizer.py's and
    model_b/plot_kawasaki_kinetics.py's own (independently duplicated)
    style. Kept as its own small copy here too, rather than importing
    either: this script is the one place that legitimately spans both
    models, but each model's own style helper is underscore-prefixed
    (module-private) by convention."""
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


def _load_csv(path: Path, generating_script: str) -> dict[str, np.ndarray]:
    """Load a kinetics CSV (as saved by np.savetxt(..., comments="") in
    both models' scripts, i.e. a plain header row with no leading '#')
    into a dict of column arrays keyed by column name."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found.\nRun `python {generating_script}` first to generate it."
        )
    data = np.genfromtxt(path, delimiter=",", names=True)
    return {name: data[name] for name in data.dtype.names}


def fit_power_law(
    t: np.ndarray, L: np.ndarray, t_min: float = FIT_T_MIN
) -> tuple[float, float, np.ndarray]:
    """Fit log L = alpha * log t + log A by least squares over t > t_min,
    excluding the pre-domain-formation transient -- same methodology as
    both models' own kinetics scripts' fit_power_law()."""
    mask = np.isfinite(L) & (L > 0) & (t > t_min)
    if mask.sum() < 2:
        return float("nan"), float("nan"), mask
    alpha, log_A = np.polyfit(np.log(t[mask]), np.log(L[mask]), 1)
    return alpha, float(np.exp(log_A)), mask


def _plot_panel(
    ax,
    t: np.ndarray,
    L: np.ndarray,
    L_err: np.ndarray,
    fit_alpha: float,
    fit_A: float,
    mask: np.ndarray,
    reference_exponent: float,
    reference_label: str,
    data_color: str,
    title: str,
) -> None:
    """Render one log-log domain-growth panel: simulation data, the fitted
    power law, and the theoretical reference slope -- same visual
    convention (anchor the reference line through the first fitted point)
    as model_a/plot_kinetics.py and model_b/plot_kawasaki_kinetics.py."""
    ax.errorbar(
        t[mask], L[mask], yerr=L_err[mask],
        fmt="o", ms=5, capsize=2.5, color=data_color, zorder=3, label="Simulation",
    )
    t_fit = np.array([t[mask].min(), t[mask].max()])
    ax.plot(
        t_fit, fit_A * t_fit**fit_alpha, "--", color="#a63603", linewidth=1.6, zorder=2,
        label=rf"Fit: $L(t) \propto t^{{{fit_alpha:.4f}}}$",
    )
    reference_A = L[mask][0] / (t[mask][0] ** reference_exponent)
    ax.plot(
        t_fit, reference_A * t_fit**reference_exponent, ":", color="#2e7d32", linewidth=1.6, zorder=1,
        label=reference_label,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Time $t$ (Monte Carlo sweeps)")
    ax.set_ylabel(r"Domain size $L(t)$ (lattice units)")
    ax.set_title(title)
    ax.legend(loc="upper left")


def plot_concentration_universality(output_path: Path) -> Path | None:
    """Fitted growth exponent vs. concentration, Model A and Model B
    overlaid on one axis: the paper's unifying result that the exponent is
    pinned by the conservation law (Hohenberg-Halperin Model A/B class), not
    by concentration or morphology, in either dynamics.

    Returns None (and prints a note instead of raising) if either sweep's
    CSV doesn't exist yet, since this figure is an optional addition on top
    of the core single-concentration comparison in `main()`.
    """
    if not (MODEL_A_CONCENTRATION_CSV.exists() and MODEL_B_CONCENTRATION_CSV.exists()):
        print(
            "Skipping concentration-universality figure: run "
            "model_a/concentration_sweep.py and model_b/concentration_sweep.py first."
        )
        return None

    a = np.genfromtxt(MODEL_A_CONCENTRATION_CSV, delimiter=",", names=True)
    b = np.genfromtxt(MODEL_B_CONCENTRATION_CSV, delimiter=",", names=True)

    _apply_publication_style()
    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    ax.errorbar(
        a["concentration"], a["fitted_exponent"], yerr=a["fitted_exponent_stderr"],
        fmt="o-", ms=7, capsize=3, color="#1f4e79",
        label="Model A (non-conserved)",
    )
    ax.errorbar(
        b["concentration"], b["fitted_exponent"], yerr=b["fitted_exponent_stderr"],
        fmt="s-", ms=7, capsize=3, color="#6a1b9a",
        label="Model B (conserved)",
    )
    ax.axhline(
        LIFSHITZ_ALLEN_CAHN_EXPONENT, color="#1f4e79", linestyle=":", linewidth=1.4, alpha=0.7,
        label=r"Lifshitz-Allen-Cahn: $1/2$",
    )
    ax.axhline(
        LIFSHITZ_SLYOZOV_EXPONENT, color="#6a1b9a", linestyle=":", linewidth=1.4, alpha=0.7,
        label=r"Lifshitz-Slyozov: $1/3$",
    )
    ax.axvline(0.15, color="#999999", linestyle="--", linewidth=1.0)

    ax.set_xlabel("Initial concentration $c$ (fraction of $+1$ spins)")
    ax.set_ylabel(r"Fitted growth exponent $\alpha$")
    ax.set_title(
        "Growth exponent vs. concentration: set by the conservation law,\n"
        "not by composition or morphology"
    )
    ax.legend(loc="lower left", fontsize=8)
    ax.set_ylim(0.0, 0.7)

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    _apply_publication_style()

    a = _load_csv(MODEL_A_CSV, "model_a/plot_kinetics.py")
    b = _load_csv(MODEL_B_CSV, "model_b/plot_kawasaki_kinetics.py")

    # Model B has independent Lx(t)/Ly(t) (anisotropic conserved dynamics);
    # averaged into one effective L(t) for a like-for-like comparison
    # against Model A's single isotropic domain size -- same convention as
    # model_b/solara_app.py's effective_growth_exponent().
    b_L = (b["domain_size_x"] + b["domain_size_y"]) / 2.0
    b_L_err = (b["domain_size_x_err"] + b["domain_size_y_err"]) / 2.0

    a_alpha, a_A, a_mask = fit_power_law(a["t_sweeps"], a["domain_size"])
    b_alpha, b_A, b_mask = fit_power_law(b["t_sweeps"], b_L)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5))

    _plot_panel(
        ax_a, a["t_sweeps"], a["domain_size"], a["domain_size_err"], a_alpha, a_A, a_mask,
        LIFSHITZ_ALLEN_CAHN_EXPONENT, r"Lifshitz-Allen-Cahn: $L(t) \propto t^{1/2}$",
        "#1f4e79", rf"Model A (non-conserved): fitted $\alpha = {a_alpha:.4f}$ (prediction: 0.5)",
    )
    _plot_panel(
        ax_b, b["t_sweeps"], b_L, b_L_err, b_alpha, b_A, b_mask,
        LIFSHITZ_SLYOZOV_EXPONENT, r"Lifshitz-Slyozov: $L(t) \propto t^{1/3}$",
        "#6a1b9a", rf"Model B (conserved): fitted $\alpha = {b_alpha:.4f}$ (prediction: 0.3333)",
    )

    fig.suptitle("Domain-Growth Scaling: Conserved vs. Non-Conserved Order Parameter", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    FIGURES_DIR.mkdir(exist_ok=True)
    output_path = FIGURES_DIR / "fig_comparative_scaling.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)

    print(f"Model A fitted growth exponent: alpha = {a_alpha:.4f} (Lifshitz-Allen-Cahn prediction: 0.5)")
    print(f"Model B fitted growth exponent: alpha = {b_alpha:.4f} (Lifshitz-Slyozov prediction: 0.3333)")
    print(f"Saved -> {output_path}")

    concentration_fig_path = FIGURES_DIR / "fig_concentration_universality.png"
    if plot_concentration_universality(concentration_fig_path):
        print(f"Saved -> {concentration_fig_path}")


if __name__ == "__main__":
    main()
