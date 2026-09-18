"""Metadata and fixed-slice QA for Fell's public Al–Ge ROI tomography series.

This inspects segmented labels and physical bounding boxes. It does not fit
growth, infer a common 3D registration, or compare Monte Carlo time with
minutes. Input TIFFs are separately credited CC BY 4.0 research data.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
from PIL import Image

from research.imaging_benchmark import sha


TIMES = (15, 105, 195, 315)
VOXEL_UM = 0.06
DISPLAY_Z_UM = 15.0


def bounding_box(description: str) -> tuple[float, float, float, float, float, float]:
    match = re.fullmatch(r"BoundingBox\s+((?:\d+(?:\.\d+)?\s*){6})", description.strip())
    if not match:
        raise ValueError(f"Missing or unexpected BoundingBox metadata: {description!r}")
    values = tuple(float(word) for word in match.group(1).split())
    if len(values) != 6 or not (values[0] < values[1] and values[2] < values[3]
                                     and values[4] < values[5]):
        raise ValueError("BoundingBox bounds are not increasing")
    return values


def common_crop(bounds: list[tuple[float, ...]], shapes: list[tuple[int, int, int]],
                voxel: float = VOXEL_UM) -> tuple[dict, list[tuple[slice, slice]]]:
    """Intersect declared XY coordinates; this is not image registration."""
    x0, x1 = max(b[0] for b in bounds), min(b[1] for b in bounds)
    y0, y1 = max(b[2] for b in bounds), min(b[3] for b in bounds)
    width = math.floor((x1 - x0) / voxel + 1e-8)
    height = math.floor((y1 - y0) / voxel + 1e-8)
    if width < 16 or height < 16:
        raise ValueError("No substantial common physical XY rectangle")
    slices = []
    for box, shape in zip(bounds, shapes):
        start_x = int(round((x0 - box[0]) / voxel))
        start_y = int(round((y0 - box[2]) / voxel))
        if (not np.isclose(box[0] + start_x * voxel, x0, atol=voxel / 20)
                or not np.isclose(box[2] + start_y * voxel, y0, atol=voxel / 20)
                or start_x < 0 or start_y < 0 or start_x + width > shape[2]
                or start_y + height > shape[1]):
            raise ValueError("Bounding boxes do not align to a common voxel grid")
        slices.append((slice(start_y, start_y + height),
                       slice(start_x, start_x + width)))
    return dict(x_start_um=x0, y_start_um=y0, x_width_um=width * voxel,
                y_height_um=height * voxel, width_pixels=width,
                height_pixels=height), slices


def inspect(source: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory; preserve the previous QA")
    records = []
    bounds = []
    shapes = []
    for minute in TIMES:
        path = source / f"ROI_{minute}min.tif"
        with Image.open(path) as image:
            box = bounding_box(str(image.tag_v2.get(270, "")))
            shape = (image.n_frames, image.height, image.width)
            # TIFF descriptions give lower/upper corner coordinates; each
            # span should be within one voxel of count × voxel spacing.
            spans = (box[1] - box[0], box[3] - box[2], box[5] - box[4])
            counts = (shape[2], shape[1], shape[0])
            if any(abs(span - count * VOXEL_UM) > VOXEL_UM + 1e-8
                   for span, count in zip(spans, counts)):
                raise ValueError(f"Voxel spacing inconsistent with BoundingBox: {path.name}")
            sampled = {}
            for z in sorted({0, shape[0] // 4, shape[0] // 2, 3 * shape[0] // 4, shape[0] - 1}):
                image.seek(z)
                labels, numbers = np.unique(np.asarray(image), return_counts=True)
                sampled[str(z)] = {str(int(label)): int(number)
                                   for label, number in zip(labels, numbers)}
            records.append(dict(file=path.name, minutes=minute, size_bytes=path.stat().st_size,
                                sha256=sha(path), shape_zyx=list(shape),
                                bounding_box_xyz_um=list(box), sampled_label_counts=sampled))
            bounds.append(box)
            shapes.append(shape)

    rectangle, crops = common_crop(bounds, shapes)
    cmap = ListedColormap(["#15232e", "#ba4397", "#b8c2c5", "#e99738", "#753b9a"])
    norm = BoundaryNorm(np.arange(-.5, 5.5, 1), cmap.N)
    figure, axes = plt.subplots(2, 2, figsize=(9, 8.8), layout="constrained")
    display_counts = []
    for axis, minute, box, crop in zip(axes.flat, TIMES, bounds, crops):
        path = source / f"ROI_{minute}min.tif"
        with Image.open(path) as image:
            z = int(round((DISPLAY_Z_UM - box[4]) / VOXEL_UM))
            if z < 0 or z >= image.n_frames:
                raise ValueError(f"Display plane outside {path.name}")
            image.seek(z)
            view = np.asarray(image)[crop]
            values, numbers = np.unique(view, return_counts=True)
            display_counts.append(dict(minutes=minute, z_index=z,
                label_counts={str(int(label)): int(number)
                              for label, number in zip(values, numbers)}))
            axis.imshow(view, cmap=cmap, norm=norm, interpolation="nearest")
            axis.set_title(f"{minute} min, claimed z≈{DISPLAY_Z_UM:g} µm")
            axis.set_xlabel("common-coordinate crop, pixels")
            axis.set_ylabel("common-coordinate crop, pixels")
    figure.suptitle("Fell Al–Ge ROI TIFFs: coordinate-based slice inspection only\n"
                    "Al=grey · Ge=orange · air=dark · other labels=purple")
    output.mkdir(parents=True)
    figure.savefig(output / "common_coordinate_slice_qa.png", dpi=150)
    plt.close(figure)
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        status="metadata and fixed-slice feasibility; no kinetic fit or registration proof",
        dataset="Fell 2023, DOI 10.17632/hj9njz3rxp.1, CC BY 4.0",
        source_url="https://data.mendeley.com/datasets/hj9njz3rxp/1",
        voxel_um=VOXEL_UM, display_z_um=DISPLAY_Z_UM,
        note="Physical bounding-box coordinates are taken from TIFF metadata. "
             "The common crop is an intersection of those declared coordinates, "
             "not an independently validated image registration or same-particle track.",
        records=records, common_xy_rectangle=rectangle,
        displayed_label_counts=display_counts,
        analysis_source_sha256=sha(Path(__file__)))
    (output / "metadata_qa.json").write_text(json.dumps(report, indent=2) + "\n")
    return output / "metadata_qa.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(inspect(args.source, args.output))
