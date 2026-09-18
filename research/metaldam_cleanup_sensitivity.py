"""Post-hoc mask-cleanup sensitivity on the public MetalDAM annotations.

This asks whether the pilot's Otsu/annotation length gap is chiefly a fine-
texture artefact. It is a descriptive stress test, not a trained segmenter,
kinetics measurement, or validation of a physical length.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter

from research.image_audit_report import SOURCE_FILES
from research.imaging_benchmark import sha, write_csv
from research.metaldam_mask_pilot import (
    CLASS_CODE, DATASET_URL, EXPECTED_ARCHIVE_SHA256, _length, _read_pair,
    otsu_threshold,
)


def dice(mask: np.ndarray, reference: np.ndarray) -> float:
    """Pixel-overlap score for two aligned nonempty binary masks."""
    if mask.shape != reference.shape or mask.dtype != bool or reference.dtype != bool:
        raise ValueError("Need aligned boolean masks")
    denominator = int(mask.sum()) + int(reference.sum())
    return float(2 * np.count_nonzero(mask & reference) / denominator) if denominator else 1.0


def cleanup(mask: np.ndarray, width: int) -> np.ndarray:
    """Odd-width median filter with reflection at the image boundary."""
    if mask.dtype != bool or mask.ndim != 2 or width not in (1, 3, 5):
        raise ValueError("Need a 2D boolean mask and width 1, 3 or 5")
    return mask.copy() if width == 1 else median_filter(mask, size=width, mode="reflect")


def _summarise(rows: list[dict]) -> dict:
    summary: dict = {
        "n_images": len({row["image_id"] for row in rows}),
        "n_mask_measurements": len(rows),
        "by_width": {},
    }
    for width in (1, 3, 5):
        subset = [row for row in rows if row["median_width"] == width]
        valid = [row for row in subset if np.isfinite(row["length_ratio"])]
        summary["by_width"][str(width)] = {
            "resolved": len(valid),
            "median_dice": float(np.median([r["dice"] for r in subset])),
            "median_phase_fraction": float(np.median([r["mask_fraction"] for r in subset])),
            "median_abs_phase_fraction_error": float(np.median([
                r["abs_phase_fraction_error"] for r in subset
            ])),
            "median_length_ratio": float(np.median([r["length_ratio"] for r in valid])) if valid else None,
            "median_abs_log_length_error": float(np.median([
                r["abs_log_length_error"] for r in valid
            ])) if valid else None,
        }
    baseline = {row["image_id"]: row for row in rows if row["median_width"] == 1}
    summary["paired_vs_raw"] = {}
    for width in (3, 5):
        paired = [(baseline[row["image_id"]], row) for row in rows if row["median_width"] == width]
        resolved = [(old, new) for old, new in paired if np.isfinite(old["abs_log_length_error"])
                    and np.isfinite(new["abs_log_length_error"])]
        summary["paired_vs_raw"][str(width)] = {
            "jointly_resolved": len(resolved),
            "length_error_improved": sum(new["abs_log_length_error"] < old["abs_log_length_error"] for old, new in resolved),
            "length_error_worsened": sum(new["abs_log_length_error"] > old["abs_log_length_error"] for old, new in resolved),
            "length_error_unchanged": sum(new["abs_log_length_error"] == old["abs_log_length_error"] for old, new in resolved),
            "median_paired_change_abs_log_length_error": float(np.median([
                new["abs_log_length_error"] - old["abs_log_length_error"] for old, new in resolved
            ])) if resolved else None,
            "median_paired_change_dice": float(np.median([
                new["dice"] - old["dice"] for old, new in paired
            ])),
            "median_paired_change_abs_phase_fraction_error": float(np.median([
                new["abs_phase_fraction_error"] - old["abs_phase_fraction_error"]
                for old, new in paired
            ])),
        }
    return summary


def _figure(rows: list[dict], destination: Path) -> None:
    palette = {1: "#203c6b", 3: "#c26924", 5: "#63843b"}
    labels = {1: "raw Otsu", 3: "3×3 median", 5: "5×5 median"}
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for width in (1, 3, 5):
        data = [row for row in rows if row["median_width"] == width
                and np.isfinite(row["length_ratio"])]
        ax.scatter([r["dice"] for r in data], [r["length_ratio"] for r in data],
                   s=24, alpha=0.65, color=palette[width], label=f"{labels[width]} (n={len(data)})")
    ax.axhline(1, color="black", lw=1, ls="--", label="published-mask length")
    ax.set(xlabel="Dice overlap with published austenite mask",
           ylabel="Measured length / published-mask length",
           title="Mask cleanup versus downstream length (42 steel micrographs)")
    ax.set_yscale("log")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def benchmark(archive_path: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Use a new output directory; prior results are immutable")
    archive_hash = sha(archive_path)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Archive hash differs from inspected MetalDAM release")
    rows: list[dict] = []
    with ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"ZIP CRC error: {bad_member}")
        for index in range(42):
            gray, labels, band_rows = _read_pair(archive, index)
            reference = labels == CLASS_CODE
            reference_length = _length(reference)
            threshold = otsu_threshold(gray)
            raw = gray < threshold  # Exploratory polarity selected in the earlier pilot.
            for width in (1, 3, 5):
                mask = cleanup(raw, width)
                length = _length(mask)
                valid = np.isfinite(reference_length) and np.isfinite(length) and reference_length > 0 and length > 0
                ratio = float(length / reference_length) if valid else float("nan")
                rows.append({
                    "image_id": f"micrograph{index}", "median_width": width,
                    "otsu_threshold": threshold, "omitted_bottom_band_rows": band_rows,
                    "reference_fraction": float(reference.mean()),
                    "reference_length_px": float(reference_length),
                    "mask_fraction": float(mask.mean()),
                    "abs_phase_fraction_error": float(abs(mask.mean() - reference.mean())),
                    "dice": dice(mask, reference),
                    "mask_length_px": float(length), "length_ratio": ratio,
                    "abs_log_length_error": float(abs(np.log(ratio))) if valid else float("nan"),
                    "resolved": bool(valid),
                })
            print(f"Measured image {index + 1}/42", flush=True)

    summary = _summarise(rows)
    output.mkdir(parents=True)
    write_csv(output / "per_image.csv", rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    source_root = Path(__file__).parent
    (output / "manifest.json").write_text(json.dumps({
        "dataset": DATASET_URL, "archive_sha256": archive_hash,
        "analysis_status": "post-hoc exploratory after a one-image 3x3 check",
        "primary_mask": "class 1 published austenite annotation",
        "segmentation": "per-image Otsu threshold, dark polarity selected in earlier pilot",
        "cleanup": "binary median filter, widths 1 (raw), 3, 5, reflect boundary",
        "units": "pixels only; no physical calibration or ageing times",
        "sources": {name: sha(source_root / name) for name in SOURCE_FILES},
        "pilot_source_sha256": sha(source_root / "metaldam_mask_pilot.py"),
        "analysis_source_sha256": sha(Path(__file__)),
    }, indent=2) + "\n")
    _figure(rows, output / "dice_vs_length_ratio.png")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.archive, args.output), indent=2))
