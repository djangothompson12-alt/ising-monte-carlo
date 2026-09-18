"""Descriptive stress test of threshold-only measurement on MetalDAM labels.

This is not a validation of Ising kinetics or a deployable phase classifier.
The annotation-optimised threshold is an in-sample upper bound, not a usable
setting for a new image. Raw images stay in an ignored local archive.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from PIL import Image

from research.image_audit_report import SOURCE_FILES
from research.imaging import image_length
from research.imaging_benchmark import sha, write_csv


DATASET_URL = "https://github.com/ari-dasci/OD-MetalDAM/releases/tag/1.0"
EXPECTED_ARCHIVE_SHA256 = "ceb65afa2495edb2000e5b858beeaf6178c4a368d0c02ec56715402482b3197e"
CLASS_CODE = 1  # Austenite, as defined by the dataset producers.


def dice_curve(gray: np.ndarray, truth: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Dice at thresholds 0..255 for gray >= t and gray < t, respectively."""
    if gray.dtype != np.uint8 or gray.shape != truth.shape or truth.dtype != bool:
        raise ValueError("Need aligned uint8 grayscale and bool annotation arrays")
    all_counts = np.bincount(gray.ravel(), minlength=256)
    positive_counts = np.bincount(gray[truth], minlength=256)
    above_all = np.cumsum(all_counts[::-1])[::-1]
    above_positive = np.cumsum(positive_counts[::-1])[::-1]
    below_all = gray.size - above_all
    below_positive = int(truth.sum()) - above_positive
    truth_size = int(truth.sum())
    above = np.divide(2 * above_positive, above_all + truth_size,
                      out=np.zeros(256, dtype=float), where=(above_all + truth_size) > 0)
    below = np.divide(2 * below_positive, below_all + truth_size,
                      out=np.zeros(256, dtype=float), where=(below_all + truth_size) > 0)
    return above, below


def otsu_threshold(gray: np.ndarray) -> int:
    """Image-only between-class-variance threshold; no expert labels used."""
    if gray.dtype != np.uint8:
        raise ValueError("Otsu input must be uint8")
    counts = np.bincount(gray.ravel(), minlength=256).astype(float)
    weight_low = np.cumsum(counts)
    weight_high = gray.size - weight_low
    sum_low = np.cumsum(counts * np.arange(256))
    total = sum_low[-1]
    valid = (weight_low > 0) & (weight_high > 0)
    score = np.full(256, -np.inf)
    score[valid] = ((total - sum_low[valid]) / weight_high[valid]
                    - sum_low[valid] / weight_low[valid]) ** 2
    score[valid] *= weight_low[valid] * weight_high[valid]
    return int(np.argmax(score)) + 1  # Bright class is >= returned threshold.


def _read_pair(archive: ZipFile, index: int) -> tuple[np.ndarray, np.ndarray, int]:
    root = f"MetalDAM/"
    with Image.open(BytesIO(archive.read(f"{root}images/micrograph{index}.jpg"))) as source:
        rgb = np.asarray(source.convert("RGB"))
    with Image.open(BytesIO(archive.read(f"{root}labels/micrograph{index}.png"))) as source:
        labels = np.asarray(source)
    # The release has one exceptional label file: micrograph26.png is RGB
    # although each of its three channels contains the same class codes.
    if index == 26 and labels.ndim == 3 and labels.shape[2] == 3:
        if not (np.array_equal(labels[:, :, 0], labels[:, :, 1])
                and np.array_equal(labels[:, :, 0], labels[:, :, 2])):
            raise ValueError("Micrograph 26 RGB label channels disagree")
        labels = labels[:, :, 0]
    band_rows = rgb.shape[0] - labels.shape[0]
    if (labels.ndim != 2 or rgb.shape[1] != labels.shape[1]
            or band_rows not in (65, 66)):
        raise ValueError(f"Image/label geometry mismatch for micrograph {index}")
    # Published labels omit the 65- or 66-pixel SEM information band at bottom.
    rgb = rgb[: labels.shape[0], :, :]
    if not np.array_equal(rgb[:, :, 0], rgb[:, :, 1]) or not np.array_equal(rgb[:, :, 0], rgb[:, :, 2]):
        raise ValueError(f"Micrograph {index} is not grayscale in its labelled region")
    if not set(np.unique(labels)).issubset(set(range(5))):
        raise ValueError(f"Unexpected label code in micrograph {index}")
    return rgb[:, :, 0].copy(), labels.copy(), band_rows


