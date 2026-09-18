"""Run the fixed, descriptive Al–Ge segmented-image operator test.

See ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md. This is not a kinetics fit.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.imaging import image_length, observe
from research.imaging_benchmark import sha
from research.inspect_alge_time_series import bounding_box, TIMES, VOXEL_UM


ROOT = Path(__file__).resolve().parents[1]
PLANES_UM = tuple(12.0 + 0.6 * index for index in range(11))
ROI_WIDTH = 300
MAX_UNKNOWN_FRACTION = .005


def centre_roi(labels: np.ndarray, width: int = ROI_WIDTH) -> tuple[np.ndarray | None, tuple[int, int, int, int], str]:
    solid = (labels == 2) | (labels == 3)
    if not solid.any():
        return None, (0, 0, 0, 0), "no Al/Ge labels"
    y, x = np.nonzero(solid)
    top = int(round(float(y.mean()) - width / 2))
    left = int(round(float(x.mean()) - width / 2))
    bounds = (top, top + width, left, left + width)
    if top < 0 or left < 0 or top + width > labels.shape[0] or left + width > labels.shape[1]:
        return None, bounds, "centred ROI outside image"
    roi = labels[top:top + width, left:left + width].copy()
    unknown = float(np.mean((roi != 2) & (roi != 3)))
    if unknown > MAX_UNKNOWN_FRACTION:
        return roi, bounds, f"non-Al/Ge fraction {unknown:.6g} exceeds 0.005"
    return roi, bounds, "eligible"


def measure(roi: np.ndarray) -> dict:
    unknown = (roi != 2) & (roi != 3)
    low = np.where(roi == 3, 1.0, -1.0)
    high = np.where((roi == 3) | unknown, 1.0, -1.0)
    native = image_length(low, VOXEL_UM)
    altered_field = observe(low, factor=4, threshold=0.0)
    altered = image_length(altered_field, 4 * VOXEL_UM)
    high_native = image_length(high, VOXEL_UM)
    high_altered = image_length(observe(high, factor=4, threshold=0.0), 4 * VOXEL_UM)
    ratio = (altered["length"] / native["length"]
             if native["resolved"] and altered["resolved"] else float("nan"))
    high_ratio = (high_altered["length"] / high_native["length"]
                  if high_native["resolved"] and high_altered["resolved"] else float("nan"))
    return dict(native_length_um=native["length"],
        native_x_um=native["length_x"], native_y_um=native["length_y"],
        altered_length_um=altered["length"],
        altered_x_um=altered["length_x"], altered_y_um=altered["length_y"],
        ratio_altered_to_native=ratio,
        ge_fraction_native=float(np.mean(low == 1)),
        ge_fraction_altered=float(np.mean(altered_field == 1)),
        unknown_as_ge_native_um=high_native["length"],
        unknown_as_ge_altered_um=high_altered["length"],
        unknown_as_ge_ratio=high_ratio,
        measurement_status=("resolved" if np.isfinite(ratio) and np.isfinite(high_ratio)
                            else "unresolved crossing"))


def run(source: Path, qa_manifest: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory; preserve previous results")
    qa = json.loads(qa_manifest.read_text())
    expected = {record["file"]: record for record in qa["records"]}
    if set(expected) != {f"ROI_{minute}min.tif" for minute in TIMES}:
        raise ValueError("QA manifest does not describe the four fixed source TIFFs")
    rows = []
    for minute in TIMES:
        path = source / f"ROI_{minute}min.tif"
        if sha(path) != expected[path.name]["sha256"]:
            raise ValueError(f"Source TIFF changed after metadata QA: {path.name}")
        with Image.open(path) as image:
            box = bounding_box(str(image.tag_v2.get(270, "")))
            if list(box) != expected[path.name]["bounding_box_xyz_um"]:
                raise ValueError("TIFF bounding box changed after metadata QA")
            for target_z in PLANES_UM:
                index = int(round((target_z - box[4]) / VOXEL_UM))
                actual_z = box[4] + index * VOXEL_UM
                if index < 0 or index >= image.n_frames or abs(actual_z - target_z) > .001:
                    raise ValueError(f"Fixed z plane absent: {path.name}, {target_z:g} µm")
                image.seek(index)
                labels = np.asarray(image)
                roi, bounds, roi_status = centre_roi(labels)
                counts = ({str(int(label)): int(number)
                           for label, number in zip(*np.unique(roi, return_counts=True))}
                          if roi is not None else {})
                base = dict(file=path.name, minutes=minute,
                    target_z_um=round(target_z, 3), actual_z_um=round(actual_z, 3),
                    z_index=index, roi_y0=bounds[0], roi_y1=bounds[1],
                    roi_x0=bounds[2], roi_x1=bounds[3],
                    label_counts=json.dumps(counts, sort_keys=True),
                    unknown_fraction=(float(np.mean((roi != 2) & (roi != 3)))
                                      if roi is not None else float("nan")),
                    roi_status=roi_status)
                if roi is not None and roi_status == "eligible":
                    rows.append({**base, **measure(roi)})
                else:
                    rows.append({**base, **dict(native_length_um=float("nan"),
                        native_x_um=float("nan"), native_y_um=float("nan"),
                        altered_length_um=float("nan"), altered_x_um=float("nan"),
                        altered_y_um=float("nan"), ratio_altered_to_native=float("nan"),
                        ge_fraction_native=float("nan"), ge_fraction_altered=float("nan"),
                        unknown_as_ge_native_um=float("nan"),
                        unknown_as_ge_altered_um=float("nan"),
                        unknown_as_ge_ratio=float("nan"),
                        measurement_status="not measured: ineligible ROI")})

    summaries = []
    for minute in TIMES:
        group = [row for row in rows if row["minutes"] == minute]
        ratios = np.asarray([row["ratio_altered_to_native"] for row in group], dtype=float)
        alternate = np.asarray([row["unknown_as_ge_ratio"] for row in group], dtype=float)
        fraction_shift = np.asarray([row["ge_fraction_altered"] - row["ge_fraction_native"]
                                     for row in group], dtype=float)
        passed = (len(group) == 11 and all(row["roi_status"] == "eligible"
                                            and row["measurement_status"] == "resolved"
                                            for row in group))
        summaries.append(dict(minutes=minute, planned_planes=11,
            eligible_resolved_planes=int(np.isfinite(ratios).sum()),
            status="all fixed planes resolved" if passed else "stage unresolved: report all failures",
            median_ratio=float(np.median(ratios)) if passed else None,
            min_ratio=float(ratios.min()) if passed else None,
            max_ratio=float(ratios.max()) if passed else None,
            median_ge_fraction_shift=float(np.median(fraction_shift)) if passed else None,
            max_abs_unknown_encoding_ratio_change=float(np.max(np.abs(alternate - ratios)))
                if passed else None))

    output.mkdir(parents=True)
    with (output / "fixed_plane_measurements.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status="exploratory within-image observation audit; not growth, strength or external use",
        dataset="Fell 2023, DOI 10.17632/hj9njz3rxp.1, CC BY 4.0",
        source_url="https://data.mendeley.com/datasets/hj9njz3rxp/1",
        protocol_sha256=sha(Path(__file__).with_name("ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md")),
        qa_manifest_sha256=sha(qa_manifest),
        source_sha256={"research/alge_static_operator_test.py": sha(Path(__file__)),
            "research/imaging.py": sha(ROOT / "research/imaging.py")},
        input_tiff_sha256={name: record["sha256"] for name, record in expected.items()},
        plane_count=44, independent_specimens=1,
        uncertainty="No inferential confidence interval; 11 correlated planes per stage",
        stages=summaries)
    (output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return output / "fixed_plane_measurements.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--qa-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.source, args.qa_manifest, args.output))
