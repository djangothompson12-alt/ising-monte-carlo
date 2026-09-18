"""Post-hoc usability replay of one published Al–Ge mask in the local tool.

This intentionally reuses a resolved plane from the earlier fixed 44-plane
audit. Agreement tests the user-facing workflow, not an independent physical
result or external laboratory use. The derived mask stays in ignored output.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.imaging_benchmark import sha
from research.mask_resolution_audit import audit


ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = "ROI_315min.tif"
TARGET_Z = 12.0
INDEX = 121
ROI = (382, 682, 360, 660)
VOXEL_UM = .06


def run(source: Path, qa_manifest: Path, reference_csv: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output folder; do not replace a previous replay")
    qa = json.loads(qa_manifest.read_text())
    source_record = next(item for item in qa["records"] if item["file"] == SOURCE_NAME)
    path = source / SOURCE_NAME
    if sha(path) != source_record["sha256"]:
        raise ValueError("Source TIFF differs from the earlier checked release")
    with Image.open(path) as image:
        image.seek(INDEX)
        labels = np.asarray(image)
    y0, y1, x0, x1 = ROI
    field = labels[y0:y1, x0:x1]
    if field.shape != (300, 300) or not np.all((field == 2) | (field == 3)):
        raise ValueError("Fixed demonstration field no longer contains only Al/Ge labels")
    with reference_csv.open(newline="") as stream:
        matches = [row for row in csv.DictReader(stream)
                   if row["file"] == SOURCE_NAME and
                   float(row["target_z_um"]) == TARGET_Z]
    if len(matches) != 1:
        raise ValueError("Earlier fixed-plane comparison is missing or ambiguous")
    reference = matches[0]
    if (int(reference["z_index"]) != INDEX or
            tuple(int(reference[name]) for name in
                  ("roi_y0", "roi_y1", "roi_x0", "roi_x1")) != ROI or
            reference["measurement_status"] != "resolved"):
        raise ValueError("Earlier fixed-plane selection differs from this replay")

    output.mkdir(parents=True)
    mask_path = output / "public_ge_mask.npy"
    np.save(mask_path, (field == 3).astype(np.uint8))
    input_path = output / "approved_input.json"
    input_path.write_text(json.dumps(dict(
        source="Jonas Fell, segmented Al–Ge tomography, DOI 10.17632/hj9njz3rxp.1",
        license="CC BY 4.0; local derived-mask usability replay only",
        phase_definition="all Ge labels (3), not isolated precipitates",
        tie_rule="foreground",
        records=[dict(id="315min_z12um", specimen_id="published single cast specimen",
                      mask_path=mask_path.name, foreground_value=1, background_value=0,
                      mask_authority="producer-supplied segmented tomography",
                      roi=[0, 300, 0, 300],
                      roi_reason="same post-hoc selected field as fixed 44-plane audit",
                      pixel_size=VOXEL_UM, length_unit="um", time=315, time_unit="min")],
    ), indent=2) + "\n")
    report = audit(input_path, output / "audit")
    with (output / "audit" / "measurements.csv").open(newline="") as stream:
        rows = {int(row["factor"]): row for row in csv.DictReader(stream)}
    checked = {"1": ("native_length_um", "ge_fraction_native"),
               "4": ("altered_length_um", "ge_fraction_altered")}
    for factor, names in checked.items():
        row = rows[int(factor)]
        for actual, earlier in ((row["length"], reference[names[0]]),
                                (row["phase_fraction"], reference[names[1]])):
            if not np.isclose(float(actual), float(earlier), rtol=0, atol=1e-10):
                raise ValueError(f"Tool replay disagrees with earlier {factor}× plane result")
    provenance = dict(
        status="passed post-hoc single-plane workflow replay; not independent data validation",
        source_tiff_sha256=sha(path), qa_manifest_sha256=sha(qa_manifest),
        reference_csv_sha256=sha(reference_csv), derived_mask_sha256=sha(mask_path),
        audit_manifest_sha256=sha(output / "audit" / "manifest.json"),
        selected_plane=dict(file=SOURCE_NAME, z_um=TARGET_Z, index=INDEX, roi=ROI),
        native_length_um=float(rows[1]["length"]),
        coarse_length_um=float(rows[4]["length"]),
        ratio=float(rows[4]["length_ratio"]),
        comparison="matches previously reported native and 4× values; same estimator code",
    )
    (output / "replay_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--qa-manifest", type=Path, required=True)
    parser.add_argument("--reference-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.source, args.qa_manifest, args.reference_csv, args.output))
