"""Build a student-facing, one-page method comparison sheet for the 2010 paper."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "benchmark_method_reading_sheet.pdf"


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    navy = colors.HexColor("#183047")
    teal = colors.HexColor("#0F6B78")
    pale = colors.HexColor("#EAF3F5")
    ink = colors.HexColor("#22313D")
    muted = colors.HexColor("#5C6C78")
    small = ParagraphStyle("small", fontName="Helvetica", fontSize=8.5,
                           leading=11.3, textColor=ink, spaceAfter=0)
    head = ParagraphStyle("head", parent=small, fontName="Helvetica-Bold",
                          fontSize=9, leading=12, textColor=navy)
    title = ParagraphStyle("title", parent=small, fontName="Helvetica-Bold",
                           fontSize=19, leading=22, textColor=navy)
    subtitle = ParagraphStyle("subtitle", parent=small, fontSize=10,
                              leading=14, textColor=muted)
    section = ParagraphStyle("section", parent=small, fontName="Helvetica-Bold",
                             fontSize=10.5, leading=14, textColor=teal)
    note = ParagraphStyle("note", parent=small, fontSize=8.6, leading=12)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18*mm,
                            rightMargin=18*mm, topMargin=17*mm, bottomMargin=15*mm,
                            title="Benchmark method reading sheet",
                            author="Ising Monte Carlo research project")
    story = [Paragraph("Paper-matching benchmark", title),
             Spacer(1, 2*mm),
             Paragraph("A separate test - not your main 0.65 Tc study", subtitle),
             Spacer(1, 3*mm)]
    distinction = Table([
        [Paragraph("YOUR MAIN RESEARCH STUDY", head), Paragraph("SEPARATE LITERATURE BENCHMARK", head)],
        [Paragraph("T = 0.65 Tc; includes asymmetric c = 0.15 and symmetric c = 0.50. The archived campaign spans L = 32, 64, 96, 128. Its larger follow-up is planned but not yet run.", small),
         Paragraph("T = 0.60 Tc; symmetric c = 0.50 only; L = 128, with 40 long runs planned. These settings intentionally match one part of Majumder and Das (2010).", small)],
    ], colWidths=[87*mm, 87*mm], hAlign="LEFT")
    distinction.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pale),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 1, teal),
    ]))
    story += [distinction, Spacer(1, 2*mm),
             Paragraph("Same Kawasaki codebase, different declared settings. Both specific campaigns use Jx = Jy = 1, although the engine also supports anisotropy. <b>Do not pool their results or treat the benchmark as a replacement for your main study.</b>", note),
             Spacer(1, 3*mm),
             Paragraph("Purpose: check whether the <b>methods</b> are comparable before looking at any exponent. Read the paper's paragraphs beginning 'In Fig. 1' and 'Fig. 2 shows' (pages 1-2). You do not need the whole paper tonight.", note),
             Spacer(1, 3*mm)]

    rows = [
        ("Setup", "Random 50:50 mixture on a periodic 2D square lattice; L=128 and T=0.6 Tc.",
         "Exactly 50:50 random starting lattice; periodic 2D L=128; isotropic Jx=Jy=1; 0.6 Tc. No pre-quench equilibration sweeps."),
        ("Dynamics and clock", "Nearest-neighbour Kawasaki exchanges. One MCS is L squared exchange trials.",
         "One sweep is L squared random nearest-neighbour exchange proposals, with Metropolis acceptance. Check whether the paper specifies the same proposal and acceptance details."),
        ("Independent runs", "For L=128, 40 independent starting configurations. The paper identifies 4.5 million MCS as its L=128 finite-size onset snapshot.",
         "40 fresh seeds planned, each to 4.5 million post-quench sweeps. This does not reproduce the paper's other lattice sizes or full scaling analysis."),
        ("Noise removal", "Before measuring morphology, replace a spin by the majority sign among that site and its four nearest neighbours.",
         "One simultaneous, periodic five-site majority pass on each saved image. It never feeds back into the simulation. The paper does not fully specify pass scheduling."),
        ("Domain length", "First moment of the distribution of distances between successive interfaces along horizontal and vertical lines.",
         "Mean of all finite same-spin chords along periodic rows and columns after filtering. Uniform lines are omitted. Confirm whether the paper treats these and weighting the same way."),
    ]
    table_data = [[Paragraph("Check", head), Paragraph("The paper says", head), Paragraph("Our benchmark does", head)]]
    for label, paper, ours in rows:
        table_data.append([Paragraph(label, head), Paragraph(paper, small), Paragraph(ours, small)])
    table = Table(table_data, colWidths=[30*mm, 71*mm, 73*mm], hAlign="LEFT", repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), pale),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), .8, teal),
        ("LINEBELOW", (0, 1), (-1, -2), .35, colors.HexColor("#D9E2E7")),
        ("BOX", (0, 0), (-1, -1), .45, colors.HexColor("#D9E2E7")),
    ]))
    story += [table, Spacer(1, 4*mm),
              Paragraph("What to write in your notes", section), Spacer(1, 1*mm),
              Paragraph("For each uncertain row: <b>(1)</b> paper page and your own one-sentence summary; <b>(2)</b> mark MATCHES / UNCLEAR / DIFFERS; <b>(3)</b> say whether it could change the time axis, measured length, or fitted exponent. Example: 'The paper gives an x/y interface-spacing definition, but does not say how a uniform periodic row is counted. UNCLEAR; this may affect the late-time mean length.'", note),
              Spacer(1, 3*mm),
              Paragraph("Your three most important notes", section), Spacer(1, 2*mm)]
    for index in range(1, 4):
        story.append(Paragraph(f"{index}. __________________________________________________________________________________", note))
        story.append(Spacer(1, 2*mm))
    story += [Spacer(1, 2*mm),
              Paragraph("Afterwards: send me your notes. We will correct the method declaration and only then analyse the completed 40-run benchmark. Do not mark it 'student verified' or claim replication yet.", note),
              Spacer(1, 3*mm),
              Paragraph("Source: S. Majumder and S. K. Das, 'Domain Coarsening in 2-d Ising Model: Finite-Size Scaling for Conserved Dynamics' (2010), arXiv:1001.3985, pp. 1-2. Our implementation: research/plans/majumder_das_2010_l128.json and research/reference_measurements.py.",
                        ParagraphStyle("foot", parent=small, fontSize=7.3, leading=9.5, textColor=muted))]
    doc.build(story)
    return OUTPUT


if __name__ == "__main__":
    print(build())
