# Conservation-aware observation audit on the completed extension

*Declared 19 September 2026 after the fixed fourfold image holdout had been
analysed. The negative binary-image shift and an older post-hoc decomposition
were already known. This is therefore a transparent new-seed mechanism audit,
not a preregistration, blind discovery, or proof of novelty.*

## Question

When a conserved Kawasaki microstructure is converted into a lower-resolution
image, how much of the fitted effective-exponent shift is associated with
linear pixel integration, which preserves the field mean, and how much is
added by binary segmentation, which can change the apparent phase fraction?
Does the direction repeat in both the bicontinuous 50:50 morphology and the
off-critical 15:85 droplet morphology?

This is an observation-pipeline audit on simulated images. It is not a
microscope calibration, an alloy prediction, or evidence that one processing
choice is universally correct.

## Frozen inputs and operators

- Use only the completed `main_065_multisize_v1` extension at `L=128`,
  `Jx=Jy=1`, `T/Tc=0.65`, compositions 0.50 and 0.15, with all 16 trajectories
  per composition. No trajectory or checkpoint is selected by its result.
- Native: measure the saved `128x128` field at one lattice-site spacing.
- Integrated: take non-overlapping `4x4` arithmetic means and measure the
  resulting `32x32` partial-volume field at four-site spacing. This linear
  operation must preserve the field mean to floating-point tolerance.
- Segmented: threshold that same integrated image at zero, assigning exact
  ties to +1, then measure at four-site spacing. Record the resulting apparent
  +1 fraction and its difference from the exactly conserved native fraction.
- Use the same finite-image connected-correlation measurement for all three
  fields. Do not wrap image edges and do not impute unresolved crossings.

## Fixed fitting and uncertainty rules

The primary nominal window is 1,000-20,000 sweeps. The secondary sensitivity
window is 1,000-200,000 sweeps. For a composition and window, retain a
checkpoint only if both directional crossings resolve for all three operators
in every trajectory. Fit `log(ensemble mean length)` against `log(sweep)`.

Report `alpha_integrated - alpha_native`,
`alpha_segmented - alpha_integrated`, and
`alpha_segmented - alpha_native`. Use 500 paired whole-trajectory bootstrap
resamples, keeping the same replica indices in both members of each
comparison. Pixels and checkpoints are not independent replicates. Report the
actual retained range, number of points, all unresolved values and percentile
intervals. The intervals are conditional on this model, mask, operator and
window; they do not represent every source of scientific uncertainty.

## Directional prediction and reporting rule

Based on the older post-hoc decomposition, the selected primary prediction is
that segmentation adds a negative shift relative to the integrated field in
both compositions over 1,000-20,000 sweeps. Call it consistent in direction
only if both point estimates are negative, while separately stating whether
each interval crosses zero. If either is non-negative, report that the
directional repeat failed. The secondary window cannot rescue the primary
result.

Whatever the outcome, keep every row, preserve the immutable source data, and
state that the broad fact that resolution or segmentation can affect measured
kinetics already exists in the literature. The project-specific question is
the conservation-aware decomposition, its composition dependence and its
fully paired provenance—not a claim to have discovered measurement bias.
