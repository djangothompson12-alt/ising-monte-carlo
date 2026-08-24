"""
main.py
=======

Entry point: runs a full temperature sweep of the 2D Ising model, saves the
raw observable data, and generates both publication figures.

Usage:
    python main.py
    python main.py --L 32 --n-temperatures 50 --eq-sweeps 4000 --mc-sweeps 5000
"""

from __future__ import annotations

import argparse
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from ising_engine import SimulationConfig, T_CRITICAL, run_temperature_sweep
from visualizer import plot_phase_transitions, plot_spin_domains

FIGURES_DIR = Path(__file__).parent / "figures"
RESULTS_DIR = Path(__file__).parent / "results"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments controlling the simulation parameters."""
    parser = argparse.ArgumentParser(description="2D Ising Model Monte Carlo pipeline")
    parser.add_argument("--L", type=int, default=24, help="Lattice size (L x L)")
    parser.add_argument("--J", type=float, default=1.0, help="Coupling constant")
    parser.add_argument("--t-min", type=float, default=1.2, help="Minimum temperature")
    parser.add_argument("--t-max", type=float, default=3.6, help="Maximum temperature")
    parser.add_argument("--n-temperatures", type=int, default=40, help="Number of T points")
    parser.add_argument("--eq-sweeps", type=int, default=3000, help="Equilibration sweeps")
    parser.add_argument("--mc-sweeps", type=int, default=4000, help="Sampling sweeps")
    parser.add_argument("--sample-interval", type=int, default=4, help="Sweeps between samples")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument(
        "--domain-L", type=int, default=64,
        help="Lattice size used only for the fig2 spin-domain snapshots (larger reads "
             "more clearly at the critical point)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the full simulation + visualization pipeline."""
    args = parse_args()
    config = SimulationConfig(
        L=args.L,
        J=args.J,
        t_min=args.t_min,
        t_max=args.t_max,
        n_temperatures=args.n_temperatures,
        eq_sweeps=args.eq_sweeps,
        mc_sweeps=args.mc_sweeps,
        sample_interval=args.sample_interval,
        seed=args.seed,
    )

    FIGURES_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    print(f"2D Ising Model Monte Carlo -- L={config.L}, J={config.J}")
    print(f"Temperature sweep: {config.t_min} to {config.t_max} "
          f"({config.n_temperatures} points), T_c = {T_CRITICAL:.4f}")
    print(f"Equilibration: {config.eq_sweeps} sweeps, Sampling: {config.mc_sweeps} sweeps "
          f"(every {config.sample_interval})")
    print()

    t0 = time.perf_counter()
    print("Running temperature sweep (JIT-compiling on first call)...")
    result = run_temperature_sweep(config)
    elapsed = time.perf_counter() - t0
    print(f"Sweep complete in {elapsed:.1f}s.")

    data_path = RESULTS_DIR / "observables.csv"
    header = "T,magnetization,energy,specific_heat,susceptibility,magnetization_err,energy_err"
    np.savetxt(
        data_path,
        np.column_stack([
            result.temperatures,
            result.magnetization,
            result.energy,
            result.specific_heat,
            result.susceptibility,
            result.magnetization_err,
            result.energy_err,
        ]),
        delimiter=",",
        header=header,
        comments="",
        fmt="%.6f",
    )
    print(f"Saved observable data -> {data_path}")

    fig1_path = plot_phase_transitions(result, FIGURES_DIR / "fig1_phase_transitions.png")
    print(f"Saved figure -> {fig1_path}")

    # A larger lattice (with a light sampling pass) makes the critical-point
    # snapshot legible: clusters at many length scales only look convincing
    # once L is well above the correlation length.
    snapshot_config = replace(
        config,
        L=args.domain_L,
        eq_sweeps=max(config.eq_sweeps, 3 * args.domain_L**2),
        mc_sweeps=200,
        sample_interval=200,
    )
    fig2_path = plot_spin_domains(snapshot_config, FIGURES_DIR / "fig2_spin_domains.png")
    print(f"Saved figure -> {fig2_path}")

    print()
    print("Pipeline complete: 0 errors.")


if __name__ == "__main__":
    main()
