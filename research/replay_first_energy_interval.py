"""Read-only check of the archived quench's first recorded heat interval.

Replays only the seeded high-temperature preparation, then independently
evaluates the Hamiltonian of that state and the first saved post-quench state.
This does not re-run the quench or independently validate the sweep kernel.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from model_b import kawasaki_engine as engine
from research.imaging_benchmark import sha


def energy(lattice: np.ndarray, jx: float, jy: float) -> float:
    spins = lattice.astype(np.float64)
    return float(-jx * np.sum(spins * np.roll(spins, 1, axis=1))
                 -jy * np.sum(spins * np.roll(spins, 1, axis=0)))


def replay_file(path: Path) -> tuple[float, float]:
    with np.load(path, allow_pickle=False) as data:
        config = json.loads(str(data["config"]))
        first = data["snapshots"][0]
        reported = float(data["delta_energy"][0])
    initial = engine._seed_and_init_lattice(
        config["L"], config["seed"], config["concentration"])
    engine._run_n_sweeps(initial, 1 / config["T_initial"], config["Jx"],
                         config["Jy"], config["eq_sweeps_initial"])
    if int(initial.sum()) != int(first.sum()):
        raise ValueError(f"First snapshot changed the conserved spin count: {path}")
    recomputed = energy(first, config["Jx"], config["Jy"]) - energy(
        initial, config["Jx"], config["Jy"])
    if not np.isclose(recomputed, reported, rtol=0, atol=1e-9):
        raise ValueError(f"First heat interval disagrees: {path}: {recomputed} != {reported}")
    return recomputed, reported


def audit(folder: Path, source_root: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((folder / "manifest.json").read_text())
    expected_engine = manifest["identity"]["sources"]["model_b/kawasaki_engine.py"]
    frozen_engine = source_root / "model_b/kawasaki_engine.py"
    if sha(frozen_engine) != expected_engine or sha(Path(engine.__file__)) != expected_engine:
        raise ValueError("Replay engine does not match the campaign's frozen source")
    plan = manifest["identity"]["plan"]
    expected = {f"c{ci}_L{size}_rep{rep:03d}.npz"
                for ci in range(len(plan["concentrations"]))
                for size in plan["sizes"] for rep in range(plan["replicas"])}
    paths = sorted(folder.glob("*.npz"))
    if {path.name for path in paths} != expected:
        raise ValueError("Campaign inventory incomplete or contains extra replicas")
    max_difference = 0.0
    files = {}
    for path in paths:
        computed, reported = replay_file(path)
        max_difference = max(max_difference, abs(computed - reported))
        files[path.name] = sha(path)
    result = {
        "status": "passed",
        "meaning": "seeded pre-quench state replay plus independent Hamiltonians; not an independent dynamics implementation",
        "campaign": str(folder),
        "replicas": len(paths),
        "first_interval_max_absolute_energy_difference": max_difference,
        "source_sha256": sha(Path(__file__)),
        "engine_sha256": expected_engine,
        "raw_npz_sha256": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.folder, args.source_root, args.output), indent=2))
