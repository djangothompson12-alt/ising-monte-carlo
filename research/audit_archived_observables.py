"""Recompute saved Model B correlations and lengths from archived snapshots.

This read-only audit deliberately does not call the engine's correlation or
length functions. It checks the *stored observables*, which the campaign
integrity verifier does not independently recompute.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from research.imaging_benchmark import sha


ATOL = 1e-10


def correlations_from_snapshot(snapshot: np.ndarray) -> np.ndarray:
    """Periodic connected x/y correlations from an independent NumPy FFT."""
    if snapshot.ndim != 2 or snapshot.shape[0] != snapshot.shape[1]:
        raise ValueError("Expected a square 2D lattice")
    if not np.all(np.isin(snapshot, (-1, 1))):
        raise ValueError("Expected only -1 and +1 spins")
    side = snapshot.shape[0]
    field = snapshot.astype(float)
    mean = float(field.mean())
    variance = 1.0 - mean * mean
    if variance <= 0:
        raise ValueError("Connected correlation undefined for a one-species lattice")
    spectrum = np.fft.fft2(field)
    raw = np.fft.ifft2(spectrum * spectrum.conj()).real / field.size
    maximum = side // 2
    horizontal = (raw[0, : maximum + 1] - mean * mean) / variance
    vertical = (raw[: maximum + 1, 0] - mean * mean) / variance
    return np.stack((horizontal, vertical))


def half_height_length(correlation: np.ndarray) -> float:
    """First interpolated downward half-height crossing; otherwise unresolved."""
    values = np.asarray(correlation, dtype=float)
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        return float("nan")
    for index in range(values.size - 1):
        left, right = values[index : index + 2]
        if left >= 0.5 and right < 0.5:
            return float(index + (left - 0.5) / (left - right))
    return float("nan")


def _direct_product(snapshot: np.ndarray, axis: int, separation: int) -> float:
    field = snapshot.astype(float)
    return float(np.mean(field * np.roll(field, -separation, axis=axis)))


def _max_finite_diff(left: np.ndarray, right: np.ndarray) -> float:
    finite = np.isfinite(left) & np.isfinite(right)
    return float(np.max(np.abs(left[finite] - right[finite]))) if finite.any() else 0.0


def _threshold_rounding_ambiguity(fresh: np.ndarray, archived: np.ndarray) -> bool:
    """Whether a half-height decision can flip under tolerated FFT roundoff."""
    return bool(np.any(np.abs(fresh - 0.5) <= ATOL)
                or np.any(np.abs(archived - 0.5) <= ATOL))


def audit_campaign(folder: Path) -> dict:
    manifest_path = folder / "manifest.json"
    status_path = folder / "status.json"
    manifest = json.loads(manifest_path.read_text())
    status = json.loads(status_path.read_text())
    plan = manifest["identity"]["plan"]
    expected = {
        f"c{ci}_L{side}_rep{rep:03d}.npz"
        for rep in range(plan["replicas"])
        for ci in range(len(plan["concentrations"]))
        for side in plan["sizes"]
    }
    found = {path.name for path in folder.glob("*.npz")}
    if status.get("state") != "complete" or status.get("completed") != len(expected) or found != expected:
        raise ValueError("Campaign must be complete with its exact declared inventory")

    max_correlation_difference = 0.0
    max_length_difference = 0.0
    max_interface_difference = 0.0
    max_direct_raw_difference = 0.0
    unresolved_saved = 0
    unresolved_recomputed = 0
    threshold_rounding_ambiguities = 0
    snapshots_checked = 0
    directions_checked = 0
    for path in sorted(folder.glob("*.npz")):
        with np.load(path, allow_pickle=False) as archive:
            snapshots = archive["snapshots"]
            saved_correlations = archive["correlations"]
            saved_lengths = archive["lengths"]
            saved_interfaces = archive["interfaces"]
            if (saved_correlations.shape != (len(snapshots), 2, snapshots.shape[1] // 2 + 1)
                    or saved_lengths.shape != (len(snapshots), 2)
                    or saved_interfaces.shape != (len(snapshots),)):
                raise ValueError(f"Unexpected observable shape in {path.name}")
            for index, snapshot in enumerate(snapshots):
                fresh = correlations_from_snapshot(snapshot)
                archived = saved_correlations[index]
                difference = _max_finite_diff(fresh, archived)
                max_correlation_difference = max(max_correlation_difference, difference)
                if not np.allclose(fresh, archived, rtol=0.0, atol=ATOL, equal_nan=True):
                    raise ValueError(f"Correlation mismatch in {path.name} checkpoint {index}: {difference}")

                lengths = np.asarray([half_height_length(row) for row in fresh])
                lengths_from_archived_correlation = np.asarray(
                    [half_height_length(row) for row in archived]
                )
                stored = saved_lengths[index]
                unresolved_saved += int(np.isnan(stored).sum())
                unresolved_recomputed += int(np.isnan(lengths).sum())
                difference = _max_finite_diff(lengths, stored)
                max_length_difference = max(max_length_difference, difference)
                # First verify that the stored length really follows the stored
                # correlation. A separately computed FFT may put a value that
                # is mathematically 0.5 just either side of the strict crossing
                # test, changing a boundary length into an unresolved one.
                if not np.allclose(lengths_from_archived_correlation, stored,
                                   rtol=0.0, atol=ATOL, equal_nan=True):
                    raise ValueError(f"Length mismatch in {path.name} checkpoint {index}: {difference}")
                for direction in range(2):
                    if not np.isclose(lengths[direction], stored[direction],
                                      rtol=0.0, atol=ATOL, equal_nan=True):
                        if not _threshold_rounding_ambiguity(
                                fresh[direction], archived[direction]):
                            raise ValueError(
                                f"Independent length mismatch in {path.name} "
                                f"checkpoint {index}, direction {direction}"
                            )
                        threshold_rounding_ambiguities += 1

                interfaces = sum(np.count_nonzero(snapshot != np.roll(snapshot, 1, axis=axis))
                                 for axis in (0, 1)) / (2 * snapshot.size)
                difference = abs(float(interfaces) - float(saved_interfaces[index]))
                max_interface_difference = max(max_interface_difference, difference)
                if difference > ATOL:
                    raise ValueError(f"Interface mismatch in {path.name} checkpoint {index}: {difference}")

                # A few direct pair products per file check the independent
                # FFT normalisation and axis convention without an expensive
                # all-separation O(L^3) calculation.
                if index in (0, len(snapshots) - 1):
                    mean = float(snapshot.mean())
                    variance = 1.0 - mean * mean
                    for axis, row in ((1, 0), (0, 1)):
                        for separation in (1, snapshot.shape[0] // 4):
                            direct = _direct_product(snapshot, axis, separation)
                            fft_raw = fresh[row, separation] * variance + mean * mean
                            difference = abs(direct - fft_raw)
                            max_direct_raw_difference = max(max_direct_raw_difference, difference)
                            if difference > ATOL:
                                raise ValueError(f"Direct-pair mismatch in {path.name}: {difference}")
                snapshots_checked += 1
                directions_checked += 2

    return {
        "campaign": str(folder),
        "manifest_sha256": sha(manifest_path),
        "replicas": len(expected),
        "snapshots_checked": snapshots_checked,
        "directional_lengths_checked": directions_checked,
        "unresolved_saved": unresolved_saved,
        "unresolved_recomputed": unresolved_recomputed,
        "threshold_rounding_ambiguities": threshold_rounding_ambiguities,
        "maximum_absolute_correlation_difference": max_correlation_difference,
        "maximum_absolute_length_difference": max_length_difference,
        "maximum_absolute_interface_difference": max_interface_difference,
        "maximum_absolute_direct_pair_difference": max_direct_raw_difference,
        "tolerance": ATOL,
        "conclusion": "All stored correlations and interface fractions match independent recomputation within tolerance. Stored lengths match an independent crossing of stored correlations; any fresh-FFT length differences occur only at the strict 0.5 boundary and are counted above. This does not validate the model against a material.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; audit records are immutable")
    result = audit_campaign(args.folder)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
