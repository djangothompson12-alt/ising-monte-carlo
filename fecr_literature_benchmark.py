"""Compare the conserved-model effective exponent with published Fe--Cr data.

This is deliberately a qualitative benchmark, not a physical calibration.
The simulation is a 2D nearest-neighbour lattice model measured in Monte Carlo
sweeps, whereas the experiment is a 3D alloy aged in hours.  The comparison is
useful because both report a dimensionless *effective growth exponent* during
an early/pre-asymptotic regime.

Experimental values are transcribed from Xu et al., "Structural
Characterization of Phase Separation in Fe-Cr: A Current Comparison of
Experimental Methods", Metallurgical and Materials Transactions A 47,
5942--5952 (2016), DOI: 10.1007/s11661-016-3800-4.  The paper reports
Q_m^{-1} ~ t^0.16 for the SANS decomposition wavelength and R ~ t^0.27 for
the Guinier particle radius in the alloy labelled 35Cr aged at 773 K (500 deg C).
Their Table I reports weight percent, not the model's site fraction. Compositions
and length observables are not matched; numerical proximity is not agreement.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).parent / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parent
SIMULATION_CSV = ROOT / "model_b" / "results" / "concentration_exponent_sweep.csv"
OUTPUT_PATH = ROOT / "figures" / "fig_fecr_literature_benchmark.png"
FECR_SANS_WAVELENGTH_EXPONENT = 0.16
FECR_GUINIER_RADIUS_EXPONENT = 0.27
LSW_ASYMPTOTIC_EXPONENT = 1.0 / 3.0


def load_simulated_c035(path: Path = SIMULATION_CSV) -> tuple[float, float]:
    """Return (exponent, fit stderr) for the c=0.35 Model B row."""
    data = np.genfromtxt(path, delimiter=",", names=True)
    index = int(np.argmin(np.abs(data["concentration"] - 0.35)))
    concentration = float(data["concentration"][index])
    if not np.isclose(concentration, 0.35):
        raise ValueError("The concentration sweep has no c=0.35 row.")
    return float(data["fitted_exponent"][index]), float(data["fitted_exponent_stderr"][index])


def make_figure(output_path: Path = OUTPUT_PATH) -> Path:
    """Render a citation-ready comparison with scope limitations on-figure."""
    simulated, simulated_err = load_simulated_c035()
    labels = [
        "2D Kawasaki model\n$c=0.35$ (fit)",
        "Fe--35Cr SANS\nwavelength (500 °C)",
        "Fe--35Cr Guinier\nradius (500 °C)",
        "Asymptotic LSW\nprediction",
    ]
    values = np.array(
        [simulated, FECR_SANS_WAVELENGTH_EXPONENT, FECR_GUINIER_RADIUS_EXPONENT, LSW_ASYMPTOTIC_EXPONENT]
    )
    colors = ["#2171b5", "#cb181d", "#ef6548", "#636363"]

    plt.rcParams.update({"font.family": "serif", "font.size": 10, "savefig.dpi": 300})
    fig, ax = plt.subplots(figsize=(7.4, 4.9), constrained_layout=True)
    x = np.arange(len(labels))
    ax.bar(x, values, color=colors, width=0.68, alpha=0.9)
    # Only the simulation CSV supplies a fit standard error. The review reports
    # the two experimental fitted values without uncertainties, so do not draw
    # fabricated zero-width error bars for them.
    ax.errorbar([x[0]], [values[0]], yerr=[simulated_err], fmt="none", ecolor="black", capsize=4, lw=1.2)
    for xpos, value in zip(x, values):
        ax.text(xpos, value + 0.012, f"{value:.3f}", ha="center", va="bottom", fontsize=10)

    ax.set_xticks(x, labels)
    ax.set_ylim(0.0, 0.40)
    ax.set_ylabel(r"Reported effective length-growth exponent, $\alpha$")
    ax.set_title("A qualitative Fe--Cr benchmark for the conserved Ising model")
    ax.grid(axis="y", alpha=0.25)
    ax.text(
        0.5,
        0.02,
        "Not a time/length calibration: 2D Monte Carlo sweeps and a 3D alloy aged in hours\n"
        "Compositions and length observables are not matched; proximity is not validation.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.3,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "0.7", "alpha": 0.95},
    )
    ax.text(
        0.99,
        0.98,
        "Experiment: Xu et al. (2016)\nDOI 10.1007/s11661-016-3800-4",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    alpha, stderr = load_simulated_c035()
    print(f"Model B c=0.35: alpha={alpha:.6f} +/- {stderr:.6f} (fit stderr)")
    print(f"Fe-35Cr SANS wavelength: alpha={FECR_SANS_WAVELENGTH_EXPONENT:.2f} (Xu et al., 2016)")
    print(f"Saved -> {make_figure()}")
