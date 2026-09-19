# Frozen short-window measurement validation

This is AI-assisted prospective follow-up after the fraction-matching result
was known. It tests measurement diagnostics, not a new physical law. The
development data are all 32 previously examined L=128 extension trajectories.
Those data are NOT a holdout. The new batch is 8 independent seeds per
composition, L=128, c=.50/.15, Jx=Jy=1, T=.65 Tc, initial T=3 Tc and 200 initial
sweeps; 20,000 post-quench sweeps, 80 logarithmic requested checkpoints.
The seed root is 2026091937. Each new derived seed is checked against saved
campaigns before launch. The timing-only seed 902100 is excluded.

No new run or its morphology is inspected before this protocol and the
analysis sources are hash-frozen. Complete all 16 or record failure; do not
extend, selectively replace, change windows or change thresholds to improve
the result. This small batch is a first independent test, not a powered claim
of universal applicability. Old and new checkpoint grids need not coincide;
do not pool their ensembles.

## Declared analysis

Use all available checkpoints in [1000,20000]. Factors 2,4,8. Four block-grid
origins: (0,0), (factor/2,0), (0,factor/2), (factor/2,factor/2).
Translate the periodic simulation array before measuring BOTH native and
coarse images. Finite-image correlations still never join opposite edges.
This tests grid origin together with the finite observation-window origin;
it does not isolate these two effects. Never wrap an experimental image.

Compare native, means retained as grey values, fixed threshold >=.5, and
nearest-count fraction matching. Five fixed tie seeds 110,211,312,413,514;
average tie lengths within each replica, not as independent experiments.
Keep all tie outcomes. Never evolve processed images.

Primary observable: mean directional connected-correlation half-height.
Secondary: mean directional positive-lobe integral, only if both directions
reach zero. Within each composition/factor/origin/observable retain only
times resolved and positive for every replica and every operator/tie seed.
Record attrition. Require >=4 checkpoints and >=5-fold time span. Do not
claim paired cross-observable agreement if time masks differ.

Primary comparison: fraction-matched minus native at factor 4, origin 0.
Other factors, origins, observables and stages are sensitivity checks. Fit
log ensemble-mean length versus log time, with 1000 paired whole-trajectory
bootstrap samples (seed 912). Report unresolved estimates and all intervals.

The slope of log(mean processed length / mean native length) must equal the
fitted exponent difference on the same time grid to rounding. Verify with
known synthetic powers. This is an algebraic accounting identity, not a
new theory, independent predictor or mechanistic proof. Do not substitute
the mean of individual length ratios for the ratio of ensemble means.

## Fixed baseline screens (not trained on new results)

1. `directional_02_adaptation`: implement Eq.34's floor/ceiling algebra from
   Ledesma-Alonso et al. (2018), using the earliest interpolated +.02 crossing
   of each native directional normalized covariance and their minimum.
   Require the proposed factor to pass at EVERY retained checkpoint and
   replica. Missing crossings => unknown, never automatic pass.
   This uses native data and is only a reduced, conservative-over-replicas
   comparison. It omits line-path and pore-size descriptors and differs
   from their ensemble-descriptor construction. It is NOT the published
   full criterion, and cannot falsify that full criterion.
2. `observed_three_pixel_screen`: require every treatment half-height
   directional length, replica, tie and retained checkpoint to be >=3 coarse
   pixels. This is an explicitly chosen heuristic, NOT a published theorem
   or a learned/new algorithm. It needs no native measurement.

An absolute exponent difference tolerance of .02 is a declared benchmark
convention, not a universally acceptable engineering error. Label a fit
`within` only if its paired 95% interval is entirely inside [-.02,.02];
`outside` if entirely beyond one end; otherwise `uncertain`. Report pass
coverage, false-safe cases (pass plus outside), and unresolved cases. Cases
share trajectories and are NOT independent samples; no binomial performance
confidence interval or precision claim. Zero passing cases is zero usable
coverage, not perfect success. Neither screen becomes a recommended rule
merely by being implemented. If neither offers useful coverage, stop the
new-diagnostic claim and ask for specialist guidance before more runs.

## External boundary

Apply the secondary observable and explicit resolution warnings to the same
fixed Al-Ge boxes. Do not fit an experimental exponent, infer a kinetic pass
from static masks, or call a 3D extension of the directional screen the
original 2D paper method. Public-data feasibility is not adoption. Full
published multi-descriptor reproduction and an owner-approved usefulness
criterion remain separate unfinished tasks, not silently fulfilled here.

## Publication gate

These tests can strengthen or weaken a small methods contribution. They do
not certify novelty. A useful diagnostic must eventually outperform suitable
prior guidance on independent cases; agreement with a trivial identity or
failure of an incomplete adaptation is not such evidence. Preserve negative
findings and do not imply new coarsening physics.
