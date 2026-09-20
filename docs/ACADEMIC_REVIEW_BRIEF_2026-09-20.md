# Does preserving composition preserve the measured growth law?

**Student project: Django Thompson. Working brief, 20 September 2026.**
Prepared with substantial AI assistance; student review and approval are
required before sending. This requests criticism, not endorsement.

## Question and motivation

The project began with 2D Ising simulations: non-conserved Metropolis flips
and conserved Kawasaki exchanges. The current study asks a narrower
measurement question: if lower-resolution images are forced to preserve the
native species fraction, do they recover the native finite-window growth
exponent? This matters because image processing can change a measured domain
length without changing the underlying simulated material.

## Main result

Sixteen fresh L=128 trajectories, eight each at 50:50 and 15:85, were run at
0.65 Tc with Jx=Jy=1. A protocol and source hashes were frozen before these
runs. Measurements used the same 24 checkpoints between 1,119 and 20,000
sweeps. Four-pixel block integration was followed by rank-based binary
segmentation with five fixed tie priorities. Matching is exact at 50:50;
off-critical matching retains the unavoidable integer-pixel rounding error.

| Species ratio | Native effective exponent | Fraction-matched exponent | Paired difference (95% interval) |
|---|---:|---:|---|
| 50:50 | 0.23141 | 0.18094 | −0.05047 [−0.05293, −0.04782] |
| 15:85 | 0.24214 | 0.16563 | −0.07651 [−0.08006, −0.07255] |

Lengths come from the half-height of finite-image directional covariance;
intervals use 1,000 paired whole-trajectory bootstrap draws. The negative
shift also appeared with the positive-lobe integral and four grid origins.
These sensitivity checks share trajectories, rather than supplying extra
independent runs. The finite-image statistic is deliberately distinct from
the simulation engine's periodic correlation estimator.

The processed/native mean-length ratio decreases through the fit window:
early lengths are inflated more than late ones. This flattens the log-log
slope. A constant multiplicative length error would not change that slope.
The identity explains the fitted difference, not its unique geometric cause.

## Checks and limits

The work includes separately coded numerical checks and raw-trajectory audits.
New known-geometry controls reproduce an analytic checkerboard correlation and
show that forcing the right fraction cannot reconstruct boundaries erased by
averaging. These are synthetic sanity checks, not novel physics.

A [complete fresh-measurement arithmetic audit](CALCULATION_AUDIT_2026-09-20.md)
found a zero-crossing roundoff issue in 37 factor-eight secondary lengths.
Direct recalculation changed four secondary fits but not the factor-four
results above or any tolerance classification. Original outputs are preserved.

Two predeclared conservative resolution screens accepted zero of 18 comparisons,
including five within the chosen exponent-error tolerance. They therefore
have no demonstrated acceptance coverage here. Thresholds were not relaxed
after seeing this result. The directional published-method adaptation is
not the full three-descriptor method; see the [method comparison](RESOLUTION_METHOD_CROSSWALK_2026-09-20.md).

Public 3D Al-Ge masks provide a separate, static image-audit demonstration.
They do not establish an experimental growth exponent or validate 2D alloy
kinetics. Binary phase fraction is not generally conserved chemical composition.
The tool has not yet been evaluated by an independent laboratory user.

## Three questions for a reviewer

1. Is the paired finite-window exponent benchmark a useful addition to
   established resolution/segmentation studies, or already adequately covered?
2. Are the observable, paired uncertainty calculation and unresolved-case
   rules defensible? Which published baseline should be implemented next?
3. Could a static mask audit inform a concrete imaging decision in your work?
   If so, what measurement and acceptance criterion would make a small pilot useful?

## Evidence and contribution boundary

Start with the [illustrated fresh-run results](../research/results/growth_reliability_summary_2026-09-19_v1/review_brief.html)
and [controlled-image demonstration](../research/results/geometry_controls_2026-09-20_v3/report.html).
Methods, all-case results and limitations are in the
[validation note](GROWTH_RELIABILITY_RESULTS_2026-09-19.md).
The [contribution record](../AI_USE_AND_CONTRIBUTIONS.md) documents AI involvement
in study design, implementation, analysis and drafting. The student remains
responsible for understanding, reproducing and approving the work.

No new growth law, full literature replication, established novelty,
predictive alloy model, outside use or academic endorsement is claimed.
