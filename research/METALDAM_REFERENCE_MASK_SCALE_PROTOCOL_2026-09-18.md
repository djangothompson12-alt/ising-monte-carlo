# Frozen exploratory question: resolution sensitivity on expert masks

*Declared before reading the output of this analysis, 18 September 2026.
AI-assisted, exploratory, not independently specified by a materials lab.*

## Question

On the 42 published MetalDAM **austenite annotation masks** (class code 1),
how much does the finite-image connected-correlation half-height length
change when the **same expert mask** is block-averaged to coarser resolution
and re-binarised? This isolates one observation operator from the earlier
failure of intensity-threshold segmentation. It is not a coarsening, alloy
phase-separation or materials-property experiment.

Source: [MetalDAM producer release 1.0](https://github.com/ari-dasci/OD-MetalDAM/releases/tag/1.0),
locally stored ZIP with expected SHA-256
`ceb65afa2495edb2000e5b858beeaf6178c4a368d0c02ec56715402482b3197e`.
The licence for image/label redistribution was not clear in the producer page;
the script publishes **no source pixels, masks, crops or overlays**. Numerical
outputs remain source-attributed and should be reviewed before public release.

## Frozen choices

1. Use all 42 class-1 producer masks, no exclusions based on outcome. Read
   label pixels from the checked ZIP; image bands are irrelevant because no
   intensity image is used. Handle image 26's three equal-code channels only
   after confirming they agree.
2. For each factor `b∈{2,4,8}`, crop only bottom/right edges to dimensions
   divisible by `b`, anchored at the original top-left. Recompute the native
   reference length on **this same cropped field** so an edge crop is not
   silently counted as a resolution effect. Record trimmed row/column counts.
3. Average each non-overlapping `b×b` binary mask block. The primary binary
   decision assigns a 50:50 block tie to class 1 (`mean>=0.5`), matching the
   existing synthetic observation operator. Record the tie-block fraction;
   also calculate a predeclared sensitivity with ties assigned to class 0
   (`mean>0.5`). Do not select the better convention after seeing results.
4. Apply the **same** `research.imaging.image_length` non-periodic connected
   half-height estimator to the native cropped mask and coarse binary masks.
   Convert coarse lengths back to original-pixel units by multiplying by `b`.
   Unresolved values remain missing, never zero. Report the length ratio,
   phase-fraction difference, and pixel Dice after nearest-neighbour
   expansion of the coarse mask on the matched cropped field.
5. Summarise across images using descriptive medians, ranges and counts of
   positive/negative length changes for each factor and tie rule. Treat
   images as possibly correlated by source/specimen: **no specimen-level
   confidence interval, hypothesis test or population claim**.
6. Preserve per-image rows, source and input hashes, code hash, and a
   no-overwrite output directory. Verify elementary uniform/block patterns
   and units in automated tests before interpreting the dataset.

## Stop/interpretation rules

- If substantial lengths are unresolved or the class label semantics fail,
  report that instead of silently selecting images.
- A resolution-dependent number on **static austenite masks** is not a
  physical ageing exponent, precipitate radius, grain size or strength
  prediction. It is a metrology sensitivity result in pixels.
- This dataset does not provide an independent user or endorsement. A lab
  contact would still need to say whether this is a measurement they care
  about and what error tolerance matters.
