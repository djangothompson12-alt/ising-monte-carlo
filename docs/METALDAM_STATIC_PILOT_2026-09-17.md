# Real-image stress test: overlap is not length agreement

**Status:** exploratory AI-assisted analysis, 17 September 2026. This is a
source/evidence note for student verification, not student-authored paper text,
independent validation or external deployment.

## Question and source

On real annotated micrographs, does a segmentation with apparently good pixel
overlap necessarily recover the same *domain-length observable*? This is a
measurement question inspired by the simulation's observation-operator study,
not a test of an Ising growth law.

Source: [MetalDAM producer repository](https://github.com/ari-dasci/OD-MetalDAM)
and [labelled release](https://github.com/ari-dasci/OD-MetalDAM/releases/tag/1.0),
ArcelorMittal Global R&D and DaSCI. The release supplies 42 annotated SEM
micrographs of additively manufactured steel. The public README identifies
class 1 as austenite and says most tiny precipitates were omitted from class 3
annotations. We therefore tested class 1, **not precipitate detection**.
The producer page did not clearly grant a reuse licence; no source images or
derived previews were added to the public working files.

The local downloaded archive passed a ZIP CRC check and has SHA-256
`ceb65afa2495edb2000e5b858beeaf6178c4a368d0c02ec56715402482b3197e`.
The labels omit the SEM information band: 65 pixel rows for 40 images and
66 rows for images 15 and 19. Each image is cropped to its paired label's
height, with the exact omitted count retained in the CSV. One label
(`micrograph26.png`) is RGB, while
its three channels carry identical 0/1 class codes; the code checks this
before using the first channel. This inconsistency was found by running the
pilot, not silently ignored.

An independent code/data audit found that the release's raw class counts do
not reproduce the producer README's percentages for matrix and austenite:
the raw labels give 34.6325% and 55.4855%, rather than 31.86% and 58.26%.
The separate producer metadata asset also has two faulty entries: image 8's
recorded total is too small for its own class counts, and image 27's recorded
class counts disagree with the raw label. The pilot uses the actual label
pixels, not these summary percentages or metadata counts. Sampled colour
labels and the producer's class definition still support code 1 as austenite;
the percentage mismatch remains a source-data limitation to disclose.

## Declared analysis and descriptive results

The script reports an Otsu intensity threshold chosen from each image alone,
both threshold polarities, and a separate *optimistic ceiling* found by
testing all 256 thresholds against that same image's expert label. The latter
is not an independently validated or deployable segmentation method. For each
mask it computes labelled phase fraction, Dice pixel overlap and a finite-field,
non-wrapping, connected-correlation half-height length. The length unit is
**pixels**, because this pilot did not verify physical pixel calibration.
No ageing times, fitted exponents or mechanical properties are inferred.

Across the 42 images, the medians for the dark Otsu mask versus the published
austenite mask were:

| Per-image quantity | Median |
|---|---:|
| Pixel overlap (Dice) | 0.825 |
| Published-mask phase fraction | 0.556 |
| Otsu-dark phase fraction | 0.735 |
| Otsu minus published phase fraction | +0.179 |
| Published-mask correlation length | 5.253 px |
| Otsu-dark / published-mask length ratio | 0.426 |

The median in-sample annotation-optimised Dice was 0.834, only slightly above
the dark Otsu median; its median length ratio remained 0.427. Bright Otsu
polarity had median Dice 0.058. Dark polarity is therefore reported as the
more relevant exploratory direction **after inspecting this dataset**, not as
a preselected rule validated for new images. All 42 masks gave a resolved
length in this analysis. The ratio ranged from 0.166 to 0.639; 26 images had
Dice at least 0.8 and *all 26* nevertheless had a length ratio outside
0.8–1.2. The 0.8–1.2 band is only a descriptive display threshold, not a
pre-agreed engineering tolerance.

This supplies a specific, falsifiable pilot finding: **on these labelled
images, a respectable pixel-overlap score did not guarantee agreement in the
domain-length quantity**. It does not establish which mask corresponds to the
true physical phase boundary, whether the austenite class is the right
materials question for a lab, or whether the discrepancy would change a real
engineering decision. All images may be correlated by specimen/source; no
independent-specimen confidence interval or inferential claim is made.
An exploratory check on one image found that a 3×3 median filter more than
doubled the threshold-mask correlation length while barely changing Dice.
This supports the narrow interpretation that the declared length observable
is sensitive to fine mask texture; it is **not** a validated correction and
does not establish a physical grain or particle diameter.

This *principle* is not a new discovery. Prior materials-image studies have
evaluated downstream [precipitate-size and oxide-thickness errors as well as
segmentation](https://www.nature.com/articles/s41524-022-00878-5), and a later
[SEM/EBSD study](https://www.nature.com/articles/s41524-025-01801-4) discusses
segmentation failures that alter grain-diameter measurements. Our value, if a
partner judges there is any, would have to be the transparent audit applied to
a specific measurement decision—not the generic statement that Dice is
insufficient.

## Next scientific checks before asking for use

1. Ask a materials-imaging researcher whether they ever use a spatial length
statistic for this phase, and what decision or uncertainty tolerance matters.
2. Inspect a few image/label/threshold overlays *privately* with that expert;
check whether label convention, imaging artefacts and noise explain the
length gap. Do not publish overlays until reuse rights are confirmed.
3. Repeat on a **different, prospectively chosen** dataset or partner-approved
images with a fixed polarity and predeclared evaluation metric. Include
specimen grouping and physical calibration if actual units matter.
4. If the tool is useful, the safe version may accept an expert-provided mask
and audit scale/ROI sensitivity, rather than pretending thresholding segments
complex multiphase steel reliably.

Reproduction: run `research/metaldam_mask_pilot.py` on the hashed release ZIP.
Its current ignored local output is
`research/runs/public_mask_pilot/v3/per_image.csv` plus `REPORT.md` and a
source/input manifest. No raw image is redistributed by the script.
