"""Create a local, reviewer-readable sensitivity audit for calibrated 2D images.

This is an observation tool, not a phase classifier, alloy-property predictor,
or growth-law fitter. Every ROI and threshold must be declared by the user.
The optional previews embed image crops in HTML; only enable them for images
that may be shared with the report's intended readers.
"""

from __future__ import annotations

import argparse
import base64
from html import escape
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.imaging import block_average, image_length
from research.imaging_benchmark import sha, write_csv
from research.segmentation_sensitivity import _load_image, _validate_thresholds


SOURCE_FILES = (
    "image_audit_report.py",
    "imaging.py",
    "imaging_benchmark.py",
    "metrology.py",
    "segmentation_sensitivity.py",
)
FACTORS = (1, 2, 4)


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Declare a nonempty {label}")
    return value.strip()


def _positive_number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive number") from exc
    if not np.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive number")
    return number


def _roi_bounds(value: object, shape: tuple[int, int]) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4 or any(
        isinstance(v, bool) or not isinstance(v, int) for v in value
    ):
        raise ValueError("ROI must be [row_start,row_stop,col_start,col_stop] integers")
    y0, y1, x0, x1 = value
    if y0 < 0 or x0 < 0 or y1 > shape[0] or x1 > shape[1] or y1 - y0 < 4 or x1 - x0 < 4:
        raise ValueError("ROI must lie inside the image and leave at least four pixels per axis")
    return y0, y1, x0, x1


def _binary(gray: np.ndarray, threshold: float, foreground: str) -> np.ndarray:
    return gray >= threshold if foreground == "above" else gray < threshold


def _thumbnail(field: np.ndarray, *, binary: bool) -> str:
    """Base64 PNG for display only; never used by the numerical analysis."""
    if binary:
        pixels = np.asarray(field, dtype=np.uint8) * 255
    else:
        lo, hi = np.percentile(field, [1, 99])
        pixels = np.zeros(field.shape, dtype=np.uint8) if hi <= lo else np.uint8(
            np.clip((field - lo) * (255.0 / (hi - lo)), 0, 255)
        )
    image = Image.fromarray(pixels, mode="L")
    image.thumbnail((320, 320), Image.Resampling.NEAREST if binary else Image.Resampling.BILINEAR)
    stream = BytesIO()
    image.save(stream, format="PNG")
    return base64.b64encode(stream.getvalue()).decode("ascii")


def _render_html(document: dict, rows: list[dict], summaries: list[dict], previews: dict) -> str:
    title = "Microstructure measurement audit"
    metadata = (
        f"<p><b>Source:</b> {escape(document['source'])}<br>"
        f"<b>Licence:</b> {escape(document['license'])}<br>"
        f"<b>Declared phase:</b> {escape(document['phase_definition'])}</p>"
    )
    summary_html = []
    for item in summaries:
        span = (
            f"{item['length_min']:.4g}–{item['length_max']:.4g} {escape(item['length_unit'])}"
            if np.isfinite(item["length_min"]) else "unresolved"
        )
        parts = [
            f"<section><h2>{escape(item['id'])}</h2>",
            f"<p><b>ROI:</b> {escape(item['roi'])} — {escape(item['roi_reason'])}<br>",
            f"<b>Threshold rationale:</b> {escape(item['threshold_reason'])}<br>",
            f"<b>Raw-image length across declared thresholds:</b> {span} "
            f"({item['resolved_thresholds']}/{item['total_thresholds']} resolved)<br>",
            f"<b>Apparent phase fraction:</b> {item['fraction_min']:.3f}–{item['fraction_max']:.3f}</p>",
        ]
        if item["id"] in previews:
            gray, mask, threshold = previews[item["id"]]
            parts.extend([
                '<div class="previews">',
                f'<figure><img alt="Declared grayscale ROI" src="data:image/png;base64,{gray}"><figcaption>Grayscale ROI; display contrast rescaled only for this preview.</figcaption></figure>',
                f'<figure><img alt="Illustrative binary phase mask" src="data:image/png;base64,{mask}"><figcaption>Mask at declared preview threshold {threshold:g}; all thresholds are reported below.</figcaption></figure>',
                "</div>",
            ])
        parts.append("</section>")
        summary_html.append("".join(parts))

    headings = ("id", "time", "threshold", "binning", "phase fraction", "length", "x", "y", "length unit", "status")
    table_rows = []
    for row in rows:
        def show(number: float, decimals: int = 4) -> str:
            return f"{number:.{decimals}g}" if np.isfinite(number) else "—"

        values = (
            escape(row["id"]),
            "—" if row["time"] == "" else f"{show(row['time'])} {escape(row['time_unit'])}",
            show(row["threshold"]),
            f"{row['factor']}×",
            show(row["phase_fraction"]),
            show(row["length"]), show(row["length_x"]), show(row["length_y"]),
            escape(row["length_unit"]),
            escape(row["status"]),
        )
        table_rows.append("<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>")
    head = "".join(f"<th>{escape(label)}</th>" for label in headings)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>
