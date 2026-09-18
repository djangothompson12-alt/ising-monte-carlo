# Fixed image-operator holdout on the running main extension

*Declared 18 September 2026 while the 0.65 Tc, 128-trajectory extension was
incomplete (26/128 completed when this analysis was designed). AI-assisted
protocol and code. The observation effect and its sign had already been seen
in the earlier eight-run ensemble and four-run fresh-seed repeat. This is a
new-seed confirmation attempt for that selected effect, **not** a fully blind
first hypothesis test or an independent experiment.*
Some extension raw files already existed when this was written. Their
new-seed image measurements and fitted slopes were not opened or used to
choose this operator or its windows. That timing is part of the provenance,
not a claim of formal preregistration before data collection.

## Question and units

On unchanged archived Model B microstructures, does a **specific** fourfold
block-averaging-and-binary-threshold operation again shift the fitted
finite-image growth exponent relative to the full native image? The
independent statistical unit is one seeded simulation trajectory. Two
observations of a trajectory are paired. Checkpoints and pixels are not
independent replicates. This is an algorithmic observation test, not a
microscope calibration or an alloy validation.

## Frozen scope and operators

- Analyse only `L=128`, `Jx=Jy=1`, `T_final/Tc=0.65`, `c=0.50` and `c=0.15`,
  with all **16** planned replicas at each composition from
  `main_065_multisize_v1`. No selection by appearance, slope or result.
- Run only after the full four-size campaign is marked complete at **128/128**,
  its exact raw-file inventory is present, and archive verification passes.
  Reject any new-seed overlap with the completed earlier main and repeat
  ensembles. No result from partial extension data is released.
- Native observation: the full, non-periodic `128×128` saved ±1 image,
  measured by `research.imaging.image_length` at one original-site unit per
  pixel. It subtracts the observed image mean and uses pair-count-corrected
  finite-window axis correlations; it does **not** wrap image edges. Pair-count
  normalisation does not make the estimated covariance statistically unbiased.
- Altered observation: `research.imaging.observe(snapshot, factor=4,
  threshold=0)`, i.e. non-overlapping `4×4` block arithmetic mean, then +1
  for values **at or above** zero and −1 otherwise. No blur or crop. Measure
  the resulting `32×32` image with pixel spacing **4 original sites**. The
  exact-tie-to-+1 rule can change apparent phase fraction and must be shown.
- Both lengths are means of their horizontal and vertical half-height
  correlation crossings. If a direction is unresolved, the length remains
  unresolved; do not impute or remove an inconvenient replica.

## Fitting and uncertainty fixed now

Primary nominal window: **1,000–20,000 sweeps**, chosen to match the previous
observation study. Secondary sensitivity window: **1,000–200,000 sweeps**.
Within each composition and window, use the same checkpoints for native and
altered image fits, retaining a checkpoint only when **both directions for
both observations resolve in all 16 replicas**. Report actual first/last
retained sweep, point count, and missingness, including if the fit becomes
unidentifiable. Do not shift either window after seeing the slopes.

For each condition fit the slope of `log(ensemble mean length)` against
`log(sweep)` by ordinary least squares. The paired quantity is
`Δα = α_bin4 − α_native`. Use 500 whole-trajectory bootstrap resamples with
the same selected replica indices for native and bin4 in each resample,
and report the 2.5th and 97.5th percentiles. Record the apparent +1
fractions before and after processing at every checkpoint. Bootstrap
intervals address run-to-run variability **conditional** on the operator,
fitting window, common mask and model—not all scientific uncertainty.

## Reporting rule, whatever happens

Report both compositions and both windows, every unresolved fraction and
the full per-run table. Call a repeat of the earlier negative shift
*consistent in direction* only if the new primary point estimate is negative
in each composition; state explicitly if its bootstrap interval crosses
zero. If either sign is non-negative, report a failure of directional
repetition. Do not recast a secondary-window result as the primary test or
add a new threshold selected from these data. Compare original, first
fresh-seed and new holdout results side by side, without pooling their
different time grids as though one prospective trial.

Success does not prove an asymptotic exponent, physical mechanism,
instrument-independent correction or practical usefulness to a laboratory.
Failure is a substantive result about limited transfer of the observation
effect. The observation analysis is a separate script and cannot change the
engine, running campaign or frozen main-extension physics protocol.

Implementation note, 18 September while the extension was still running:
the holdout figure code was made robust to a percentile interval that does
not contain its original point estimate. It now draws the interval and point
separately. This changed no input, operator, fit mask, bootstrap or reporting
rule, and no holdout result had been calculated.
The readable REPORT.md generator was also updated before any holdout result:
it now displays the phase fractions already present in the CSV, whether each
paired interval crosses zero, and the exact two-composition primary-window
sign-rule verdict stated above. The secondary window cannot rescue the
primary result. This was a presentation/guard change, not a new analysis
choice or a peek at unfinished image measurements.
