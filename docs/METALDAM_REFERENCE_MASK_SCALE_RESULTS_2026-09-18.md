# What lower image resolution did to measured length on real steel masks

*Exploratory AI-assisted analysis, 18 September 2026. It is not a Kawasaki
growth-law test, a student-authored paper section, independent lab validation
or a ready-to-use industrial tool. The student must inspect the source and
results before citing them externally.*

## Question, source and control

The [predeclared protocol](../research/METALDAM_REFERENCE_MASK_SCALE_PROTOCOL_2026-09-18.md)
asks what happens to **one measured length** when the *same labelled steel
microstructure* is viewed at coarser resolution. We used all 42 producer
austenite (class 1) masks in the [MetalDAM release](https://github.com/ari-dasci/OD-MetalDAM/releases/tag/1.0).
The ZIP's checked SHA-256 is recorded in the ignored local
[`summary.json`](../research/runs/public_mask_pilot/reference_scale_v1/summary.json).
Source pixels and labels have not been copied into this document or a review
pack; the producer page's redistribution licence needs clarification before
publishing them.

For each image and reduction factor, the native reference mask was cropped
to the **same field** as the coarse mask. Blocks of 2×2, 4×4 or 8×8 labelled
pixels were averaged, then re-binarised at 50%. We ran both fixed tie rules:
ties to class 1 (the predeclared primary rule) and ties to class 0 (sensitivity).
The non-periodic connected-correlation half-height length was calculated on
both masks. Coarse pixel lengths were multiplied by the block factor, so the
ratio compares the **same original-pixel units**. No physical micrometre
calibration was established. All 252 image×factor×tie-rule comparisons had
resolved lengths; no result was imputed as zero.

## Descriptive result: tie-to-class-1 rule

| Resolution | Median coarse/native length ratio | Range across 42 masks | Images with increased measured length | Median pixel Dice after expansion | Median coarse minus native class fraction |
|---|---:|---:|---:|---:|---:|
| 2× coarser | 0.995 | 0.977–1.072 | 11/42 | 0.964 | +0.024 |
| 4× coarser | 1.050 | 1.015–1.181 | 42/42 | 0.927 | +0.012 |
| 8× coarser | 1.195 | 1.078–1.471 | 42/42 | 0.859 | +0.0004 |

At 8×, the median phase-fraction change is almost zero, yet the median
*measured length* is about 20% larger. This is a direct, controlled example
of why phase fraction or pixel overlap alone may not describe what happened
to a length statistic. It does **not** mean austenite domains physically grew.

The tie convention matters at 2×: ties to class 0 instead give a median
length ratio of `1.029` (42/42 above one) and median fraction difference
`−0.024`, compared with `0.995` and `+0.024` for ties to class 1. The median
fraction of tied 2×2 blocks was `0.0485`. At 4× and 8× both tie conventions
gave length ratios above one for all 42 images (medians `1.070` and `1.200`
for ties to class 0). These are predeclared alternatives, **not** a search
for whichever produces a more dramatic result.

The numbers are descriptive across images, not an independent-specimen
confidence interval. The source does not establish that these 42 images are
independent materials experiments, and the annotation is a published label,
not guaranteed physical ground truth. The measured quantity is a correlation
half-height length in pixels, **not** a precipitate radius, grain diameter,
growth exponent, ageing time or mechanical-property prediction.

## Relation to the project and an honest external-use question

The earlier [threshold-only pilot](METALDAM_STATIC_PILOT_2026-09-17.md)
showed that a crude segmentation could overlap the label yet give a poor
length. This follow-up removes that particular segmentation error by starting
from the **expert mask itself**. It tests a distinct resolution/binning
choice and finds that the downstream length remains sensitive. A user with
approved masks could run the same short audit on their own images, but no
outside researcher has asked for, adopted or evaluated it.

The narrow question to put to an imaging researcher is: *When you report a
feature length from a labelled micrograph, do you compare it across
resolutions or processing settings, and what change would actually affect
your interpretation?* If their work uses a different length or phase, this
tool may be irrelevant. Its value would come from answering a **specified
measurement decision**, not from simply being run on a public dataset.

Reproduction: `research/metaldam_reference_mask_scale.py` checks the source
ZIP and refuses to overwrite an output directory. The ignored local output
holds all 252 per-image rows, a summary and source/protocol hashes.
`tests/test_metaldam_reference_mask_scale.py` checks matched cropping,
original-pixel units, 50% ties, missing values and Dice arithmetic. No
source mask/image pixels are redistributed.
