"""Re-measure an archived symmetric Model B campaign using reference observables.

This does not rerun dynamics, fit an exponent, or establish agreement with a
paper.  It creates a complete per-replica/per-timepoint measurement table only
after a human has completed a declaration identifying the target study and its
measurement convention.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from research.reference_measurements import reference_measurements


REQUIRED_DECLARATION_KEYS = (
    "reference", "purpose", "dynamics_match", "postprocessing_match",
    "observable_match", "comparison_scope", "reviewer_status", "student_verified",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_declaration(path: Path) -> dict:
    """Load an intentionally human-authored comparison declaration.

    A placeholder, an unpublished target, or a reviewer name invented by the
    code would undermine the purpose of this pathway, so those are rejected.
    """
    declaration = json.loads(path.read_text())
    missing = [key for key in REQUIRED_DECLARATION_KEYS if not str(declaration.get(key, "")).strip()]
    if missing:
        raise ValueError("Declaration has empty required fields: " + ", ".join(missing))
    if declaration.get("reviewer_status") not in {"not_yet_reviewed", "reviewed"}:
        raise ValueError("reviewer_status must be 'not_yet_reviewed' or 'reviewed'")
    if declaration.get("student_verified") is not True:
        raise ValueError("A student must read and verify the declaration before measurement.")
    return declaration


def validate_campaign(folder: Path, concentration_index: int) -> tuple[dict, float]:
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing campaign manifest: {manifest_path}")
    plan = json.loads(manifest_path.read_text())["identity"]["plan"]
    if plan["Jx"] != plan["Jy"]:
        raise ValueError("Reference pathway is limited to isotropic Jx=Jy campaigns.")
    concentrations = plan["concentrations"]
    if not 0 <= concentration_index < len(concentrations):
        raise ValueError("concentration index is outside the campaign plan")
    concentration = float(concentrations[concentration_index])
    if not np.isclose(concentration, 0.5):
        raise ValueError("Reference pathway is limited to the symmetric c=0.5 composition.")
    return plan, concentration


def measure_campaign(folder: Path, declaration_path: Path, output: Path, concentration_index: int = 0) -> Path:
    """Write raw and one-pass-filtered observables for every archived snapshot."""
    declaration = load_declaration(declaration_path)
    plan, concentration = validate_campaign(folder, concentration_index)
    paths = sorted(folder.glob(f"c{concentration_index}_L*_rep*.npz"))
    expected = plan["replicas"] * len(plan["sizes"])
    if len(paths) != expected:
        raise ValueError(f"Reference benchmark requires all {expected} planned symmetric replicas; found {len(paths)}")
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            if int(data["t"][-1]) != plan["max_sweeps"]:
                raise ValueError(f"Incomplete result: {path}")
    output.mkdir(parents=True, exist_ok=True)
    table_path = output / "reference_measurements.csv"
    if table_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {table_path}")
    rows: list[dict] = []
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            snapshots, sweeps = data["snapshots"], data["t"]
            if len(snapshots) != len(sweeps):
                raise ValueError(f"Snapshot/time mismatch in {path}")
            for snapshot_index, (sweep, lattice) in enumerate(zip(sweeps, snapshots)):
                metrics = reference_measurements(lattice)
                rows.append(dict(
                    input_file=path.name, snapshot_index=snapshot_index,
                    L=int(lattice.shape[0]), concentration=concentration, sweep=int(sweep), **metrics,
                ))
    with table_path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    provenance = dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=_sha256(Path(__file__)),
        measurement_sha256=_sha256(Path(__file__).with_name("reference_measurements.py")),
        declaration_sha256=_sha256(declaration_path), campaign_manifest_sha256=_sha256(folder / "manifest.json"),
        campaign_folder=str(folder), concentration_index=concentration_index,
        concentration=concentration, plan=plan, input_sha256={path.name: _sha256(path) for path in paths},
        declaration=declaration,
        caveat=("One-pass filtering is observation-only. This table is not evidence of a reproduction, "
                "a fitted growth exponent, or agreement with the named reference."),
    )
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return table_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path, help="Campaign directory containing manifest.json and NPZ replicas")
    parser.add_argument("declaration", type=Path, help="Student-verified comparison declaration")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concentration-index", type=int, default=0)
    args = parser.parse_args()
    print(measure_campaign(args.campaign, args.declaration, args.output, args.concentration_index))