def _length(mask: np.ndarray) -> float:
    return image_length(2.0 * mask.astype(float) - 1.0, 1.0)["length"]


def benchmark(archive_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("Use a new output directory; prior results are immutable")
    archive_hash = sha(archive_path)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Archive hash differs from the inspected MetalDAM release")

    rows: list[dict] = []
    with ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"ZIP CRC error: {bad_member}")
        for index in range(42):
            gray, labels, band_rows = _read_pair(archive, index)
            truth = labels == CLASS_CODE
            bright, dark = dice_curve(gray, truth)
            threshold = otsu_threshold(gray)
            # Optimising against the very same annotation is deliberately
            # reported only as an optimistic diagnostic ceiling.
            oracle_bright = int(np.argmax(bright))
            oracle_dark = int(np.argmax(dark))
            if bright[oracle_bright] >= dark[oracle_dark]:
                oracle_direction, oracle_threshold = "bright", oracle_bright
                oracle_dice = bright[oracle_bright]
                oracle_mask = gray >= oracle_bright
            else:
                oracle_direction, oracle_threshold = "dark", oracle_dark
                oracle_dice = dark[oracle_dark]
                oracle_mask = gray < oracle_dark
            otsu_bright = gray >= threshold
            otsu_dark = gray < threshold
            rows.append(dict(
                image_id=f"micrograph{index}", height=gray.shape[0], width=gray.shape[1],
                omitted_bottom_band_rows=band_rows,
                reference_fraction=float(truth.mean()), reference_length_px=_length(truth),
                otsu_threshold=threshold, otsu_bright_dice=float(bright[threshold]),
                otsu_dark_dice=float(dark[threshold]),
                otsu_bright_fraction=float(otsu_bright.mean()),
                otsu_dark_fraction=float(otsu_dark.mean()),
                otsu_bright_length_px=_length(otsu_bright),
                otsu_dark_length_px=_length(otsu_dark),
                oracle_direction=oracle_direction, oracle_threshold=oracle_threshold,
                oracle_dice=float(oracle_dice),
                oracle_fraction=float(oracle_mask.mean()),
                oracle_length_px=_length(oracle_mask),
            ))

    output.mkdir(parents=True)
    write_csv(output / "per_image.csv", rows)
    source_root = Path(__file__).parent
    (output / "manifest.json").write_text(json.dumps(dict(
        dataset=DATASET_URL, archive_sha256=archive_hash, image_count=len(rows),
        primary_class="austenite (dataset label 1)", units="pixels only; scale not established",
        label_role="published annotations, not infallible physical ground truth",
        label_exception="micrograph26.png is RGB with identical class-code channels; first channel used",
        sources={name: sha(source_root / name) for name in SOURCE_FILES},
        pilot_source_sha256=sha(Path(__file__)),
        thresholds="all integer 0..255, both polarities; oracle is in-sample only",
    ), indent=2) + "\n")
    best = np.asarray([row["oracle_dice"] for row in rows])
    bright = np.asarray([row["otsu_bright_dice"] for row in rows])
    dark = np.asarray([row["otsu_dark_dice"] for row in rows])
    (output / "REPORT.md").write_text(
        "# MetalDAM threshold-only stress test\n\n"
        "Descriptive results on 42 published annotated additive-manufacturing steel SEM images. "
        "The original 65- or 66-pixel bottom information band is omitted by matching "
        "each label's dimensions. "
        "Class 1 is austenite. Images and labels are not redistributed here.\n\n"
        f"Median Otsu-bright Dice: {np.median(bright):.3f}; median Otsu-dark Dice: "
        f"{np.median(dark):.3f}. Median in-sample annotation-optimised Dice: "
        f"{np.median(best):.3f}. These are per-image descriptive medians, not "
        "independent-specimen confidence intervals.\n\n"
        "The annotation-optimised result uses each image's reference mask to choose both "
        "polarity and threshold, so it is an optimistic diagnostic ceiling, not a deployable "
        "classifier or independent validation. Otsu polarity is shown both ways rather than "
        "chosen after seeing labels. Correlation half-height lengths are measured in pixels "
        "only and are not particle radii. These static steel images do not test Kawasaki "
        "coarsening, ageing time, physical length calibration, or alloy performance. "
        "Dataset authors state that most tiny precipitates were not annotated; this is "
        "why class 3 is not used as a validation target.\n"
    )
    print(output / "REPORT.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    benchmark(args.archive, args.output)
