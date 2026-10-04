"""Render the current two-page criticism brief, without changing frozen results.

Requires reportlab, Pillow and numpy. The artifact runtime supplies these.
Numbers and the chart are read from hash-checked fresh-cohort outputs. This
builder does not rerun simulations, certify novelty, or claim student approval.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = Path("research/results/growth_reliability_fresh_2026-09-19_v1")
RAW = Path("research/runs/growth_reliability_holdout_v1")
FREEZE = Path("research/results/growth_reliability_freeze_2026-09-19_v1.json")
TEAL = "#176568"
INK = "#172c35"
GREY = "#52626a"
ORANGE = "#a35220"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def load_evidence(root):
    folder = root / ANALYSIS
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["cohort"] != "fresh" or manifest["independent_replica_count"] != 16:
        raise ValueError("Expected the separate 16-run fresh cohort")
    for name, digest in manifest["outputs"].items():
        if sha(folder / name) != digest:
            raise ValueError(f"Frozen analysis output changed: {name}")
    if sha(root / FREEZE) != manifest["freeze_sha256"]:
        raise ValueError("Freeze record does not match the analysis")
    fits = read_rows(folder / "fits.csv")
    primary = [r for r in fits if (r["factor"], r["origin"], r["observable"], r["stage"])
               == ("4", "0", "half", "matched")]
    primary.sort(key=lambda r: -float(r["composition"]))
    if [r["composition"] for r in primary] != ["0.5", "0.15"]:
        raise ValueError("Expected exactly two primary comparisons")
    for row in primary:
        if ((row["trajectories"], row["retained_points"], row["first_sweep"], row["last_sweep"])
                != ("8", "24", "1119", "20000")):
            raise ValueError("Primary cohort or retained time grid changed")
    observations = read_rows(folder / "observations.csv")
    if len(observations) != 36864 or len(fits) != 144:
        raise ValueError("Incomplete analysis inventory")
    curves = []
    for fit in primary:
        selected = [r for r in observations if r["composition"] == fit["composition"]
                    and r["factor"] == "4" and r["origin"] == "0"]
        times = sorted({int(r["sweep"]) for r in selected})
        points = []
        for time in times:
            native = [float(r["half"]) for r in selected
                      if int(r["sweep"]) == time and r["stage"] == "native"]
            matched = [float(r["half"]) for r in selected
                       if int(r["sweep"]) == time and r["stage"] == "matched"]
            if len(native) != 8 or len(matched) != 40:
                raise ValueError("Unexpected replica/tie counts in plot")
            points.append((time, mean(matched) / mean(native)))
        if len(points) != 24:
            raise ValueError("Plot must use the exact common 24 checkpoints")
        for result, key in ((points[0][1], "ratio_first"), (points[-1][1], "ratio_last")):
            if not math.isclose(result, float(fit[key]), rel_tol=1e-12):
                raise ValueError("Figure endpoints do not match fitted evidence")
        curves.append((fit["composition"], points))
    return manifest, primary, curves


def snapshot_images(root, manifest):
    """A fixed illustration: first sorted 50:50 trajectory, first fitted time."""
    import numpy as np
    from PIL import Image

    name = "c0_L128_rep000.npz"
    path = root / RAW / name
    if sha(path) != manifest["input_sha256"][name]:
        raise ValueError("Illustration archive changed")
    with np.load(path, allow_pickle=False) as data:
        index = np.flatnonzero(data["t"] == 1119)
        if len(index) != 1:
            raise ValueError("Illustration checkpoint missing")
        native = (data["snapshots"][index[0]].astype(float) + 1) / 2
    grey = native.reshape(32, 4, 32, 4).mean(axis=(1, 3))
    # Independent, full-sort implementation of the declared seed-110 tie rule.
    flat = grey.ravel()
    priority = np.random.default_rng(110).random(flat.size)
    ranked = np.lexsort((priority, -flat))
    count = int(np.floor(native.mean() * flat.size + .5))
    matched = np.zeros(flat.size, dtype=float)
    matched[ranked[:count]] = 1
    matched = matched.reshape(grey.shape)
    if float(native.mean()) != .5 or float(matched.mean()) != .5:
        raise ValueError("Illustration must preserve the 50:50 count exactly")
    result = []
    for a in (native, grey, matched):
        buffer = io.BytesIO()
        Image.fromarray(np.rint(a * 255).astype("uint8")).resize(
            (384, 384), Image.Resampling.NEAREST).save(buffer, format="PNG")
        buffer.seek(0)
        result.append(buffer)
    return result, {"archive": str(RAW / name), "sha256": sha(path),
                    "sweep": 1119, "tie_seed": 110,
                    "selection": "First sorted 50:50 trajectory, first retained fitted checkpoint"}


def load_context(root):
    """Read contextual numbers from their own cohorts; never pool with primary."""
    extension = Path("research/runs/main_065_multisize_v1/analysis_declared_v1/fit_windows.csv")
    late = [r for r in read_rows(root / extension) if
            (r["L"], r["method"], r["nominal_t_min"], r["nominal_t_max"]) ==
            ("128", "primary_unfiltered", "20000", "1000000")]
    late.sort(key=lambda r: -float(r["composition"]))
    if len(late) != 2 or any(r["n_replicas"] != "16" for r in late):
        raise ValueError("Unexpected long-run context")
    sources = {str(extension): sha(root / extension)}
    fem = []
    for folder in ("fem_mask_audit_2026-09-22_v2",
                   "fem_mask_audit_2026-09-22_tie_foreground_sensitivity_v1"):
        base = root / "output" / folder
        path = base / "field_summary.csv"
        provenance_path = base / "replay_provenance.json"
        if provenance_path.exists():
            provenance = json.loads(provenance_path.read_text())
            if sha(path) != provenance["field_summary_sha256"]:
                raise ValueError("FeM summary changed")
        rows = read_rows(path)
        if [r["factor"] for r in rows] != ["1", "2", "4"] or any(r["fields"] != "81" for r in rows):
            raise ValueError("Unexpected FeM field inventory")
        measurements = read_rows(base / "audit/measurements.csv")
        audit_manifest = json.loads((base / "audit/manifest.json").read_text())
        if sha(base / "audit/measurements.csv") != audit_manifest["output_sha256"]["measurements.csv"]:
            raise ValueError("FeM field measurements changed")
        for row in rows:
            field_values = [float(r["length_change_percent"]) for r in measurements
                            if r["factor"] == row["factor"]]
            if len(field_values) != 81 or not math.isclose(median(field_values),
                    float(row["length_change_percent_median"]), abs_tol=1e-12):
                raise ValueError("FeM median does not reproduce from field values")
        fem.append(rows)
        for name in ("field_summary.csv", "audit/measurements.csv", "audit/manifest.json"):
            sources[str((base / name).relative_to(root))] = sha(base / name)
    return {"late": late, "fem": fem, "sources": sources}


def ratio_chart(curves, width=489, height=145):
    from reportlab.graphics.shapes import Drawing, Line, PolyLine, String
    from reportlab.lib.colors import HexColor

    d = Drawing(width, height)
    left, bottom, right, top = 43, 28, width - 13, height - 22
    x = lambda t: left + (math.log10(t)-3) / (math.log10(20000)-3) * (right-left)
    y = lambda r: bottom + (r-1) / .5 * (top-bottom)
    d.add(String(left, height-9, "Matched / native ensemble-mean length", fontName="Helvetica-Bold", fontSize=9, fillColor=HexColor(INK)))
    for v in (1, 1.2, 1.4):
        d.add(Line(left, y(v), right, y(v), strokeColor=HexColor("#dbe3e5"), strokeWidth=.5))
        d.add(String(left-8, y(v)-3, f"{v:.1f}", textAnchor="end", fontSize=8, fillColor=HexColor(GREY)))
    for t, label in ((1000,"1,000"),(5000,"5,000"),(20000,"20,000")):
        d.add(String(x(t), bottom-12, label, textAnchor="middle", fontSize=8, fillColor=HexColor(GREY)))
    d.add(String((left+right)/2, 1, "Post-quench sweeps (log scale)", textAnchor="middle", fontSize=8, fillColor=HexColor(GREY)))
    for i, (composition, points) in enumerate(curves):
        color = HexColor(TEAL if i == 0 else ORANGE)
        coordinates = [coordinate for t,r in points for coordinate in (x(t), y(r))]
        d.add(PolyLine(coordinates, strokeColor=color, strokeWidth=1.8))
        label = "50:50" if composition == "0.5" else "15:85"
        d.add(Line(right-130+i*72, top+9, right-113+i*72, top+9, strokeColor=color, strokeWidth=1.8))
        d.add(String(right-109+i*72, top+6, label, fontSize=8, fillColor=color))
    return d


def build(root, output):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
    from pypdf import PdfReader

    if output.exists() or output.with_suffix(".provenance.json").exists():
        raise FileExistsError("Choose a new output PDF; existing review copies are retained")
    manifest, primary, curves = load_evidence(root)
    context = load_context(root)
    pictures, illustration = snapshot_images(root, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = {
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=12.9, textColor=colors.HexColor(INK), spaceAfter=6),
        "small": ParagraphStyle("Small", fontName="Helvetica", fontSize=8, leading=10.4, textColor=colors.HexColor(GREY), spaceAfter=5),
        "section": ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor(TEAL), spaceBefore=9, spaceAfter=5),
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=23, leading=26, textColor=colors.HexColor(INK), spaceAfter=9),
    }
    story = []
    def p(text, style="body"):
        story.append(Paragraph(text, styles[style]))
    def h(text):
        p(text, "section")

    p("TECHNICAL CRITICISM DRAFT | 1 OCTOBER 2026", "small")
    p("Does preserving species fraction<br/>preserve measured coarsening?", "title")
    p("Django Thompson | Student project | AI-assisted draft; student approval pending", "small")
    h("The question")
    p("After reducing image resolution, is matching the original species fraction enough to preserve a fitted finite-window coarsening exponent? The comparison is with the <b>original image measurement</b>, not with a forced value of 1/3. Lower early slopes in Kawasaki simulations motivated this question; this experiment does not settle every cause of that original shortfall.")
    labels = ["Original: 128 x 128", "4 x 4 block means: 32 x 32", "Fraction-matched: 32 x 32"]
    rows = [[Paragraph(label, styles["small"]) for label in labels],
            [Image(b, width=100, height=100) for b in pictures]]
    table = Table(rows, colWidths=[163]*3)
    table.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("BOTTOMPADDING",(0,0),(-1,-1),2),("TOPPADDING",(0,0),(-1,-1),0)]))
    story.append(table)
    p("<b>Figure 1.</b> The same 50:50 snapshot, not three simulations. A fixed example uses the first trajectory at 1,119 sweeps and tie priority 110. White-site fraction is 0.5 in both binary images; averaging retains grey values. The example illustrates the operation, not the statistical result.", "small")
    h("The controlled test")
    p("Sixteen fresh independent trajectories (eight per mixture) used a 128 x 128 periodic lattice, Kawasaki exchange with Metropolis acceptance and Jx = Jy = 1. After 200 preparation sweeps at 3 Tc, each was quenched to 0.65 Tc. A protocol and source hashes were fixed before these runs, after an earlier processing effect was known. The primary comparison uses 24 common checkpoints from 1,119 to 20,000 post-quench sweeps.")
    result_rows = [[Paragraph(s, styles["small"]) for s in
                    ("Mixture", "Original exponent", "Matched exponent", "Difference [95% interval]")]]
    for row in primary:
        result_rows.append(["50:50" if row["composition"] == "0.5" else "15:85",
                            f'{float(row["native_alpha"]):.5f}', f'{float(row["alpha"]):.5f}',
                            f'{float(row["delta"]):.5f} [{float(row["low"]):.5f}, {float(row["high"]):.5f}]'])
    table = Table(result_rows, colWidths=[48,105,105,231])
    table.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,1),(-1,-1),9),
        ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor(INK)),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#edf3f3")),
        ("LINEBELOW",(0,-1),(-1,-1),.5,colors.HexColor("#bccccc")),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.append(table)
    story.append(Spacer(1,7))
    p("<b>Main finding:</b> at fourfold reduction, fraction matching did not preserve the original fitted exponent. Matching is exact at 50:50; the 15:85 coarse fraction is rounded to the nearest attainable pixel count. Finer reduction can give much smaller differences: this is not a claim that matching never helps.")
    p("Intervals use 1,000 paired whole-trajectory bootstrap draws, not independent checkpoints. They quantify run-sampling uncertainty conditional on this analysis, not uncertainty in real-alloy physics.", "small")
    h("Why use this short window when longer runs exist?")
    late = context["late"]
    p(f"A separate 128-trajectory campaign reached one million sweeps across four lattice sizes and two mixtures. At L = 128 its periodic half-height fits over {int(late[0]['used_t_min']):,}-1,000,000 sweeps were {float(late[0]['alpha']):.3f} (50:50) and {float(late[1]['alpha']):.3f} (15:85). Another 40-run, 0.6 Tc reference campaign reached 4.5 million sweeps; its literature-matched analysis is unfinished. Neither establishes an asymptotic plateau. The short test above isolates observation changes on identical snapshots in a deliberately demanding resolution regime; it is not the entire simulation study.", "small")
    story.append(PageBreak())

    p("METHOD, LIMITATIONS AND QUESTIONS FOR REVIEW", "small")
    story.append(ratio_chart(curves, height=115))
    p("<b>Figure 2.</b> Fresh trajectories only; each curve is the ratio of ensemble-mean lengths. The ratio decreases with time, so early lengths are inflated more than late ones and the fitted slope is reduced. Constant multiplicative length error would leave the slope unchanged. This accounting identity does not identify a unique geometric cause.", "small")
    h("How the measurement works")
    p("Lengths are the mean X/Y half-height crossings of variance-normalized, mean-subtracted covariance, using valid pairs without wrapping image edges. Coarse lengths are converted to original lattice spacing. Log ensemble-mean length is fitted against log sweeps on shared times. Rank segmentation retains the highest block means; five fixed tie priorities are averaged within each trajectory. These are not additional independent runs.")
    h("What the result does not establish")
    p("Some coarse lengths approach or fall below one pixel. Four grid/window origins and a second covariance length retained the negative shift, but an exploratory chord analysis found smaller shifts. No universal sensitivity is claimed. Two proposed exponent-warning screens accepted zero of 18 comparisons: they are not validated selectors. A direct-pair audit corrected a roundoff issue in factor-eight secondary results; the factor-four result was unchanged.", "small")
    h("A separate materials-image audit")
    fem, opposite = context["fem"]
    p(f"The audit compares calibrated binary masks at native, 2x and 4x spacing and reports length, phase fraction and resolution warnings. Across all 81 FeM iron-ore fields [5], median length changes were {float(fem[1]['length_change_percent_median']):+.3f}% and {float(fem[2]['length_change_percent_median']):+.3f}%. A post-hoc opposite tie rule changed the 2x median to {float(opposite[1]['length_change_percent_median']):+.3f}%. All fields were resolved and unflagged, unlike the short-window exponent screens. These are fields from one specimen, not 81 specimens; producer masks are references, not physical truth. This is a static sensitivity test, not ageing validation, microscope calibration or laboratory adoption. Phase fraction is not generally chemical composition.", "small")
    h("Closest work and the possible contribution")
    p("Zabler et al. [1] already tested coarsening fits against segmentation threshold; Ledesma-Alonso et al. [2] studied resolution-dependent descriptors. Majumder and Das [3,4] used noise filtering and initial-length/finite-size analysis; their three length measures agreed up to constant factors. Our short raw fits are not equivalent. The possible contribution is the paired dynamic benchmark after fraction matching, not discovery of image bias or a new growth law. Novelty remains unestablished.", "small")
    h("Three questions for a reviewer")
    p("1. Does this specific benchmark add anything useful beyond the closest prior work?<br/>2. Are the length definition, common time mask and paired uncertainty defensible?<br/>3. Could a static mask comparison inform an imaging decision in your work, and what reference and tolerance would make a fair pilot?", "small")
    p('[1] Zabler et al., Acta Materialia 55 (2007), 5045-5055. <link href="https://doi.org/10.1016/j.actamat.2007.05.028" color="'+TEAL+'">doi:10.1016/j.actamat.2007.05.028</link><br/>[2] Ledesma-Alonso et al., Physical Review E 97 (2018), 023304. <link href="https://arxiv.org/abs/1712.03183" color="'+TEAL+'">arXiv:1712.03183</link><br/>[3] Majumder and Das, Physical Review E 81 (2010), 050102(R). <link href="https://arxiv.org/abs/1001.3985" color="'+TEAL+'">arXiv:1001.3985</link>', "small")
    p('[4] Majumder and Das (2013), <link href="https://arxiv.org/abs/1305.2556" color="'+TEAL+'">arXiv:1305.2556</link>. [5] Gomes et al., FeM dataset, <link href="https://doi.org/10.5281/zenodo.5014700" color="'+TEAL+'">doi:10.5281/zenodo.5014700</link>.', "small")
    p("Code, design, analysis and this draft used substantial AI assistance. Student approval and an accessible evidence copy must be checked before sharing. No independent review or outside use has occurred. This requests criticism, not endorsement.", "small")

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#cbd6d8"))
        canvas.line(53,42,A4[0]-53,42)
        canvas.setFillColor(colors.HexColor(GREY))
        canvas.setFont("Helvetica",8)
        canvas.drawString(53,29,"AI-assisted working draft | Not externally reviewed | Student approval pending")
        canvas.drawRightString(A4[0]-53,29,str(doc.page))

    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=53, rightMargin=53,
            topMargin=38, bottomMargin=54,
            title="Does preserving species fraction preserve measured coarsening?",
            author="AI-assisted draft for Django Thompson", subject="Two-page technical criticism brief")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    pages = len(PdfReader(output).pages)
    if pages != 2:
        raise ValueError(f"Expected two pages, got {pages}; inspect and revise layout")
    provenance = {
        "status":"AI-assisted criticism draft; student approval and external review pending",
        "builder_sha256": sha(Path(__file__)), "pdf_sha256":sha(output), "pages":pages,
        "fresh_analysis_manifest_sha256":sha(root/ANALYSIS/"manifest.json"),
        "freeze_sha256":sha(root/FREEZE), "primary":primary,
        "context": context,
        "illustration":illustration,
        "figure_2_data":"Fresh factor-four origin-zero half-height observations; ratio of ensemble means",
        "boundary":"Artifact generation verifies hashes and extraction, not all numerical calculations or novelty"
    }
    output.with_suffix(".provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps({"pdf":str(output),"pages":pages,"sha256":sha(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    build(args.root.resolve(),args.output.resolve())
