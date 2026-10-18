# Audit improvements and resolution study feasibility

The current question stays fixed: does matching the native species-site
fraction after resolution reduction preserve the native finite-window
coarsening exponent? The target is not to force a result of one third.
The most useful next step is to establish where this comparison is adequately
resolved, while keeping the first academic criticism brief simple.

This is an AI-assisted development record for Django to check, not a
student-authored paper, new holdout, independent review or publication claim.

## Improvement completed in the mask audit

The static 2D mask tool now reports changes in horizontal and vertical lengths
separately, as well as their mean. An owner can choose `decision_scope` as
`mean_length` or `both_directions` before analysing an image. The existing
mean-only decision remains the default for compatibility. Both the output
table and provenance record identify the chosen scope.

This prevents an ambiguous interpretation: if equal native directional
lengths change by +20% and -20%, their mean does not change. A 10% tolerance
on the mean therefore passes, but a 10% tolerance on each direction fails.
Neither criterion establishes physical accuracy. The owner must choose the
one relevant to their measurement, not whichever passes afterwards.

The numerical length estimator, simulation engines, frozen study sources and
historical results were not changed. Regression tests cover cancellation,
missing directions, unit changes, axis exchange, invalid scope and report
provenance. The synthetic demonstration is a software example, not evidence
of experimental validation.

The full local suite passed 231 tests in 52.397 seconds. A separate spot check
recomputed covariance by explicit valid pixel pairs for 18 directional native
lengths: first, middle and last retained checkpoints of replica zero in each
of the three conditions below. These matched the saved inventory with zero
observed absolute difference; both paths used the same crossing interpolator,
so this is not an independent check of that interpolator or the full inventory.
HTML content checks passed, but browser policy blocked the local-file preview;
the updated report layout has not been visually verified.

## What the saved long runs can support

The new `research/inspect_saved_resolution.py` reads the full saved fields,
uses finite nonperiodic directional half-height lengths with refined
decision-boundary arithmetic, and records source and archive hashes. It fits
no exponents and processes no coarse images. Existing trajectories remain
unchanged.

On 7 October it inspected 72 size-128 archives containing 6,000 saved
snapshots. Native lengths were recalculated at checkpoints from 1,000 sweeps
onwards. There are 32 trajectories at 0.65 Tc (16 per composition) and a
separate 40-trajectory symmetric reference campaign at 0.6 Tc. They must not
be pooled, and have already been inspected in earlier analyses.

For a conservative feasibility check, require every replica and both native
directional lengths to span at least three proposed coarse pixels. Separately
require each directional length to be below 0.15 of the lattice width. These
are planning heuristics, not validated accuracy or finite-size criteria. In
particular, native length divided by block factor is only a resolution proxy;
it is NOT the actual measured length after processing. The directional size
screen is stricter than a screen on the ensemble mean.

| Cohort | At factor two, checkpoints passing both planning screens | Time span |
|---|---|---|
| 0.65 Tc, 50:50, 16 trajectories | 4 checkpoints, 350,190 to 591,769 sweeps | 1.69-fold |
| 0.65 Tc, 15:85, 16 trajectories | 4 checkpoints, 591,769 to 1,000,000 sweeps | 1.69-fold |
| 0.6 Tc, 50:50, 40 trajectories | 2 checkpoints, 553,061 to 649,840 sweeps | 1.17-fold |

No factor-four or factor-eight checkpoint passes the all-replica native
three-pixel proxy in these cohorts. At factor two the reference campaign
passes the resolution proxy alone over a 5.89-fold span, but not both checks
over that span. None meets the existing study's four-checkpoint and fivefold
span convention under both checks. This does not show that all individual
images are unusable, that finite-size effects have been detected, or that
another justified observable cannot help. It does show why longer duration
alone is not yet an adequate response to the resolution objection.

The local inventories are under
`output/resolution_feasibility_2026-10-07/main_065/inventory.json` and
`output/resolution_feasibility_2026-10-07/reference_060/inventory.json`.
To reproduce, choose new output folders:

```sh
.venv311/bin/python -m research.inspect_saved_resolution research/runs/main_065_multisize_v1 --output output/new-main-resolution-check
.venv311/bin/python -m research.inspect_saved_resolution research/runs/majumder_das_2010_l128 --output output/new-reference-resolution-check
```

## Study decision before more simulations

Do not relax the screens until the desired answer appears or relabel these
known data as an unseen test. Keep the current severe-resolution result as a
bounded counterexample and ask a specialist whether a useful next comparison
requires larger lattices, a different justified resolution diagnostic, or a
different primary observable. Any new design should be written down before
new measurements, with a compute pilot and explicit budget before a campaign.
An alternate estimator is a robustness test, not a way to choose the exponent
closest to one third.

The existing chord appendix and reliability maps remain supporting evidence;
they are not new contributions to be implemented again. The full published
multi-descriptor resolution criterion remains unimplemented. A partial
directional adaptation must not be described as outperforming that method.

## What would make the audit useful outside this project

The first pilot should answer one researcher's real question on one approved
dataset, with its phase definition, calibration, ROI, specimen grouping and
tolerance fixed beforehand. Ask whether the result changes a decision about
image reduction or measurement reporting. Record criticisms and revisions,
including a finding that the audit adds no useful information.

Accuracy has distinct levels: a calculation can reproduce a direct numerical
reference while its segmentation or physical calibration is wrong. Static
mask comparisons do not validate an ageing exponent, and repeated fields
from one specimen do not become independent specimens. A native image is a
reference measurement, not ground truth. A suitable time series or independent
measurement is required before extending those claims.

Authenticity means Django can explain the chosen measurement, its failure
cases, and a change he made in response to evidence. The programming and
analysis assistance must remain disclosed. A professional's actual criticism
and a documented response are evidence; a planned pilot or helpful discussion
is not endorsement or adoption.

## Closest literature and the criticism request

[Zabler et al. (2007)](https://www.alexanderrack.eu/papers/zabler2007.pdf)
already tested coarsening exponents against segmentation threshold.
[Ledesma-Alonso et al. (2018)](https://arxiv.org/abs/1712.03183)
already studied resolution-dependent microstructure descriptors.
[Werz et al. (2014)](https://pure.hw.ac.uk/ws/files/10435481/WeBaWo14_preprint.pdf)
downsampled alloy tomography, adjusted segmented phase fraction and analysed
coarsening. Combining these ingredients is therefore not itself a novelty
claim. A candidate contribution is the controlled, reproducible comparison
of finite-window exponent preservation, with useful success and failure
boundaries. That distinction still needs specialist criticism.

The focused question for a reviewer is: does a controlled fraction-matching
benchmark add a useful test beyond these studies, and what resolution and
observable requirements would make its next validation persuasive? This
decision should precede substantial new computation. It need not delay the
first two-page request for criticism.