body{{margin:0;background:#eef2f1;color:#18343b;font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1080px;margin:24px auto;background:white;padding:32px}}
h1{{margin:0 0 8px;font-size:28px}}h2{{font-size:19px;margin:0 0 8px}}
p{{margin:8px 0}}.notice{{background:#fff3df;border-left:4px solid #b06a16;padding:12px 16px}}
section{{border-top:1px solid #ccd8d8;padding:18px 0}}.previews{{display:flex;flex-wrap:wrap;gap:16px}}
figure{{margin:0;max-width:320px}}img{{display:block;max-width:100%;border:1px solid #ccd8d8}}
figcaption{{font-size:12px;color:#526568;margin-top:4px}}.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid #dce4e4;white-space:nowrap}}
th{{background:#e5eeec}}@media(max-width:700px){{main{{margin:0;padding:18px}}}}
</style></head><body><main><h1>{title}</h1>
<p class="notice">Exploratory 2D measurement sensitivity, not a validated phase classifier,
physical particle radius, alloy-property prediction or growth-law fit. ROI and
threshold choices require domain-expert review. No automatically chosen
“best” threshold or universal pass/fail score is supplied.</p>
{metadata}
<p>Every declared threshold is retained. “2×” and “4×” mean block averaging
<em>before</em> thresholding; pixel spacing is multiplied accordingly. A missing
measurement is shown as unresolved, never replaced by a convenient value.
Images at different times are not assumed registered or statistically
independent. Physical scale, phase identity and specimen geometry are
declarations, not inferred from pixels.</p>
{''.join(summary_html)}
<h2>All measurements</h2><div class="scroll"><table><thead><tr>{head}</tr></thead>
<tbody>{''.join(table_rows)}</tbody></table></div>
<p>Download the accompanying CSV and manifest for every value, file hash and
analysis-source hash. If previews were enabled, this HTML embeds image crops;
check permission before sharing it.</p></main></body></html>"""


def analyse(manifest_path: Path, output: Path, *, include_previews: bool = False) -> None:
    if output.exists():
        raise FileExistsError("Use a new output directory; previous results are immutable")
    document = json.loads(manifest_path.read_text())
    for key in ("source", "license", "phase_definition"):
        document[key] = _nonempty(document.get(key), key)
    records = document.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Declare at least one image record")

    rows: list[dict] = []
    summaries: list[dict] = []
    previews: dict = {}
    image_hashes: dict = {}
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each image record must be an object")
        identifier = _nonempty(record.get("id"), "image id")
        if identifier in seen:
            raise ValueError(f"Duplicate image id: {identifier}")
        seen.add(identifier)
        relative_path = _nonempty(record.get("path"), "image path")
        path = manifest_path.parent / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        image = _load_image(path)
        roi = _roi_bounds(record.get("roi"), image.shape)
        roi_reason = _nonempty(record.get("roi_reason"), "ROI reason")
        threshold_reason = _nonempty(record.get("threshold_reason"), "threshold reason")
        pixel_size = _positive_number(record.get("pixel_size"), "pixel_size")
        length_unit = _nonempty(record.get("length_unit"), "length_unit")
        thresholds = _validate_thresholds(record.get("thresholds"))
        foreground = record.get("foreground")
        if foreground not in ("above", "below"):
            raise ValueError("foreground must be 'above' or 'below'")
        time = record.get("time", "")
        time_unit = record.get("time_unit", "")
        if time != "":
            if isinstance(time, bool) or not isinstance(time, (int, float)) or not np.isfinite(time) or time < 0:
                raise ValueError("time must be finite and non-negative")
            time_unit = _nonempty(time_unit, "time_unit")
        elif time_unit != "":
            raise ValueError("time_unit requires time")
        if include_previews:
            preview_threshold = record.get("preview_threshold")
            if preview_threshold not in thresholds:
                raise ValueError("Declare preview_threshold as one of the thresholds")

        y0, y1, x0, x1 = roi
        gray = image[y0:y1, x0:x1].copy()
        image_hashes[identifier] = sha(path)
        raw_lengths = []
        raw_fractions = []
        for factor in FACTORS:
            reason = ""
            try:
                reduced = block_average(gray, factor)
            except ValueError as exc:
                reduced = None
                reason = f"not measured: {exc}"
            for threshold in thresholds:
                base = dict(
                    id=identifier, time=time, time_unit=time_unit, threshold=threshold,
                    foreground=foreground, factor=factor, pixel_size=pixel_size * factor,
                    length_unit=length_unit, roi=json.dumps(roi),
                )
                if reduced is None:
                    measured = dict(phase_fraction=float("nan"), length=float("nan"),
                                    length_x=float("nan"), length_y=float("nan"), status=reason)
                else:
                    mask = _binary(reduced, threshold, foreground)
                    length = image_length(2.0 * mask.astype(float) - 1.0, pixel_size * factor)
                    measured = dict(
                        phase_fraction=float(mask.mean()),
                        length=length["length"], length_x=length["length_x"],
                        length_y=length["length_y"],
                        status="resolved" if length["resolved"] else "unresolved crossing",
                    )
                    if factor == 1:
                        raw_lengths.append(length["length"])
                        raw_fractions.append(float(mask.mean()))
                rows.append({**base, **measured})

        finite = np.asarray(raw_lengths)[np.isfinite(raw_lengths)]
        summaries.append(dict(
            id=identifier, roi=json.dumps(roi), roi_reason=roi_reason,
            threshold_reason=threshold_reason, length_unit=length_unit,
            length_min=float(finite.min()) if len(finite) else float("nan"),
            length_max=float(finite.max()) if len(finite) else float("nan"),
            resolved_thresholds=len(finite), total_thresholds=len(thresholds),
            fraction_min=float(min(raw_fractions)), fraction_max=float(max(raw_fractions)),
        ))
        if include_previews:
            previews[identifier] = (
                _thumbnail(gray, binary=False),
                _thumbnail(_binary(gray, preview_threshold, foreground), binary=True),
                float(preview_threshold),
            )

    output.mkdir(parents=True)
    write_csv(output / "measurements.csv", rows)
    write_csv(output / "summaries.csv", summaries)
    source_hashes = {name: sha(Path(__file__).with_name(name)) for name in SOURCE_FILES}
    (output / "manifest.json").write_text(json.dumps(dict(
        input_manifest_sha256=sha(manifest_path), image_sha256=image_hashes,
        source=document["source"], license=document["license"],
        phase_definition=document["phase_definition"], source_hashes=source_hashes,
        previews_embedded=include_previews,
    ), indent=2) + "\n")
    (output / "report.html").write_text(_render_html(document, rows, summaries, previews))
    print(output / "report.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-previews", action="store_true",
                        help="Embed image crops in HTML; check sharing permission first")
    arguments = parser.parse_args()
    analyse(arguments.manifest, arguments.output, include_previews=arguments.include_previews)
