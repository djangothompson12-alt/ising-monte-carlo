"""Audit resolution sensitivity of declared, expert-supplied 2D phase masks.

This is a local measurement check, not a segmentation algorithm, an ageing
kinetics fit, an alloy-property predictor, a chemical mass-balance test, or
evidence of laboratory adoption. Masks and physical scale are supplied by the
user; no image pixels are copied into the HTML or CSV output.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, __version__ as pillow_version
import scipy

from research.mask_audit_io import _nonempty, _positive_number, _roi_bounds, sha, write_csv
from research.imaging import block_average
from research.mask_metrology import binary_image_length


FACTORS = (1, 2, 4)
DECISION_SCOPES = ("mean_length", "both_directions")
SOURCE_FILES = ("mask_resolution_audit.py", "mask_audit_io.py", "imaging.py",
                "mask_metrology.py", "metrology.py")
MATERIALS_CONTEXT_FIELDS = (
    "material_system",
    "processing_condition",
    "imaging_method",
    "section_geometry",
    "calibration_source",
    "measurement_purpose",
)


def _mask_snapshot(path: Path, foreground_value: int,
                   background_value: int) -> tuple[np.ndarray, str]:
    """Measure and hash the same bytes, even if the source later changes."""
    payload = path.read_bytes()
    stream = BytesIO(payload)
    if path.suffix.lower() == ".npy":
        array = np.load(stream, allow_pickle=False)
    else:
        with Image.open(stream) as image:
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError(f"{path}: select and save one 2D mask plane; multi-frame images are not accepted")
            array = np.asarray(image)
    if array.ndim != 2 or min(array.shape) < 16:
        raise ValueError(f"{path}: mask must be a single 2D plane at least 16 pixels wide")
    if foreground_value == background_value:
        raise ValueError("Foreground and background values must differ")
    if not np.all((array == foreground_value) | (array == background_value)):
        raise ValueError(f"{path}: undeclared label, nonfinite value, or antialiased pixel")
    return array == foreground_value, hashlib.sha256(payload).hexdigest()


def load_mask(path: Path, foreground_value: int, background_value: int) -> np.ndarray:
    """Read an explicit two-label mask; never infer polarity from appearance."""
    return _mask_snapshot(path, foreground_value, background_value)[0]


def measure(mask: np.ndarray, factor: int, pixel_size: float,
            ties_to_foreground: bool) -> dict:
    if mask.ndim != 2 or mask.dtype != bool or factor not in FACTORS:
        raise ValueError("Need a 2D Boolean mask and a declared factor")
    blocks = block_average(mask.astype(float), factor)
    tie_fraction = float(np.mean(blocks == 0.5))
    observed = blocks >= 0.5 if ties_to_foreground else blocks > 0.5
    coarse_pixel_size = pixel_size * factor
    length = binary_image_length(observed, coarse_pixel_size)
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
                exact_half_height_checks=length["exact_half_height_checks"],
                direction_ratio_x_over_y=direction_ratio_x_over_y,
                minimum_pixels_per_length=minimum_pixels_per_length,
                three_pixel_warning=(
                    "unresolved" if not np.isfinite(minimum_pixels_per_length)
                    else "flag" if minimum_pixels_per_length < 3.0
                    else "no flag"
                ),
                status="resolved" if length["resolved"] else "unresolved crossing")


def compare_lengths(item: dict, native: dict, tolerance: float | None,
                    scope: str = "mean_length") -> dict:
    """Compare paired observables, not accuracy against physical truth.

    Mean-only agreement can conceal opposite x/y changes. Keep the legacy
    mean decision as the default, but expose both axes and allow a declared
    requirement that each directional length meet the same tolerance.
    """
    if scope not in DECISION_SCOPES:
        raise ValueError("decision_scope must be mean_length or both_directions")
    if tolerance is not None:
        tolerance = _positive_number(tolerance, "decision_tolerance_fraction")
    result = {}
    for name in ("length", "length_x", "length_y"):
        value, reference = item[name], native[name]
        ratio = (float(value / reference)
                 if np.isfinite(value) and value > 0
                 and np.isfinite(reference) and reference > 0 else float("nan"))
        result[name + "_ratio"] = ratio
        result[name + "_change_percent"] = 100.0 * (ratio - 1.0)
    axis_changes = np.array([result["length_x_change_percent"],
                             result["length_y_change_percent"]])
    result["max_directional_change_percent"] = (
        float(np.max(np.abs(axis_changes)))
        if np.all(np.isfinite(axis_changes)) else float("nan")
    )
    ratios = ([result["length_ratio"]] if scope == "mean_length" else
              [result["length_x_ratio"], result["length_y_ratio"]])
    if not np.all(np.isfinite(ratios)):
        status = "unresolved"
    elif item["factor"] == 1:
        status = "native reference"
    elif tolerance is None:
        status = "not classified: no owner tolerance"
    elif all(abs(ratio - 1.0) <= tolerance + 8 * np.finfo(float).eps * max(1.0, abs(ratio), tolerance)
             for ratio in ratios):
        status = "within owner tolerance"
    else:
        status = "outside owner tolerance"
    return dict(**result, decision_scope=scope, decision_status=status)


def tie_summary(selected: dict, opposite: dict, native: dict,
                tolerance: float | None, scope: str) -> dict:
    """Report sensitivity to both exact-tie conventions on the same field.

    No convention is selected for its result. These two cases are not a
    statistical interval, a search over all segmentation thresholds, or a
    validation of the three-pixel warning.
    """
    chosen = compare_lengths(selected, native, tolerance, scope)
    alternative = compare_lengths(opposite, native, tolerance, scope)
    statuses = [chosen["decision_status"], alternative["decision_status"]]
    within = "within owner tolerance"
    outside = "outside owner tolerance"
    resolution_warning = any(item["three_pixel_warning"] != "no flag"
                             for item in (native, selected, opposite))
    if "unresolved" in statuses:
        criterion = "unresolved comparison"
    elif tolerance is None:
        criterion = "no owner tolerance"
    elif statuses == [within, within]:
        criterion = "within tolerance under both tie rules"
    elif statuses == [outside, outside]:
        criterion = "outside tolerance under both tie rules"
    else:
        criterion = "criterion depends on tie rule"
    if criterion == "unresolved comparison":
        action = "Review unresolved length"
    elif resolution_warning:
        action = "Review image resolution before relying on agreement"
    elif criterion == "no owner tolerance":
        action = "Define a useful tolerance before making a decision"
    elif criterion == "criterion depends on tie rule":
        action = "Document and justify the tie rule; conclusion changes"
    elif criterion == "outside tolerance under both tie rules":
        action = "Retain native mask for this declared comparison"
    else:
        action = "Declared criterion met; confirm suitability with image owner"
    return dict(factor=selected["factor"],
                selected_mean_change_percent=chosen["length_change_percent"],
                opposite_mean_change_percent=alternative["length_change_percent"],
                selected_max_directional_change_percent=chosen["max_directional_change_percent"],
                opposite_max_directional_change_percent=alternative["max_directional_change_percent"],
                selected_decision=chosen["decision_status"],
                opposite_decision=alternative["decision_status"],
                selected_fraction_change=selected["phase_fraction"] - native["phase_fraction"],
                opposite_fraction_change=opposite["phase_fraction"] - native["phase_fraction"],
                tie_block_fraction=selected["tie_block_fraction"],
                criterion=criterion, any_resolution_warning=resolution_warning,
                next_action=action, decision_scope=scope)


def render_html(document: dict, rows: list[dict], summaries: list[dict] | None = None) -> str:
    header = "".join(f"<th>{escape(name)}</th>" for name in
                     ("Image", "Specimen", "Mask authority", "ROI", "Time",
                      "Factor", "Pixel spacing", "Phase fraction", "Tie fraction",
                      "Fraction change",
                      "Mean length", "X length", "Y length", "Unit",
                      "X/Y geometry ratio",
                      "Length/native", "Change from native", "X change", "Y change",
                      "Max absolute directional change", "Min pixels/length",
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
                  (f'{row["length_x_change_percent"]:+.2f}%'
                   if np.isfinite(row["length_x_change_percent"]) else "—"),
                  (f'{row["length_y_change_percent"]:+.2f}%'
                   if np.isfinite(row["length_y_change_percent"]) else "—"),
                  (f'{row["max_directional_change_percent"]:.2f}%'
                   if np.isfinite(row["max_directional_change_percent"]) else "—"),
                  number(row["minimum_pixels_per_length"]),
                  escape(row["three_pixel_warning"]),
                  escape(row["decision_status"]),
                  escape(row["status"]))
        body.append("<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>")
    tolerance = document.get("decision_tolerance_fraction")
    scope_text = ("mean of horizontal and vertical lengths"
                  if document.get("decision_scope", "mean_length") == "mean_length"
                  else "each horizontal and vertical length separately")
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
    summary_table = ""
    if summaries:
        summary_body = []
        for row in summaries:
            def percent(value):
                return f"{value:+.2f}%" if np.isfinite(value) else "—"
            def changes(mean, maximum):
                axis = f"{maximum:.2f}%" if np.isfinite(maximum) else "—"
                return f'Mean {percent(mean)}<br>Largest axis {axis}'
            values = (escape(row["id"]), f'{row["factor"]}×',
                      changes(row["selected_mean_change_percent"],
                              row["selected_max_directional_change_percent"]),
                      changes(row["opposite_mean_change_percent"],
                              row["opposite_max_directional_change_percent"]),
                      escape(row["criterion"]),
                      "review required" if row["any_resolution_warning"] else "no current flag",
                      escape(row["next_action"]))
            summary_body.append("<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>")
        summary_table = f'''<h2>What to check next</h2>
<p>The declared tie rule remains the primary result. The opposite exact-tie
rule is also checked on the same field, automatically. If the tolerance result
changes, the report exposes that dependency. The two cases are sensitivity
checks, not an uncertainty interval or evidence of a unique correct segmentation.</p>
<div class="scroll"><table class="decision"><thead><tr><th>Image</th><th>Factor</th>
<th>Declared rule: length changes</th><th>Opposite rule: length changes</th>
<th>Declared criterion</th><th>Resolution screen</th><th>Next action</th>
</tr></thead><tbody>{''.join(summary_body)}</tbody></table></div>
<p>Criterion decisions use the declared mean-only or both-directions scope.
The detailed CSV includes both directional changes under both tie rules. A
small mean change can conceal opposite directional changes.</p>'''
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
.decision th,.decision td{{white-space:normal;vertical-align:top}}
.decision td:last-child{{min-width:180px}}
@media(max-width:700px){{main{{margin:0;padding:18px}}}}</style></head><body><main>
<h1>Phase-mask resolution audit</h1>
<p><b>Question:</b> Does digital 2× or 4× reduction preserve this mask's
declared correlation-length measurement within the owner's tolerance?</p>
<p><b>Decision criterion:</b> {tolerance_text}<br>
<b>Decision scope:</b> {scope_text}. <b>Declared tie rule:</b> {escape(document["tie_rule"])}.</p>
{summary_table}
<p class="notice">Agreement is relative to the supplied native mask.
Check resolution warnings before relying on a small percentage change.
Digital mask reduction is a different test from changing microscope resolution.</p>
<details><summary><b>Data source and materials context</b></summary>
{materials_html}
<p><b>Source:</b> {escape(document["source"])}<br>
<b>Rights:</b> {escape(document["license"])}<br>
<b>Foreground phase:</b> {escape(document["phase_definition"])}</p></details>
<details><summary><b>Calculation, assumptions and limits</b></summary>
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
<p><b>Decision scope:</b> {scope_text}. Opposite changes in the two directions
can cancel in the mean; the directional changes are therefore shown separately.
Agreement with the native mask is a sensitivity check, not proof of physical
accuracy. A tolerance decision does not override an unresolved or low-resolution
warning.</p>
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
or substitute for a three-dimensional descriptor.</p></details>
<details><summary><b>Full primary measurement table</b></summary>
<div class="scroll"><table><thead><tr>{header}</tr></thead>
<tbody>{''.join(body)}</tbody></table></div></details>
<p>The accompanying CSV records directional lengths, scale, region, status
and optional time metadata. The decision-summary and tie-sensitivity CSVs
retain both tie conventions. The manifest records input and source hashes.
No mask pixels are embedded in this report.</p></main></body></html>"""


