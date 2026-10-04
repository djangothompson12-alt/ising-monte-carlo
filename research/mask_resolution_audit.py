"""Audit resolution sensitivity of declared, expert-supplied 2D phase masks.

This is a local measurement check, not a segmentation algorithm, an ageing
kinetics fit, an alloy-property predictor, a chemical mass-balance test, or
evidence of laboratory adoption. Masks and physical scale are supplied by the
user; no image pixels are copied into the HTML or CSV output.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.image_audit_report import _nonempty, _positive_number, _roi_bounds
from research.imaging import block_average, image_length
from research.imaging_benchmark import sha, write_csv


FACTORS = (1, 2, 4)
SOURCE_FILES = ("mask_resolution_audit.py", "imaging.py",
                "imaging_benchmark.py", "image_audit_report.py")
MATERIALS_CONTEXT_FIELDS = (
    "material_system",
    "processing_condition",
    "imaging_method",
    "section_geometry",
    "calibration_source",
    "measurement_purpose",
)


def load_mask(path: Path, foreground_value: int, background_value: int) -> np.ndarray:
    """Read an explicit two-label mask; never infer polarity from appearance."""
    if path.suffix.lower() == ".npy":
        array = np.load(path, allow_pickle=False)
    else:
        with Image.open(path) as image:
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError(f"{path}: select and save one 2D mask plane; multi-frame images are not accepted")
            array = np.asarray(image)
    if array.ndim != 2 or min(array.shape) < 16:
        raise ValueError(f"{path}: mask must be a single 2D plane at least 16 pixels wide")
    if foreground_value == background_value:
        raise ValueError("Foreground and background values must differ")
    if not np.all((array == foreground_value) | (array == background_value)):
        raise ValueError(f"{path}: undeclared label, nonfinite value, or antialiased pixel")
    return array == foreground_value


def measure(mask: np.ndarray, factor: int, pixel_size: float,
            ties_to_foreground: bool) -> dict:
    if mask.ndim != 2 or mask.dtype != bool or factor not in FACTORS:
        raise ValueError("Need a 2D Boolean mask and a declared factor")
    blocks = block_average(mask.astype(float), factor)
    tie_fraction = float(np.mean(blocks == 0.5))
    observed = blocks >= 0.5 if ties_to_foreground else blocks > 0.5
    coarse_pixel_size = pixel_size * factor
    length = image_length(2.0 * observed.astype(float) - 1.0,
                          coarse_pixel_size)
    directional = np.asarray([length["length_x"], length["length_y"]])
    minimum_pixels_per_length = (
        float(np.min(directional) / coarse_pixel_size)
        if np.all(np.isfinite(directional)) else float("nan")
    )
    direction_ratio_x_over_y = (
        float(length["length_x"] / length["length_y"])
        if np.all(np.isfinite(directional)) and length["length_y"] > 0
        else float("nan")
    )
    return dict(factor=factor, phase_fraction=float(observed.mean()),
                tie_block_fraction=tie_fraction,
                length=length["length"], length_x=length["length_x"],
                length_y=length["length_y"],
                direction_ratio_x_over_y=direction_ratio_x_over_y,
                minimum_pixels_per_length=minimum_pixels_per_length,
                three_pixel_warning=(
                    "unresolved" if not np.isfinite(minimum_pixels_per_length)
                    else "flag" if minimum_pixels_per_length < 3.0
                    else "no flag"
                ),
                status="resolved" if length["resolved"] else "unresolved crossing")


def render_html(document: dict, rows: list[dict]) -> str:
    header = "".join(f"<th>{escape(name)}</th>" for name in
                     ("Image", "Specimen", "Mask authority", "ROI", "Time",
                      "Factor", "Pixel spacing", "Phase fraction", "Tie fraction",
                      "Fraction change",
                      "Mean length", "X length", "Y length", "Unit",
                      "X/Y geometry ratio",
                      "Length/native", "Change from native", "Min pixels/length",
                      "3-pixel screen", "Owner criterion", "Status"))
    body = []
    for row in rows:
        def number(value: float) -> str:
            return f"{value:.5g}" if np.isfinite(value) else "—"
        time = (f'{row["time"]} {row["time_unit"]}'
                if row["time"] != "" else "—")
        values = (escape(row["id"]), escape(row["specimen_id"]),
                  escape(row["mask_authority"]), escape(row["roi"]), escape(time),
                  f'{row["factor"]}×', number(row["pixel_size"]),
                  number(row["phase_fraction"]),
                  number(row["tie_block_fraction"]),
                  (f'{100.0 * row["phase_fraction_change"]:+.2f} pp'
                   if np.isfinite(row["phase_fraction_change"]) else "—"),
                  number(row["length"]),
                  number(row["length_x"]), number(row["length_y"]),
                  escape(row["length_unit"]),
                  number(row["direction_ratio_x_over_y"]),
                  number(row["length_ratio"]),
                  (f'{row["length_change_percent"]:+.2f}%'
                   if np.isfinite(row["length_change_percent"]) else "—"),
                  number(row["minimum_pixels_per_length"]),
                  escape(row["three_pixel_warning"]),
                  escape(row["decision_status"]),
                  escape(row["status"]))
        body.append("<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>")
    tolerance = document.get("decision_tolerance_fraction")
    tolerance_text = (
        "No owner-defined tolerance was declared, so the report does not label "
        "changes acceptable or unacceptable."
        if tolerance is None else
        f'The owner declared a {100.0 * tolerance:.3g}% relative-length tolerance: '
        f'{escape(document["decision_tolerance_reason"])}'
    )
    materials = document.get("materials_context")
    if materials is None:
        materials_html = (
            '<p class="notice"><b>Materials context not declared.</b> Treat this '
            'as a software or synthetic demonstration, not an applied materials '
            'result.</p>'
        )
    else:
        labels = {
            "material_system": "Material system",
            "processing_condition": "Processing / ageing condition",
            "imaging_method": "Imaging method",
            "section_geometry": "Section / acquisition geometry",
            "calibration_source": "Spatial calibration source",
            "measurement_purpose": "Intended materials measurement",
        }
        items = "".join(
            f'<dt>{escape(labels[key])}</dt><dd>{escape(materials[key])}</dd>'
            for key in MATERIALS_CONTEXT_FIELDS
        )
        materials_html = f'<h2>Declared materials context</h2><dl>{items}</dl>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phase-mask resolution audit</title><style>
body{{font:15px/1.5 system-ui,sans-serif;color:#19313a;background:#edf2f1;margin:0}}
main{{max-width:1000px;margin:24px auto;padding:28px;background:white}}
h1{{line-height:1.15}}.notice{{padding:12px;background:#fff2df;border-left:4px solid #af681d}}
.context,dl{{display:grid;grid-template-columns:minmax(180px,1fr) 3fr;gap:6px 18px}}
dt{{font-weight:700}}dd{{margin:0}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{text-align:left;padding:8px;border-bottom:1px solid #dce5e4;white-space:nowrap}}
@media(max-width:700px){{main{{margin:0;padding:18px}}}}</style></head><body><main>
<h1>Phase-mask resolution audit</h1>
{materials_html}
<p class="notice">A bounded test of one declared measurement on supplied 2D
masks. Downsampling a mask is not the same as re-imaging and re-segmenting a
specimen at lower instrumental resolution. This does not validate segmentation,
infer a particle radius, fit an ageing law, predict strength, or establish
independent specimens or lab use. The supplied physical pixel size is assumed
equal in the horizontal and vertical directions; non-square pixels need a
different measurement implementation. A binary phase-mask area fraction is
not generally the alloy's conserved chemical composition: the phases can have
different compositions and their area fractions can change while total solute
is conserved. Do not use this report as a chemical mass-balance test.</p>
<p><b>Source:</b> {escape(document["source"])}<br>
<b>Rights:</b> {escape(document["license"])}<br>
<b>Foreground phase:</b> {escape(document["phase_definition"])}<br>
<b>Tie rule:</b> {escape(document["tie_rule"])}</p>
<p><b>Decision criterion:</b> {tolerance_text}</p>
<p>Each image uses its own declared rectangular field at native, 2×, or 4×
resolution. Binary mask blocks are averaged and thresholded at one half;
physical pixel spacing scales with the factor. A 50:50 block follows the
declared tie rule. Unresolved correlation crossings remain visible. The
ratio is relative to that image's native measurement, not to another
specimen, and is not an uncertainty interval. Units are declared per image;
do not pool unlike units. Repeated slices from one specimen are not
independent samples.</p>
<p><b>Resolution screen:</b> the table also reports the smaller of the x/y
lengths in pixels. A value below three is flagged because the crossing is
being inferred from very few pixels. Three pixels is a deliberately
conservative diagnostic, not a universal accuracy threshold; passing it
does not prove that a measurement is accurate.</p>
<p>The X/Y ratio describes directional geometry in this selected 2D mask. It
is not a mechanical-property anisotropy, crystallographic texture measurement,
or substitute for a three-dimensional descriptor.</p>
<div class="scroll"><table><thead><tr>{header}</tr></thead>
<tbody>{''.join(body)}</tbody></table></div>
<p>The accompanying CSV records directional lengths, scale, region, status
and optional time metadata. The manifest records input and source hashes.
No mask pixels are embedded in this report.</p></main></body></html>"""


