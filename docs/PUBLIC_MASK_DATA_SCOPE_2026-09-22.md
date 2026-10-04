# Public phase-mask data screened for the resolution audit

**Date:** 22 September 2026

**Purpose:** find an additional public experimental materials mask that can
stress-test the bounded native/2x/4x audit without changing its method after
seeing the result.

## Minimum selection conditions

I required a supplied mask of a named material feature, an explicit physical
pixel scale, enough source information to define a fixed 2D field, and terms
that permit a local academic analysis. I excluded data whose only label was a
grain boundary, because a thin boundary network is not the binary phase mask
for which this audit was designed. I also excluded synthetic images as the main
outside test and did not infer a scale from magnification alone.

## Dataset used

The [MicroAl-Dataset public GitHub sample](https://github.com/neulmc/MicroAl-Dataset)
contains one heat-treated optical-metallography example with separate Si-particle
and Al-grain-boundary labels. Its documentation states 0.1 micrometres per
pixel. The Si-particle mask was therefore a direct fit for the declared audit.
The fixed protocol and numerical result are recorded in
`MASK_RESOLUTION_AUDIT_VALIDATION_2026-09-22.md` and the ignored local output
folder `output/microal_mask_audit_2026-09-22_v1/`.

The source's terms permit academic research but prohibit unauthorised
redistribution and commercial use. No raw MicroAl pixels are copied into this
repository or its report. Only the source description, input hash and derived
measurements are retained locally.

## Other candidates screened

| Candidate | What it offers | Decision for this audit |
|---|---|---|
| FeM | 81 experimental registered iron-ore microscopy fields, binary producer references and explicit 1.05 um/pixel calibration | **Used in full**; all 81 fields plus a post-hoc tie-rule sensitivity |
| MicroAl | Experimental aluminium-alloy optical micrograph, supplied Si-particle mask, explicit 0.1 um/pixel scale | **Used** for one fixed public-sample test |
| Al-Ge tomography | Producer-segmented two-phase 3D time series with 0.06 um voxels | Already replayed; useful for workflow consistency but not new independent evidence |
| MetalDAM | 42 labelled SEM images of additively manufactured steel with matrix, austenite, martensite/austenite, precipitate and defect classes | Already investigated; physical pixel calibration and producer reuse terms are not sufficiently clear for the new calibrated replay |
| UHCS semantic/particle masks | 24 manually annotated steel micrographs and 24 particle micrographs; published figures include scale bars | Promising future dataset, but an exact per-file pixel calibration was not established from the public description during this screen. Manually reading a scale bar would add another unvalidated operator step |
| Materials Data Segmentation Benchmark | Multiple material image sets with ground-truth masks | Not used because the public overview did not establish a calibrated pixel spacing and feature definition for a directly suitable file |
| Texture Boundary in Metallography | Expert boundary annotations for 320 metallographic crops | Excluded because it is a boundary-detection benchmark rather than a binary phase-area mask |
| Synthetic grain-boundary restoration library | Pixel-perfect artificial ground truth | Useful for software benchmarks, but not an independent experimental-material test |

## What this search changes

The audit has now been exercised on three distinct public materials sources: a
segmented Al-Ge tomography plane, an aluminium-alloy Si-particle mask and all
81 fields in the FeM iron-ore dataset. FeM is the strongest software stress
test: all fields remain resolved at 4x, and an explicit sensitivity analysis
shows that the tie convention can change the sign of a small 2x length bias.
This is stronger evidence that the program behaves transparently on real
masks, but it remains software and workflow testing rather than external
laboratory validation.

The next highest-value evidence is not another convenient download. It is a
small owner-led pilot in which a materials researcher chooses the phase, field,
descriptor and practically meaningful tolerance before the result is run.