def audit(manifest_path: Path, output: Path) -> Path:
    if output.exists():
        raise FileExistsError("Choose a new output directory; do not overwrite an audit")
    manifest_bytes = manifest_path.read_bytes()
    document = json.loads(manifest_bytes)
    source_hashes = {name: sha(Path(__file__).with_name(name)) for name in SOURCE_FILES}
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
    scope = document.get("decision_scope", "mean_length")
    if scope not in DECISION_SCOPES:
        raise ValueError("decision_scope must be mean_length or both_directions")
    document["decision_scope"] = scope
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
    sensitivity_rows, summaries = [], []
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
        mask, mask_digest = _mask_snapshot(path, foreground, background)
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
        hashes[identifier] = mask_digest
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
        native = measured[0]
        native_fraction = measured[0]["phase_fraction"]
        for item in measured:
            comparison = compare_lengths(item, native, tolerance, scope)
            phase_fraction_change = item["phase_fraction"] - native_fraction
            rows.append(dict(id=identifier, specimen_id=specimen_id,
                             mask_authority=mask_authority, roi=json.dumps([y0, y1, x0, x1]),
                             roi_reason=roi_reason, time=time, time_unit=time_unit,
                             pixel_size=pixel_size * item["factor"], length_unit=length_unit,
                             foreground_value=foreground, background_value=background,
                             tie_rule=tie_rule,
                             phase_fraction_change=phase_fraction_change,
                             **comparison, **item))
        for selected in measured[1:]:
            opposite = measure(field, selected["factor"], pixel_size,
                               tie_rule != "foreground")
            summaries.append(dict(id=identifier, specimen_id=specimen_id,
                                  selected_tie_rule=tie_rule,
                                  opposite_tie_rule=("foreground" if tie_rule == "background" else "background"),
                                  **tie_summary(selected, opposite, native, tolerance, scope)))
            for variant, item in (("declared", selected), ("opposite", opposite)):
                sensitivity_rows.append(dict(
                    id=identifier, specimen_id=specimen_id, variant=variant,
                    tie_rule=tie_rule if variant == "declared" else
                    ("foreground" if tie_rule == "background" else "background"),
                    pixel_size=pixel_size * item["factor"], length_unit=length_unit,
                    phase_fraction_change=item["phase_fraction"] - native_fraction,
                    **compare_lengths(item, native, tolerance, scope), **item))

    if source_hashes != {name: sha(Path(__file__).with_name(name)) for name in SOURCE_FILES}:
        raise RuntimeError("Analysis sources changed during this audit; use a stable version and rerun")
    output.mkdir(parents=True)
    write_csv(output / "measurements.csv", rows)
    write_csv(output / "tie_sensitivity.csv", sensitivity_rows)
    write_csv(output / "decision_summary.csv", summaries)
    (output / "report.html").write_text(render_html(document, rows, summaries))
    (output / "manifest.json").write_text(json.dumps(dict(
        created_utc=datetime.now(timezone.utc).isoformat(),
        input_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(), mask_sha256=hashes,
        source=document["source"], license=document["license"],
        phase_definition=document["phase_definition"], tie_rule=tie_rule,
        materials_context=document.get("materials_context"),
        decision_tolerance_fraction=tolerance,
        decision_scope=scope,
        decision_tolerance_reason=document.get("decision_tolerance_reason"),
        method_version="binary-half-height-and-tie-audit-2026-10-13",
        numerical_convention=("Finite covariance with exact binary pair counts at FFT lags "
                              "within 1e-12 of half height; first descending bracket from "
                              ">=0.5 to <0.5 with linear interpolation; tolerance comparisons "
                              "allow eight float64 epsilons for roundoff, not measurement uncertainty"),
        sensitivity_convention=("Declared rule is primary; opposite 50:50 block-tie rule "
                                "is always checked on the same field; no best-rule selection"),
        versions=dict(python=sys.version.split()[0], numpy=np.__version__,
                      scipy=scipy.__version__, pillow=pillow_version),
        provenance_convention="Input and mask hashes identify the exact byte snapshots parsed and measured",
        input_settings=input_settings,
        source_sha256=source_hashes,
        output_sha256={name: sha(output / name)
                       for name in ("measurements.csv", "report.html", "tie_sensitivity.csv",
                                    "decision_summary.csv")},
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
