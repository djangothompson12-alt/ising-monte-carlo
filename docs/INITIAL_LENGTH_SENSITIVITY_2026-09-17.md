# Exploratory initial-length sensitivity on the completed study

17 September 2026. This is a secondary analysis specified after the original
64-run results and after reading [Majumder & Das 2010](https://arxiv.org/pdf/1001.3985)
and [2011](https://arxiv.org/pdf/1101.4524). It is **not** a preregistered
confirmation or a reproduction of their finite-size scaling. Code:
`research/initial_length_sensitivity.py`; complete output and hashes:
`research/runs/overnight/initial_length_sensitivity_v1/`.

## Question and fixed calculation

Could an early measured length materially alter the finite-window slope of
the existing connected-correlation half-height observable? For each of the
same eight independent trajectories in a group, subtract its measured length
at saved sweep **18** or **22**, the two checkpoints adjacent to 20. Shift the
time origin by the same amount. Fit the log of the ensemble mean of these
positive differences over the nominal windows 1,000–200,000 and
20,000–200,000 sweeps. Fit the raw length on **exactly the same retained
checkpoints** for a paired comparison. No offset, endpoint or exponent is
optimized to obtain one-third. A missing or non-positive adjusted value in
any replica removes that checkpoint from both fits. Bootstrap differences
resample whole trajectories, not timepoints.

## Selected numerical results

These are fixed sweep-18 examples from the full CSV. All listed large-system
rows use eight trajectories and 28 checkpoints for the first window; the
actual retained times are 1,069–200,000 sweeps.

| c | L | Nominal window | Raw slope | Slope after measured early-length subtraction |
|---:|---:|---:|---:|---:|
| .50 | 64 | 1,000–200,000 | .263 | .369 |
| .50 | 96 | 1,000–200,000 | .258 | .365 |
| .50 | 128 | 1,000–200,000 | .258 | .363 |
| .15 | 64 | 1,000–200,000 | .263 | .370 |
| .15 | 96 | 1,000–200,000 | .257 | .360 |
| .15 | 128 | 1,000–200,000 | .260 | .366 |
| .50 | 128 | 20,000–200,000 | .284 | .348 |
| .15 | 128 | 20,000–200,000 | .293 | .358 |

For the two L=128 compositions, sweep 22 instead of 18 yields .368 and .369
in the 1,000–200,000 window. The c=.50, L=32 late-start 20,000–200,000
comparison has only three jointly resolved checkpoints through sweep 34,974,
so it has **no valid fitted slope** under the four-point/fivefold-span rule.
The full table includes every size, both initial checkpoints, both windows,
actual retained times, and paired bootstrap intervals.

## Interpretation and reviewer question

The raw value near .26 is not invariant to a plausible fixed measured-offset
convention. But a value near .36 after subtraction is **not** proof of a new
growth law, nor a demonstration of exact one-third behaviour. The length at
sweep 18 or 22 is an observed early-time half-height correlation length; it
has not been shown to equal the additive *bare length* in the literature's
scaling ansatz. The shifted estimate still changes with fit window and could
be an overcorrection. The literature's main filtered-chord observable,
time-origin treatment and multi-size collapse differ from this test.

The useful question for an external coarsening reviewer is: **Is subtracting
an observed early correlation length physically justified for this observable,
and what independent diagnostic could distinguish a true additive offset from
finite-time dynamics or estimator bias?** Keep this as an exploratory
sensitivity panel or appendix unless that methodological question is resolved.
