# Full-extension observable robustness audit

**Frozen before running this analysis on the completed extension:** 19
September 2026. This is a post-result robustness audit. The primary
connected-correlation results, the smaller four-observable pilot and the
general fact of estimator disagreement were already known. It is not a blind
discovery test or a replacement for the extension's declared primary analysis.

## Question

Do the two main qualitative conclusions of the completed `0.65 Tc` extension
survive when the same 9,600 saved microstructures are measured using physically
different length proxies?

The conclusions tested are:

1. fitted effective exponents depend on the selected finite time window; and
2. the smallest 15:85 system develops a late matched-time departure from the
   `L=128` system.

This audit will not ask which estimator is the uniquely correct particle or
domain radius. It will not tune a high-frequency cutoff, initial length,
fitting window or size threshold to obtain one-third.

## Frozen input

- Campaign: `research/runs/main_065_multisize_v1`
- `T=0.65 Tc`, compositions `c=0.50` and `c=0.15`
- sizes `L=32,64,96,128`
- 16 independent seeded trajectories per condition
- 1,000,000 sweeps and 75 archived checkpoints per trajectory
- exact expected inventory: 128 NPZ files and 9,600 saved states

The analysis must reject an incomplete or unexpected inventory, mismatched
time arrays, failed exact-composition checks or changed input hashes. It reads
saved states but never advances or alters a trajectory.

## Four declared observables

All are already implemented and tested in `research/metrology.py`.

1. `threshold_05`: mean x/y half-height crossing of the saved connected
   correlation. This must reproduce the archived primary length.
2. `positive_lobe`: mean x/y area under the positive correlation lobe up to
   its interpolated first zero.
3. `spectral_moment`: inverse first moment of the full nonzero structure
   factor. It has no adjustable radial cutoff and can be biased by thermal
   high-frequency power.
4. `inverse_interface_proxy`: inverse fraction of unlike nearest-neighbour
   bonds. It is a morphology proxy, not an interfacial energy or calibrated
   radius, and it can include thermal interfaces.

No majority-spin filter is used in this audit because that observation step
can change apparent composition, particularly in an off-critical field. A
paper-inspired filtered-chord analysis is a separate question.

## Frozen fits

Use the extension's five nominal windows:

- 1,000–20,000 sweeps
- 1,000–200,000 sweeps
- 20,000–200,000 sweeps
- 20,000–1,000,000 sweeps
- 200,000–1,000,000 sweeps

Within each composition–size group, an estimator comparison uses a **common
checkpoint mask**: every one of the four values must be finite and positive
for every one of the 16 trajectories. Do not use `nanmean`, fill an unresolved
value or silently let estimator sample sizes differ. A fit needs at least four
checkpoints and a factor-five span in actual retained time, matching the main
analysis rule. Report nominal and actual time bounds and unresolved counts.

For every estimator and window, fit the logarithm of the ensemble-mean length
against log time. Use 2,000 whole-trajectory bootstrap draws. Use the same
replica indices for an estimator and the threshold reference so the interval
for their slope difference is paired.

## Frozen matched-size checks

At the archived checkpoints at 207,231 and 1,000,000 sweeps,
compare each smaller size's ensemble mean with `L=128` separately for each
observable. Resample whole trajectories independently between sizes using
2,000 draws. A ratio is unresolved unless every contributing trajectory has a
finite positive value. These are matched-time ratios, not a fitted finite-size
onset or proof that `L=128` is infinite.

**Time-grid amendment before any output was written:** the first implementation
attempt stopped because the logarithmic archive does not contain an exact
200,000-sweep checkpoint. Its nearest checkpoint is 207,231 sweeps. This
amendment records the existing time grid and was made without inspecting any
observable result.

## Interpretation rule

A qualitative conclusion is *observable-robust* only if it has the same
direction for all resolved observables. Mixed signs or unresolved rows must be
reported as dependence, not averaged into agreement. Numerical exponent
agreement is not required: the observables have different thermal and
geometrical sensitivities and are not four estimates of a known true radius.

The final report must show all fit rows and ratios, including failures, plus
source, protocol and raw-file hashes. Any interpretation written after seeing
the results must be clearly separated from these frozen rules.
