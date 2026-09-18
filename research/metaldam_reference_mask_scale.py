"""Resolution audit on the *published masks* of static MetalDAM images.

This tests observation sensitivity on expert-labelled steel micrographs, not
Kawasaki kinetics, ageing, strength or automated phase segmentation. It does
not redistribute producer image or label pixels. See the frozen protocol.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from PIL import Image

from research.imaging import block_average, image_length
from research.imaging_benchmark import sha, write_csv
from research.metaldam_mask_pilot import (
    CLASS_CODE, DATASET_URL, EXPECTED_ARCHIVE_SHA256,
)


FACTORS = (2, 4, 8)
PROTOCOL = Path(__file__).with_name("METALDAM_REFERENCE_MASK_SCALE_PROTOCOL_2026-09-18.md")


def read_label(archive: ZipFile, index: int) -> np.ndarray:
    """Read one producer label, checking the documented exceptional RGB file."""
    member = f"MetalDAM/labels/micrograph{index}.png"
    with Image.open(BytesIO(archive.read(member))) as source:
        labels = np.asarray(source)
    if index == 26 and labels.ndim == 3 and labels.shape[2] == 3:
        if not (np.array_equal(labels[:, :, 0], labels[:, :, 1])
                and np.array_equal(labels[:, :, 0], labels[:, :, 2])):
            raise ValueError("Micrograph 26 label channels disagree")
        labels = labels[:, :, 0]
    if labels.ndim != 2 or not set(np.unique(labels)).issubset(set(range(5))):
        raise ValueError(f"Unexpected label geometry or class code: {member}")
    return labels == CLASS_CODE


def dice(a: np.ndarray, b: np.ndarray) -> float:
    """Pixel Dice for two same-field binary masks."""
    if a.shape != b.shape or a.dtype != bool or b.dtype != bool:
        raise ValueError("Dice needs aligned Boolean masks")
    denominator = int(a.sum()) + int(b.sum())
    return float(2 * np.count_nonzero(a & b) / denominator) if denominator else 1.0


def measure_factor(mask: np.ndarray, factor: int, *, tie_to_class_one: bool) -> dict:
    """Compare downsampled mask to native mask over exactly the same field."""
    if mask.ndim != 2 or mask.dtype != bool or factor not in FACTORS:
        raise ValueError("Need Boolean 2D mask and a frozen reduction factor")
    height, width = mask.shape
    cropped_height = (height // factor) * factor
    cropped_width = (width // factor) * factor
    cropped = mask[:cropped_height, :cropped_width]
    if min(cropped.shape) // factor < 4:
        raise ValueError("Coarse field too small")
    reference = image_length(2.0 * cropped.astype(float) - 1.0, pixel_size=1.0)
    blocks = block_average(cropped.astype(float), factor)
    ties = blocks == 0.5
    coarse = blocks >= 0.5 if tie_to_class_one else blocks > 0.5
    reduced = image_length(2.0 * coarse.astype(float) - 1.0, pixel_size=float(factor))
    expanded = np.repeat(np.repeat(coarse, factor, axis=0), factor, axis=1)
    if expanded.shape != cropped.shape:
        raise AssertionError("Block expansion failed to recover the matched field")
    ratio = (reduced["length"] / reference["length"]
             if reference["resolved"] and reduced["resolved"] else float("nan"))
    return dict(
        factor=factor, tie_to_class_one=tie_to_class_one,
        trimmed_rows=height-cropped_height, trimmed_columns=width-cropped_width,
        reference_fraction=float(cropped.mean()), coarse_fraction=float(coarse.mean()),
        fraction_difference=float(coarse.mean()-cropped.mean()),
        tie_block_fraction=float(ties.mean()),
        dice_after_expansion=dice(cropped, expanded),
        reference_length_px=reference["length"], coarse_length_original_px=reduced["length"],
        reference_resolved=reference["resolved"], coarse_resolved=reduced["resolved"],
        length_ratio=ratio,
    )


def summarize(rows: list[dict]) -> list[dict]:
    result = []
    for factor in FACTORS:
        for tie_to_class_one in (True, False):
            group = [row for row in rows if row["factor"] == factor
                     and row["tie_to_class_one"] == tie_to_class_one]
            values = np.asarray([row["length_ratio"] for row in group], dtype=float)
            finite = values[np.isfinite(values)]
            result.append(dict(
                factor=factor, tie_to_class_one=tie_to_class_one,
                images=len(group), resolved_ratios=len(finite), unresolved_ratios=len(group)-len(finite),
                median_length_ratio=float(np.median(finite)) if len(finite) else None,
                min_length_ratio=float(np.min(finite)) if len(finite) else None,
                max_length_ratio=float(np.max(finite)) if len(finite) else None,
                count_ratio_below_one=int(np.sum(finite < 1)),
                count_ratio_above_one=int(np.sum(finite > 1)),
                median_dice=float(np.median([row["dice_after_expansion"] for row in group])),
                median_fraction_difference=float(np.median([row["fraction_difference"] for row in group])),
                median_tie_block_fraction=float(np.median([row["tie_block_fraction"] for row in group])),
            ))
    return result


def audit(archive_path: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory; do not overwrite prior runs")
    archive_hash = sha(archive_path)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Archive hash differs from the inspected MetalDAM release")
    rows = []
    with ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"ZIP CRC error: {bad_member}")
        for index in range(42):
            mask = read_label(archive, index)
            for factor in FACTORS:
                for tie_to_class_one in (True, False):
                    rows.append(dict(image_id=f"micrograph{index}", height=mask.shape[0],
                                     width=mask.shape[1],
                                     **measure_factor(mask, factor,
                                                      tie_to_class_one=tie_to_class_one)))
    output.mkdir(parents=True)
    write_csv(output / "per_image.csv", rows)
    (output / "summary.json").write_text(json.dumps(dict(
        status="exploratory real-mask observation audit; not kinetic or industrial validation",
        dataset=DATASET_URL, archive_sha256=archive_hash,
        protocol_sha256=sha(PROTOCOL), analysis_sha256=sha(Path(__file__)),
        mask_class="austenite (producer class 1)", image_count=42,
        possible_shared_specimens="images not treated as independent experimental units",
        units="original pixels, not physical length",
        groups=summarize(rows),
    ), indent=2) + "\n")
    return output / "summary.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(audit(args.archive, args.output))
