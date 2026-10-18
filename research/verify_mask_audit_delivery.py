"""Check a static mask-audit delivery, with optional local numerical replay.

Hashes detect accidental changes against the supplied manifest, not forgery.
A replay needs the owner's original plan and masks, held locally. No image
pixels or input paths are written into the returned verification record.
This is not segmentation, calibration or physical validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np

from research.mask_resolution_audit import SOURCE_FILES, audit


OUTPUT_FILES = ("measurements.csv", "report.html", "tie_sensitivity.csv",
                "decision_summary.csv")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames
        values = list(reader)
    if not names or len(set(names)) != len(names) or not values:
        raise ValueError(f"Invalid or empty audit table: {path.name}")
    if any(None in row or any(value is None for value in row.values()) for row in values):
        raise ValueError(f"Malformed audit table: {path.name}")
    return names, values


def _same_tables(old: Path, new: Path) -> None:
    names, before = _rows(old)
    other_names, after = _rows(new)
    if names != other_names or len(before) != len(after):
        raise ValueError(f"Replay table structure differs: {old.name}")
    for index, (left, right) in enumerate(zip(before, after, strict=True)):
        for key in names:
            if left[key] == right[key]:
                continue
            try:
                a, b = float(left[key]), float(right[key])
            except (ValueError, TypeError):
                raise ValueError(f"Replay differs in {old.name}, row {index}, {key}") from None
            # A fixed absolute tolerance would silently become very permissive
            # when an owner expresses lengths in small physical units.
            if not np.isclose(a, b, rtol=1e-12, atol=0, equal_nan=True):
                raise ValueError(f"Replay differs in {old.name}, row {index}, {key}")


def verify(folder: Path, *, input_plan: Path | None = None,
           require_current_sources: bool = False) -> dict:
    folder = Path(folder)
    manifest_path = folder / "manifest.json"
    record = json.loads(manifest_path.read_bytes())
    hashes = record.get("output_sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(OUTPUT_FILES):
        raise ValueError("Expected the four named audit outputs; no arbitrary paths are accepted")
    for name in OUTPUT_FILES:
        if digest(folder / name) != hashes[name]:
            raise ValueError(f"Delivered output hash mismatch: {name}")
    for name in OUTPUT_FILES:
        if name.endswith(".csv"):
            _rows(folder / name)
    recorded_sources = record.get("source_sha256", {})
    current_sources = {name: digest(Path(__file__).with_name(name)) for name in SOURCE_FILES}
    sources_match = recorded_sources == current_sources
    if require_current_sources and not sources_match:
        raise ValueError("Recorded source version differs from current sources")
    replayed = False
    if input_plan is not None:
        input_plan = Path(input_plan)
        if digest(input_plan) != record.get("input_manifest_sha256"):
            raise ValueError("Input plan hash differs from the delivered audit")
        with tempfile.TemporaryDirectory(prefix="mask-audit-replay-") as temporary:
            target = Path(temporary) / "replay"
            audit(input_plan, target)
            replay = json.loads((target / "manifest.json").read_bytes())
            if replay["mask_sha256"] != record.get("mask_sha256"):
                raise ValueError("Replay mask hashes differ from the delivered audit")
            if replay["input_settings"] != record.get("input_settings"):
                raise ValueError("Replay input declarations differ from the delivered audit")
            for name in OUTPUT_FILES:
                if name.endswith(".csv"):
                    _same_tables(folder / name, target / name)
            replayed = True
    return dict(
        audit_manifest_sha256=digest(manifest_path),
        output_hashes_verified=len(OUTPUT_FILES),
        current_sources_match=sources_match,
        numerical_tables_replayed=replayed,
        interpretation=("Internal delivery integrity and optional numerical replay only; "
                        "hashes are not authentication; replay uses the same implementation, "
                        "not an independent algorithm or physical reference"),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--input-plan", type=Path)
    parser.add_argument("--require-current-sources", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.folder, input_plan=args.input_plan,
                            require_current_sources=args.require_current_sources), indent=2))
