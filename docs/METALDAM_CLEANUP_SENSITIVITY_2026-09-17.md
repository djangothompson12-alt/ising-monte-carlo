# Follow-up: does simple mask cleanup resolve the image-length gap?

**Exploratory AI-assisted evidence note, 17 September 2026.** This is not
student-authored paper prose, external validation, or a recommended segmentation
recipe. The analysis was prompted by a one-image post-hoc observation that a
3×3 median filter strongly changed the measured correlation length. The 5×5
width was then included as an additional sensitivity check. Treat the whole
follow-up as exploratory, not as a prospective test on independent specimens.

## Question and fixed comparison

The [first public-image pilot](METALDAM_STATIC_PILOT_2026-09-17.md) found that
dark Otsu masks of 42 annotated steel SEM images had reasonably high Dice
overlap with the published austenite masks, yet much shorter measured
correlation lengths. Does removing isolated binary-mask texture close the
length gap, and what happens to other measurement targets?

The input is the same source-hashed MetalDAM labelled release as the first
pilot. For each full labelled field, the pipeline uses the same image-only
Otsu threshold and the already-selected dark polarity. It then measures the
raw mask and versions passed through a 3×3 or 5×5 binary median filter with
reflecting image edges. The published class-1 mask is an unchanged comparison
reference. The reported length is the finite-field, non-wrapping connected-
correlation half-height length in **pixels**, averaged across the two image
axes. It is not a grain diameter or physical particle radius. Dice, apparent
phase fraction and length are all measured on exactly the same 42 images;
each image supplies a paired comparison, not three independent observations.

## Descriptive result

| Mask | Median Dice | Median absolute phase-fraction error | Median measured/reference length |
|---|---:|---:|---:|
| Raw dark Otsu | 0.825 | 0.179 | 0.426 |
| Otsu + 3×3 median | 0.835 | 0.194 | 0.609 |
| Otsu + 5×5 median | 0.833 | 0.207 | 0.701 |

All 42 correlation lengths resolved under each treatment. Relative to each
image's raw mask, the absolute *log* length error decreased for all 42 after
3×3 cleanup and for all 42 after 5×5 cleanup. The median **paired** change
in that error was −0.343 and −0.507, respectively. Median paired Dice changed
by only +0.0086 and +0.0036. However, median paired absolute phase-fraction
error **increased** by +0.020 and +0.036. These paired medians need not equal
the difference between the table's marginal medians.

The local run also generates a scatter plot of Dice versus length ratio at
`research/runs/public_mask_pilot/cleanup_v3/dice_vs_length_ratio.png`. It is
kept in ignored local output for now, so this note does not imply a public
figure or resolved image-data reuse permission.

The defensible interpretation is narrow: the original short Otsu-mask
lengths are substantially sensitive to fine binary-mask texture. A modest
change that barely affects Dice can move the length statistic substantially.
But making one statistic closer to the annotation moves another statistic
(phase fraction) further away. A cleaner-looking mask is not therefore a
validated physical phase boundary or a generally better segmentation.

## Checks, reproduction and limits

- The 42 unfiltered rows match the earlier pilot's Otsu threshold, Dice,
  phase fraction, reference length and Otsu length to floating-point tolerance
  for every image. The new output has 42 images and 126 mask measurements.
- Three focused unit tests check Dice, binary median behaviour, and paired
  summary accounting. The run records archive and source hashes in
  `research/runs/public_mask_pilot/cleanup_v3/manifest.json`; raw image files
  are not copied into the output. Earlier local `cleanup_v1` and `cleanup_v2`
  runs are superseded because the summary accounting was improved; the
  immutable `cleanup_v3` result is the one to cite.
- Reproduce locally with the public labelled archive and
  `MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.metaldam_cleanup_sensitivity
  research/runs/public_mask_pilot/MetalDAM_labeled.zip --output
  research/runs/public_mask_pilot/<new-output-name>`. The script verifies the
  exact inspected archive SHA-256 before analysis. Do not redistribute source
  images or label previews without resolving the producer's reuse terms.
- Published labels are comparison annotations, **not infallible physical
  ground truth**. Their edge conventions and omission of tiny features may
  themselves explain some disagreement. The 42 fields may share specimens
  or preparation conditions; no independent-specimen confidence interval or
  population inference is attempted. Polarity and cleanup were selected
  after examining this dataset, so the results are not held-out validation.
- These are static micrographs of a different material system. There is no
  ageing time series, no verified pixel-to-length calibration, no measured
  growth exponent, no strength prediction and no evidence of lab adoption.

**Useful expert-review question:** For austenite images like these, is this
correlation length a meaningful quantity in your workflow? If so, what
reference measurement and tolerance would make a mask-sensitivity audit useful
for an actual materials decision? If not, which downstream quantity should be
audited instead? The answer should determine whether this stays a cautionary
appendix or merits a partner-defined follow-up.
