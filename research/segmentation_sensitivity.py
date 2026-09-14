"""Audit explicitly declared segmentation-threshold sensitivity in 2D images.

This is not automatic segmentation or growth-law fitting. A microscopist or
data owner supplies the candidate thresholds and phase definition. Every
declared threshold is retained, preventing silent selection of a favourable
coarsening slope.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.analyse_images import validate_image
from research.imaging import image_length
from research.imaging_benchmark import sha, write_csv


REQUIRED_DOCUMENT_FIELDS = ("source", "license", "phase_definition")
REQUIRED_RECORD_FIELDS = (
    "id", "specimen", "path", "time", "time_unit", "pixel_size", "length_unit", "foreground", "thresholds"
)


def _load_image(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return validate_image(np.load(path, allow_pickle=False))
    if path.suffix.lower() in (".png", ".tif", ".tiff"):
        with Image.open(path) as source:
            if getattr(source, "n_frames", 1) != 1:
                raise ValueError("Choose and document a 2D slice, not a multipage volume")
            return validate_image(np.asarray(source))
    raise ValueError("Use NPY, PNG or single-plane TIFF")


def _validate_thresholds(values: object) -> list[float]:
    if not isinstance(values, list) or len(values) < 3:
        raise ValueError("Each record needs at least three declared thresholds")
    thresholds = [float(value) for value in values]
    if not np.all(np.isfinite(thresholds)) or len(set(thresholds)) != len(thresholds):
        raise ValueError("Thresholds must be finite and unique")
    return sorted(thresholds)


def analyse(manifest_path: Path, output: Path) -> None:
    """Measure every image at every declared threshold and save all outcomes."""
    document = json.loads(manifest_path.read_text())
    for key in REQUIRED_DOCUMENT_FIELDS:
        if not isinstance(document.get(key), str) or not document[key].strip():
            raise ValueError(f"Missing documented {key}")
    records = document.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("No real image records supplied")
    if output.exists():
        raise FileExistsError("Use a new output directory")

    rows, summaries, seen, units, image_hashes = [], [], set(), set(), {}
    for record in records:
        for key in REQUIRED_RECORD_FIELDS:
            if key not in record:
                raise ValueError(f"Missing {key}")
        identifier = record["id"]
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Missing or duplicate image id")
        seen.add(identifier)
        if record["foreground"] not in ("above", "below"):
            raise ValueError("Foreground must be 'above' or 'below'")
        if not record["specimen"] or not record["time_unit"] or not record["length_unit"]:
            raise ValueError("Specimen and units must be named")
        if not np.isfinite(record["time"]) or record["time"] < 0:
            raise ValueError("Time must be finite and non-negative")
        if not np.isfinite(record["pixel_size"]) or record["pixel_size"] <= 0:
            raise ValueError("Pixel size must be finite and positive")

        thresholds = _validate_thresholds(record["thresholds"])
        units.add((record["time_unit"], record["length_unit"]))
        path = manifest_path.parent / record["path"]
        if not path.is_file():
            raise FileNotFoundError(
                f"Input image does not exist: {path}. Replace template paths with an approved data file."
            )
        image = _load_image(path)
        image_hashes[identifier] = sha(path)
        lengths, fractions = [], []
        for threshold in thresholds:
            foreground = image >= threshold if record["foreground"] == "above" else image < threshold
            measured = image_length(2.0 * foreground.astype(float) - 1.0, record["pixel_size"])
            lengths.append(measured["length"])
            fractions.append(float(foreground.mean()))
            rows.append(dict(
                id=identifier, specimen=record["specimen"], time=record["time"], time_unit=record["time_unit"],
                length_unit=record["length_unit"], pixel_size=record["pixel_size"], foreground=record["foreground"],
                threshold=threshold, phase_fraction=fractions[-1], **measured,
            ))
        finite_lengths = np.asarray(lengths)[np.isfinite(lengths)]
        summaries.append(dict(
            id=identifier, thresholds_json=json.dumps(thresholds), resolved_thresholds=int(finite_lengths.size),
            total_thresholds=len(thresholds),
            length_min=float(np.min(finite_lengths)) if finite_lengths.size else float("nan"),
            length_max=float(np.max(finite_lengths)) if finite_lengths.size else float("nan"),
            phase_fraction_min=float(np.min(fractions)), phase_fraction_max=float(np.max(fractions)),
        ))
    if len(units) != 1:
        raise ValueError("Convert records to common time and length units explicitly")

    output.mkdir(parents=True)
    write_csv(output / "measurements_by_threshold.csv", rows)
    write_csv(output / "threshold_summaries.csv", summaries)
    manifest = dict(
        input_manifest_sha256=sha(manifest_path), image_sha256=image_hashes,
        source=document["source"], license=document["license"], phase_definition=document["phase_definition"],
        source_hashes={path.name: sha(path) for path in (Path(__file__), Path(__file__).with_name("imaging.py"), Path(__file__).with_name("metrology.py"))},
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "REPORT.md").write_text(
        "# Declared segmentation sensitivity\n\n"
        "Every candidate threshold supplied by the data owner is retained in the CSV. No threshold is selected automatically and no growth-law exponent is fitted. Threshold sensitivity does not resolve registration, specimen masking, phase identification, independence, or 2D/3D comparability; those require external technical review.\n"
    )
    print(output / "measurements_by_threshold.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analyse(args.manifest, args.output)
