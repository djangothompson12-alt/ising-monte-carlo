"""Render a four-page review draft: two-page brief plus methods appendix.

Uses reportlab in the document runtime; scientific figures are built separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak


def build(figures,output):
    if output.exists(): raise FileExistsError('Use a new PDF filename')
    output.parent.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Text',fontName='Helvetica',fontSize=9.5,leading=13.2,spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallText',fontName='Helvetica',fontSize=8,leading=10.5,spaceAfter=6))
    styles.add(ParagraphStyle(name='Section',fontName='Helvetica-Bold',fontSize=12,leading=15,spaceBefore=10,spaceAfter=6,textColor=colors.HexColor('#176c72')))
    styles['Title'].fontSize=22; styles['Title'].leading=25; styles['Title'].alignment=0
    story=[]
    def p(text,style='Text'): story.append(Paragraph(text,styles[style]))
    def h(text): p(text,'Section')
    def picture(name,height): story.append(Image(str(figures/name),width=475,height=height))
    p('RESEARCH REVIEW DRAFT | 19 SEPTEMBER 2026','SmallText')
    p('When image processing changes<br/>the measured growth law','Title')
    p('Django Thompson | Student review required | Substantial AI-assisted development','SmallText')
    h('Question and motivation')
    p('A Kawasaki simulation conserves the number of sites occupied by each species, but an image made from that simulation need not appear to conserve it. This study asks how much of a fitted coarsening-exponent shift appears during <b>mean-preserving pixel averaging</b>, and how much is added by <b>binary segmentation</b>. The motivation is to distinguish changes in observation from changes in the simulated physics.')
    h('Controlled comparison')
    p('The focused analysis uses 16 independent seeded trajectories at each of two compositions, c = 0.50 and 0.15, on a 128 x 128 periodic lattice, with Jx = Jy = 1 and T = 0.65 Tc. Identical saved snapshots are measured natively, after 4 x 4 averaging, and after thresholding at zero (ties assigned to +1). The observation measurement itself does not wrap image edges. All three fits use the same resolved checkpoints.')
    picture('figure1_stage_differences.png',174)
    p('<b>Figure 1.</b> Differences in slopes of log ensemble-mean length against log time. Bars are 95% percentile intervals from 500 paired whole-trajectory resamples, not independent time points. The nominal primary window is 1,000-20,000 sweeps; 17 shared checkpoints lie at 1,091-17,913 sweeps.','SmallText')
    h('Main result and its boundary')
    p('At c = 0.50, averaging shifts the exponent by -0.00145 [-0.00338, 0.00085], while segmentation adds -0.05446 [-0.05635, -0.05219]. At c = 0.15, the respective shifts are -0.03006 [-0.03405, -0.02563] and -0.04383 [-0.04684, -0.04057]. These are finite-window observation effects, not new asymptotic growth laws. The split changes with the fitted window.')
    p('<b>Design status:</b> this analysis followed an already observed processing effect. New-seed trajectories support a repeat in direction; this was not a blind discovery or preregistered confirmation.','SmallText')
    story.append(PageBreak())

    p('REVIEW BRIEF | 2 OF 2','SmallText')
    h('A real-image test with a narrower claim')
    p('A companion tool tests field size and voxel resolution on four publicly supplied 3D Al-Ge phase masks [4]. It keeps partial-volume averaging separate from binary segmentation, retains unresolved measurements, and records calibration and input hashes. The simulation is still 2D: the tool does not convert Monte Carlo sweeps into alloy ageing time.')
    picture('figure3_real_volume_sensitivity.png',190)
    p('<b>Figure 2.</b> Static comparisons within each selected scan region. At native resolution, the two smaller fields in the 15- and 105-minute scans contain no Ge; no length is plotted. The scan labels do not imply registration or a valid cross-time growth fit. Adapted measurements from Fell [4], CC BY 4.0.','SmallText')
    p('The fixed-box audit produced 60 comparisons: 40 resolved three-axis half-height lengths and 20 unresolved. Fourfold averaging changed the 195-minute full-box length from 0.15717 to 0.32173 micrometres; subsequent segmentation gave 0.21005 micrometres. However, all selected boxes are sparse in Ge, and some lengths are near the voxel scale. Numerical resolution does not establish representative sampling or physical accuracy.')
    h('What might be a contribution?')
    p('Threshold-dependent coarsening exponents are already reported by Zabler et al. [1], and mixed-pixel versus binary image coarsening has prior art in Eidel et al. [2]. The candidate contribution is therefore the <b>paired, conservation-aware stage decomposition of a finite-window exponent</b> across two conserved mixtures, with reproducible uncertainty and failure reporting. Its novelty and usefulness still require specialist criticism.')
    h('Three questions for an academic or engineer')
    p('1. Is this stage decomposition already established in conserved-phase-ordering studies, and which work is the closest comparison?<br/>2. Is the connected-correlation half-height length suitable for both morphologies, and is the common all-trajectory resolved-time rule defensible?<br/>3. Is there an imaging decision for which this audit would be useful? If so, what owner-selected data and acceptance criterion would make a fair pilot?')
    p('<b>Not claimed:</b> a new growth law; proof that fraction loss causes the exponent shift; validated alloy kinetics or properties; laboratory adoption; external endorsement. The present request is for criticism, not a recommendation letter.','SmallText')
    story.append(PageBreak())

    p('METHODS APPENDIX | 1 OF 2','SmallText')
    h('Observable, operations and statistical unit')
    p('For each finite image, subtract its own mean. Along each axis, average products of these centred values over valid pixel pairs separated by r and divide by the image variance. No opposite edges are joined. The length is the first crossing of normalized correlation through 0.5, linearly interpolated between sampled lags. Multiply by pixel spacing, then average the two directional lengths only if both resolve.')
    p('Averaging uses disjoint 4 x 4 blocks; its physical spacing is four original lattice sites. Segmentation maps averaged values greater than or equal to zero to +1, and all others to -1. Mean preservation is checked at every snapshot. Identical fields, physical extent and resolved checkpoints are used across the three stages; only the observation operation changes.')
    p('A checkpoint enters a window only if both directions resolve for every operator in every trajectory. Fit ordinary least squares to log(mean length across trajectories) against log(sweeps), using the same time mask. Resample complete trajectories with replacement and apply the same indices to each operator. The interval is conditional on the chosen model, window, operator and resolution rule; it excludes uncertainty in those design choices.')
    picture('figure2_apparent_fraction.png',174)
    p('<b>Figure A1.</b> Segmentation changes the apparent +1 fraction while block averaging preserves it. Shading around the curves shows pointwise 95% trajectory-bootstrap intervals, not a simultaneous confidence band. Grey vertical shading marks the retained primary window. These are simulated species-site fractions, not real-alloy chemical compositions.','SmallText')
    h('Interpretation safeguards')
    p('The sequential identity is: combined exponent shift = averaging shift + additional segmentation shift. It is an order-specific accounting decomposition, not a causal mediation analysis. Segmentation alters geometry as well as apparent composition. The longer 1,000-200,000-sweep sensitivity window reduces the additional segmentation shift to approximately -0.012 at both compositions; neither window replaces the other.')
    p('The familiar t^(1/3) law is a late-stage expectation under diffusion-controlled scaling assumptions. A finite-window fit below 1/3 neither falsifies that expectation nor identifies finite size as its cause. Majumder and Das [3] use a different measurement protocol. The archived 0.6 Tc reference simulations are not described here as a method-matched reproduction.','SmallText')
    story.append(PageBreak())

    p('METHODS APPENDIX | 2 OF 2','SmallText')
    h('Verification completed')
    p('A separately coded direct-pair calculation checked native, averaged and segmented lengths at the first, middle and last saved checkpoint of all 32 included trajectories: 96 snapshots and 576 directional values. The maximum absolute difference was 3.6 x 10^-15 lattice sites. A centred-dot-product regression independently reproduced all 12 fitted stage comparisons and their original bootstrap intervals.')
    p('A 5,000-draw bootstrap sensitivity check retained the same zero-crossing classifications as the original 500-draw intervals. Leaving out one trajectory at a time retained the negative primary segmentation-stage shift at both compositions. These are internal checks performed with AI assistance, not verification by a separate researcher. They do not establish model adequacy or novelty.')
    h('Real-image method and limitations')
    p('Each fixed 256-cube is centred on page 169 and the solid-mask centroid on that page. Concentric 192- and 128-cubes test field size; factors 2 and 4 test voxel averaging and thresholding. Spacing is 0.06 micrometres per native voxel. Undeclared labels invalidate the full box. Three directional lengths must resolve for the mean. Complete binary chords and first-positive-lobe integrals are supplementary quantities, not interchangeable radii.')
    p('Overlapping crops are not independent specimens. The original segmentation is a reference, not verified ground truth. Sparse fields may miss entire features; removing boundary-touching chords favours shorter complete chords. A binary phase volume fraction is generally not alloy chemical composition. No ageing slope, representative-volume threshold or calibrated mechanical property is inferred.')
    h('Reproducibility and student ownership')
    p('The accompanying reviewer guide identifies raw archives, frozen analysis, input/output hashes, numerical checks and the standalone audit. Original trajectories are unchanged. A clean-copy check covers the minimal audit under a separate Python runtime, not fresh installation of the full simulation environment. Before sharing, the student must verify the narrative, explain the definitions and select the questions they genuinely want answered.')
    h('Selected sources and novelty boundary')
    p('[1] Zabler et al. (2007), <i>Coarsening of grain refined semi-solid Al-Ge32 alloy: X-ray microtomography and in situ radiography</i>, Acta Materialia 55, 5045-5055. Figure 8 relates fitted exponent to threshold/solid fraction. <link href="https://doi.org/10.1016/j.actamat.2007.05.028" color="#176c72">doi:10.1016/j.actamat.2007.05.028</link>','SmallText')
    p('[2] Eidel, Fischer and Gote (2021), <i>From image data towards microstructure information</i>, ZAMM 101, e202000245. Image-resolution and discretization errors in microstructure mechanics; mixed-pixel coarsening is not a new general idea. <link href="https://doi.org/10.1002/zamm.202000245" color="#176c72">doi:10.1002/zamm.202000245</link>','SmallText')
    p('[3] Majumder and Das (2010), <i>Domain coarsening in two dimensions: Conserved dynamics and finite-size scaling</i>, Physical Review E 81, 050102(R). <link href="https://arxiv.org/abs/1001.3985" color="#176c72">arXiv:1001.3985</link>','SmallText')
    p('[4] Fell (2023), <i>Microstructural evolution of an Al-Ge alloy revealed by nano-CT</i>, Mendeley Data v1, CC BY 4.0. Supplied segmentation; this project derives cropped/coarsened measurements. <link href="https://data.mendeley.com/datasets/hj9njz3rxp/1" color="#176c72">doi:10.17632/hj9njz3rxp.1</link>','SmallText')
    p('Literature searches were bounded, not systematic or exhaustive. No "first-ever" claim is made. Full scope and AI contributions are recorded in the repository.','SmallText')
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#bed3d3')); canvas.line(60,43,A4[0]-60,43)
        canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#52636a'))
        canvas.drawString(60,30,'Working draft for technical criticism | Not externally reviewed')
        canvas.drawRightString(A4[0]-60,30,str(doc.page))
    doc=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=60,rightMargin=60,topMargin=43,bottomMargin=57,
        title='Conservation-aware measurement of Kawasaki coarsening: review draft',
        author='AI-assisted working draft for Django Thompson',subject='Two-page technical brief and methods appendix')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    output.with_suffix('.provenance.json').write_text(json.dumps(dict(builder_sha256=sha(Path(__file__)),
        figure_manifest_sha256=sha(figures/'manifest.json'),pdf_sha256=sha(output),
        status='AI-assisted working draft; student verification and external review pending'),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('figures',type=Path)
    p.add_argument('--output',type=Path,required=True); a=p.parse_args(); build(a.figures,a.output)