def audit(manifest_path: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory; do not overwrite an audit")
    document = json.loads(manifest_path.read_text())
    for key in ("source", "license", "phase_definition"):
        document[key] = _nonempty(document.get(key), key)
    materials = document.get("materials_context")
    if materials is not None:
        if not isinstance(materials, dict):
            raise ValueError("materials_context must be an object or null")
        document["materials_context"] = {
            key: _nonempty(materials.get(key), f"materials_context.{key}")
            for key in MATERIALS_CONTEXT_FIELDS
        }
    tie_rule = document.get("tie_rule")
    if tie_rule not in ("foreground", "background"):
        raise ValueError("Declare tie_rule as foreground or background")
    tolerance = document.get("decision_tolerance_fraction")
    if tolerance is not None:
        tolerance = _positive_number(tolerance, "decision_tolerance_fraction")
        document["decision_tolerance_fraction"] = tolerance
        document["decision_tolerance_reason"] = _nonempty(
            document.get("decision_tolerance_reason"),
            "decision_tolerance_reason",
        )
    records = document.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Declare at least one mask record")

    rows, hashes, seen, input_settings = [], {}, set(), []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every mask record must be an object")
        identifier = _nonempty(record.get("id"), "mask id")
        if identifier in seen:
            raise ValueError(f"Duplicate mask id: {identifier}")
        seen.add(identifier)
        specimen_id = _nonempty(record.get("specimen_id"), "specimen_id")
        path = manifest_path.parent / _nonempty(record.get("mask_path"), "mask_path")
        if not path.is_file():
            raise FileNotFoundError(path)
        foreground = record.get("foreground_value")
        background = record.get("background_value")
        if any(isinstance(v, bool) or not isinstance(v, int)
               for v in (foreground, background)):
            raise ValueError("Declare integer foreground_value and background_value")
        mask = load_mask(path, foreground, background)
        y0, y1, x0, x1 = _roi_bounds(record.get("roi"), mask.shape)
        roi_reason = _nonempty(record.get("roi_reason"), "ROI reason")
        if min(y1 - y0, x1 - x0) < 16:
            raise ValueError("The ROI must leave at least four pixels at 4× reduction")
        if (y1 - y0) % 4 or (x1 - x0) % 4:
            raise ValueError("The ROI must divide exactly by 4; no field is silently cropped")
        pixel_size = _positive_number(record.get("pixel_size"), "pixel_size")
        length_unit = _nonempty(record.get("length_unit"), "length_unit")
        mask_authority = _nonempty(record.get("mask_authority"), "mask_authority")
        time, time_unit = record.get("time", ""), record.get("time_unit", "")
        if time != "":
            if (isinstance(time, bool) or not isinstance(time, (int, float))
                    or not np.isfinite(time) or time < 0):
                raise ValueError("time must be finite and non-negative")
            time_unit = _nonempty(time_unit, "time_unit")
        elif time_unit != "":
            raise ValueError("time_unit requires time")
        field = mask[y0:y1, x0:x1].copy()
        hashes[identifier] = sha(path)
        declared_hash = record.get("sha256")
        if declared_hash is not None and declared_hash != hashes[identifier]:
            raise ValueError(f"{identifier}: mask changed since its hash was declared")
        input_settings.append(dict(
            id=identifier, specimen_id=specimen_id,
            mask_authority=mask_authority, roi=[y0, y1, x0, x1],
            roi_reason=roi_reason, pixel_size=pixel_size,
            length_unit=length_unit, foreground_value=foreground,
            background_value=background, time=time, time_unit=time_unit,
        ))
        measured = [measure(field, factor, pixel_size, tie_rule == "foreground")
                    for factor in FACTORS]
        native = measured[0]["length"]
        native_fraction = measured[0]["phase_fraction"]
        for item in measured:
            ratio = (item["length"] / native
                     if np.isfinite(item["length"]) and np.isfinite(native) else float("nan"))
            change_percent = ((ratio - 1.0) * 100.0
                              if np.isfinite(ratio) else float("nan"))
            phase_fraction_change = item["phase_fraction"] - native_fraction
            if not np.isfinite(ratio):
                decision_status = "unresolved"
            elif item["factor"] == 1:
                decision_status = "native reference"
            elif tolerance is None:
                decision_status = "not classified: no owner tolerance"
            elif abs(ratio - 1.0) <= tolerance:
                decision_status = "within owner tolerance"
            else:
                decision_status = "outside owner tolerance"
            rows.append(dict(id=identifier, specimen_id=specimen_id,
                             mask_authority=mask_authority, roi=json.dumps([y0, y1, x0, x1]),
                             roi_reason=roi_reason, time=time, time_unit=time_unit,
                             pixel_size=pixel_size * item["factor"], length_unit=length_unit,
                             foreground_value=foreground, background_value=background,
                             tie_rule=tie_rule, length_ratio=ratio,
                             length_change_percent=change_percent,
                             phase_fraction_change=phase_fraction_change,
                             decision_status=decision_status, **item))

    output.mkdir(parents=True)
    write_csv(output / "measurements.csv", rows)
    (output / "report.html").write_text(render_html(document, rows))
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        input_manifest_sha256=sha(manifest_path), mask_sha256=hashes,
        source=document["source"], license=document["license"],
        phase_definition=document["phase_definition"], tie_rule=tie_rule,
        materials_context=document.get("materials_context"),
        decision_tolerance_fraction=tolerance,
        decision_tolerance_reason=document.get("decision_tolerance_reason"),
        input_settings=input_settings,
        source_sha256={name: sha(Path(__file__).with_name(name)) for name in SOURCE_FILES},
        output_sha256={name: sha(output / name)
                       for name in ("measurements.csv", "report.html")},
        interpretation=("Static 2D phase-mask resolution sensitivity; phase area "
                        "fraction is not a chemical-composition mass balance; "
                        "not kinetic or alloy validation"),
    ), indent=2) + "\n")
    return output / "report.html"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(audit(arguments.manifest, arguments.output))
