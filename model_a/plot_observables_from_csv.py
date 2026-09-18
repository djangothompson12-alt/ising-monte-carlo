"""Relabel the archived Model A temperature-sweep figure without rerunning it.

The CSV column named ``susceptibility`` contains Var(|M|)/(N T), an
absolute-magnetization fluctuation proxy, not the field-response
susceptibility. This script preserves the numerical values and uses the
corrected visualizer label in a new figure file.
"""

from pathlib import Path

import numpy as np

from ising_engine import SweepResult
from visualizer import plot_phase_transitions


HERE = Path(__file__).resolve().parent


def main() -> None:
    source = HERE / "results" / "observables.csv"
    target = HERE / "figures" / "fig1_phase_transitions_corrected.png"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    table = np.genfromtxt(source, delimiter=",", names=True)
    if table.ndim != 1 or len(table) < 2:
        raise ValueError("Expected a multi-temperature archived sweep")
    result = SweepResult(
        temperatures=table["T"], magnetization=table["magnetization"],
        energy=table["energy"], specific_heat=table["specific_heat"],
        susceptibility=table["susceptibility"],
        magnetization_err=table["magnetization_err"],
        energy_err=table["energy_err"],
    )
    plot_phase_transitions(result, target)
    print(target)


if __name__ == "__main__":
    main()
