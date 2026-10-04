"""Run the phase-mask resolution audit on all 81 public FeM fields.

The FeM record contains registered reflected-light images and binary reference
masks for one mounted iron-ore concentrate sample.  This replay checks the
published archive checksum, every pair, mask labels and dimensions before
running the frozen native/2x/4x audit.  Field summaries are descriptive: the
81 views are not treated as 81 independent specimens.

Raw FeM pixels are neither copied into the repository nor embedded in the
report.  The Zenodo record is open, but its licence field is blank, so derived
results should be shared with the source cited while the raw files stay local.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.imaging_benchmark import sha
from research.mask_resolution_audit import audit


ARCHIVE_MD5 = "f1f2d29c449d12deb71b676f81b4ae78"
EXPECTED_FIELDS = 81
EXPECTED_SHAPE = (756, 999)
# Largest near-centred field that is divisible by four: one column is removed
# at the left and two at the right. This is fixed for every image.
ROI = (0, 756, 1, 997)
PIXEL_SIZE_UM = 1.05
SOURCE_URL = "https://doi.org/10.5281/zenodo.5014700"


def md5(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - verifies the producer's published MD5
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _checked_pairs(dataset_root: Path) -> list[tuple[Path, Path]]:
    references = sorted((dataset_root / "Reference").glob("FeM_*_Ref.tif"))
    images = sorted((dataset_root / "Reflected_Light_Microscopy").glob("FeM_*_RLM.tif"))
    if len(references) != EXPECTED_FIELDS or len(images) != EXPECTED_FIELDS:
        raise ValueError("FeM release must contain exactly 81 reference/image pairs")
    pairs = []
    for reference, image in zip(references, images, strict=True):
        ref_id = reference.stem.removesuffix("_Ref")
        image_id = image.stem.removesuffix("_RLM")
        if ref_id != image_id:
            raise ValueError(f"Unpaired FeM files: {reference.name}, {image.name}")
        with Image.open(reference) as handle:
            if handle.n_frames != 1:
                raise ValueError(f"{reference.name}: expected one mask plane")
            mask = np.asarray(handle)
        with Image.open(image) as handle:
            if handle.n_frames != 1 or np.asarray(handle).shape[:2] != EXPECTED_SHAPE:
                raise ValueError(f"{image.name}: unexpected source-image geometry")
        if mask.shape != EXPECTED_SHAPE:
            raise ValueError(f"{reference.name}: unexpected mask geometry")
        if set(int(value) for value in np.unique(mask)) != {0, 255}:
            raise ValueError(f"{reference.name}: expected only ore=0 and resin=255")
        pairs.append((reference, image))
    return pairs


def _quartiles(values: list[float]) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    return tuple(float(value) for value in np.quantile(array, [0.25, 0.5, 0.75]))


def summarise(measurements: Path, output: Path) -> list[dict]:
    with measurements.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    summary = []
    for factor in (1, 2, 4):
        selected = [row for row in rows if int(row["factor"]) == factor]
        resolved = [row for row in selected if row["status"] == "resolved"]
        if len(selected) != EXPECTED_FIELDS:
            raise ValueError(f"Expected 81 rows at {factor}x")
        metrics = {}
        for name in (
            "length", "length_ratio", "length_change_percent",
            "phase_fraction", "phase_fraction_change", "tie_block_fraction",
            "minimum_pixels_per_length", "direction_ratio_x_over_y",
        ):
            q25, median, q75 = _quartiles([float(row[name]) for row in resolved])
            metrics[f"{name}_q25"] = q25
            metrics[f"{name}_median"] = median
            metrics[f"{name}_q75"] = q75
        summary.append(dict(
            factor=factor,
            pixel_size_um=PIXEL_SIZE_UM * factor,
            fields=EXPECTED_FIELDS,
            resolved_fields=len(resolved),
            flagged_fields=sum(row["three_pixel_warning"] == "flag" for row in selected),
            **metrics,
        ))
    names = list(summary[0])
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        writer.writerows(summary)
    return summary


def _direct_length(mask: np.ndarray, factor: int) -> tuple[float, float, float]:
    """Independent, non-FFT half-height check for selected FeM fields."""
    y0, y1, x0, x1 = ROI
    field = mask[y0:y1, x0:x1] == 0
    height, width = field.shape
    blocks = field.reshape(
        height // factor, factor, width // factor, factor
    ).mean(axis=(1, 3))
    observed = blocks > 0.5  # the frozen ties-to-background rule
    z = (2.0 * observed.astype(float) - 1.0)
    z -= z.mean()
    variance = float(np.mean(z * z))
    lengths = []
    for axis in (1, 0):
        previous = 1.0
        crossing = float("nan")
        for distance in range(1, min(observed.shape) // 2 + 1):
            if axis == 1:
                correlation = float(np.mean(z[:, :-distance] * z[:, distance:]) / variance)
            else:
                correlation = float(np.mean(z[:-distance, :] * z[distance:, :]) / variance)
            if previous >= 0.5 > correlation:
                crossing = ((distance - 1) +
                            (previous - 0.5) / (previous - correlation))
                break
            previous = correlation
        lengths.append(crossing * PIXEL_SIZE_UM * factor)
    return float(observed.mean()), float(lengths[0]), float(lengths[1])


def verify_selected_fields(pairs: list[tuple[Path, Path]], measurements: Path) -> list[dict]:
    """Compare three predeclared fields with a direct real-space calculation."""
    with measurements.open(newline="") as stream:
        rows = {(row["id"], int(row["factor"])): row for row in csv.DictReader(stream)}
    checks = []
    selected = {"FeM_001", "FeM_041", "FeM_081"}
    for reference, _ in pairs:
        identifier = reference.stem.removesuffix("_Ref")
        if identifier not in selected:
            continue
        with Image.open(reference) as handle:
            mask = np.asarray(handle)
        for factor in (1, 2, 4):
            fraction, length_x, length_y = _direct_length(mask, factor)
            row = rows[(identifier, factor)]
            compared = {
                "phase_fraction": (fraction, float(row["phase_fraction"])),
                "length_x_um": (length_x, float(row["length_x"])),
                "length_y_um": (length_y, float(row["length_y"])),
            }
            for name, (direct, fft) in compared.items():
                if not np.isclose(direct, fft, rtol=0, atol=1e-10):
                    raise ValueError(
                        f"{identifier} {factor}x: direct {name} check disagrees"
                    )
            checks.append(dict(
                id=identifier, factor=factor, phase_fraction=fraction,
                length_x_um=length_x, length_y_um=length_y,
                status="direct real-space result matches FFT audit to 1e-10",
            ))
    if len(checks) != 9:
        raise ValueError("Expected nine independent direct checks")
    return checks


def run(dataset_root: Path, archive: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output folder; do not replace a previous replay")
    if md5(archive) != ARCHIVE_MD5:
        raise ValueError("Downloaded FeM archive does not match the published MD5")
    pairs = _checked_pairs(dataset_root)

    output.mkdir(parents=True)
    records = []
    for reference, _ in pairs:
        identifier = reference.stem.removesuffix("_Ref")
        records.append(dict(
            id=identifier,
            specimen_id=f"FeM single mounted iron-ore sample; field {identifier[-3:]}",
            mask_path=str(reference.resolve()),
            sha256=sha(reference),
            foreground_value=0,
            background_value=255,
            mask_authority=("Producer reference mask generated by thresholding the "
                            "registered SEM image; treated as a supplied reference, "
                            "not physical ground truth"),
            roi=list(ROI),
            roi_reason=("Same predeclared near-centred 756x996 field for every mask; "
                        "largest field divisible by four without resampling"),
            pixel_size=PIXEL_SIZE_UM,
            length_unit="um",
        ))
    plan = dict(
        source=("FeM dataset version 1, DOI 10.5281/zenodo.5014700; "
                "81 registered iron-ore microscopy fields"),
        license=("Zenodo record is publicly open and requests citation, but displays "
                 "no licence identifier; local academic analysis only and no raw-data "
                 "redistribution in this project"),
        phase_definition=("Binary producer reference: ore particles are value 0; "
                          "embedding resin is value 255"),
        materials_context=dict(
            material_system=("Itabiritic iron-ore concentrate, mainly hematite and "
                             "quartz with minor magnetite and goethite, mounted in epoxy"),
            processing_condition=("-149+105 um size fraction with density above 3.2; "
                                  "cold mounted, ground and polished"),
            imaging_method=("10x reflected-light microscopy registered to SEM; binary "
                            "reference masks produced by thresholding the SEM images"),
            section_geometry=("81 two-dimensional registered fields from one mounted "
                              "sample; each source field is 756x999 pixels"),
            calibration_source=("FeM Zenodo record states 1.05 um/pixel after registration"),
            measurement_purpose=("Field-wise stress test of how 2x and 4x digital mask "
                                 "reduction changes an ore/resin correlation half-height "
                                 "length and apparent ore area fraction"),
        ),
        tie_rule="background",
        decision_tolerance_fraction=None,
        records=records,
    )
    plan_path = output / "approved_input.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    report = audit(plan_path, output / "audit")
    summary_path = output / "field_summary.csv"
    summary = summarise(output / "audit" / "measurements.csv", summary_path)
    direct_checks = verify_selected_fields(
        pairs, output / "audit" / "measurements.csv"
    )
    provenance = dict(
        status="passed full 81-field public-data replay",
        interpretation=("descriptive distribution across fields from one mounted sample; "
                        "not independent-specimen uncertainty or laboratory validation"),
        source=SOURCE_URL,
        archive_md5=ARCHIVE_MD5,
        archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,
        reference_masks=len(pairs),
        source_images=len(pairs),
        expected_shape=list(EXPECTED_SHAPE),
        fixed_roi=list(ROI),
        pixel_size_um=PIXEL_SIZE_UM,
        input_plan_sha256=sha(plan_path),
        audit_manifest_sha256=sha(output / "audit" / "manifest.json"),
        measurements_sha256=sha(output / "audit" / "measurements.csv"),
        field_summary_sha256=sha(summary_path),
        independent_direct_checks=direct_checks,
        summary=summary,
    )
    (output / "replay_provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.dataset_root, args.archive, args.output))
