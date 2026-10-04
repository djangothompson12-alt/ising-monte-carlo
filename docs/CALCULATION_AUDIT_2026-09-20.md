# Calculation and numerical-boundary audit

20 September 2026. Internal AI-assisted verification, not external review.

## Why this check was added

Passing the software tests is not enough to establish that every saved result
is correct. A separate implementation now reconstructs the fresh-run image
measurements directly from pixel pairs, without using the production FFT,
length, fitting or bootstrap functions. This tests the measurement pipeline;
it does not establish a new physical growth law.

## A numerical issue found

One correlation had an exact zero at separation four, followed by another
positive value. The FFT returned approximately `2.78e-17` instead of zero.
The positive-lobe integral therefore continued past the correct stopping
point. In that example the reported mean length was 5.126011 rather than
5.068436 lattice spacings, a difference of about 1.14% relative to the
direct calculation. The example is the 50:50 fresh run `rep000`, at 20,000
sweeps, factor eight, origin zero, tie seed 211.

This is a numerical-boundary issue, not a failure of Kawasaki conservation.
It is also not evidence that every small discrepancy in the physics is a
rounding error. The effect on fitted results must be checked explicitly.

The new opt-in `research/stable_image_metrology.py` recomputes correlations
near the zero, half-height and 0.02 decision levels using direct pixel pairs.
The tolerance selects values to check: it does not round a genuine small
correlation to zero. A regression test contains the actual affected mask.
The frozen analysis files, observations and original figures remain unchanged.
The safeguard is for future finite-image analyses, not a silent replacement
of the simulation engines or of the 3D volume measurement implementation.

## Checks already completed

- Recalculated the saved correlations, lengths and interface fractions for
  all 9,600 snapshots from the 128-trajectory extension. Maximum correlation
  difference was `8.89e-16`; maximum finite length difference was `2.85e-14`.
  One strict half-height boundary changed a resolved/unresolved decision
  under fresh FFT rounding. It is counted, not hidden as a successful match.
- Re-ran the four fixed public Al–Ge regions with physical units now visible
  in the report table. The 96-row observations file is byte-identical to its
  earlier version. No new specimen, region or kinetic fit was introduced.
- The existing physics tests cover energy accounting, conservation, a small
  canonical transition matrix, the regular-solution map, exact coexistence
  limits and LSW normalization. These checks do not establish the physical
  applicability of those theoretical approximations to an actual alloy.

## Fresh-run audit

The completed audit covers all 36,864 retained observation rows (147,456
scalar checks) and all 144 fit rows. The original fitted numbers and bootstrap
intervals reproduce to a maximum absolute difference of `2.02e-15` when using
the original saved measurements. All nine frozen source files are unchanged.

Direct-pair recalculation found 37 discrepant positive-lobe lengths, all at
factor eight in fraction-matched 50:50 images. Six involved a disagreement
over whether the first zero was reached. Among the finite pairs, the maximum
length difference was 0.984605 lattice spacings; this is not merely rounding
in the printed length. Half-height and near-zero lengths agreed to floating
point precision across the complete retained dataset.

Using direct-pair lengths changed four secondary fitted differences. The
largest change was −0.001841: the factor-eight, origin-zero, 50:50 matched
positive-lobe difference changed from −0.153129 to −0.154969. No retained
time mask or tolerance classification changed in the 144 comparisons.
All factor-four results, including the primary comparisons and their
four-origin sensitivity checks, were unchanged to numerical precision.
The safeguard was separately checked against direct calculations on all 37
affected masks; all four metrics agreed within `3.56e-15`.

The audit also enumerates the complete empirical paired-bootstrap distribution
for the four primary comparisons: 6,435 distinct count vectors represent all
16,777,216 ordered resamples of eight trajectories.

| Composition | Length definition | Exponent difference | Enumerated 95% percentile interval |
|---|---|---:|---|
| 50:50 | Half-height | −0.050475 | [−0.052985, −0.047860] |
| 15:85 | Half-height | −0.076511 | [−0.080010, −0.072361] |
| 50:50 | Positive-lobe | −0.034029 | [−0.037107, −0.030429] |
| 15:85 | Positive-lobe | −0.049860 | [−0.054196, −0.045066] |

These use an inverse discrete cumulative distribution, whereas the original
1,000-resample calculation interpolates sample percentiles. The original
reported intervals remain in the frozen results. All four conclusions remain
outside the chosen ±0.02 band, and leaving out any one trajectory does not
reverse their sign. Enumeration removes random-resampling error, not the
limitations of eight runs, uncertainty in measurement choices or possible
poor confidence-interval coverage. It does not create new independent data.

The [machine-readable audit](../research/results/fresh_arithmetic_audit_2026-09-20_v1/verification.json)
contains every discrepancy and recalculated fit. Its status is deliberately
`discrepancies_found`, not an unconditional pass. The complete software suite
passes 178 tests. This is a bounded calculation audit, not certification that
every historic calculation, theoretical assumption or literature claim is correct.

## Additional archive, baseline and software checks

The next pass checked four complete, existing campaigns. These counts overlap
the work above; they are not newly generated data or extra independent evidence.

| Campaign | Trajectories | Saved snapshots |
|---|---:|---:|
| Original 0.65 Tc size/composition study | 64 | 3,840 |
| Million-sweep 0.65 Tc extension | 128 | 9,600 |
| Separate 0.6 Tc reference-condition campaign | 40 | 3,600 |
| Fresh short-window measurement study | 16 | 1,120 |
| Total | 248 | 18,160 |

The strengthened archive checker now verifies the quench temperatures from the
couplings and declared ratios, the full checkpoint grid and the integer species
count implied by each nominal composition. All four campaigns passed these
checks, together with source identity, seed, conservation and later heat-interval
checks. Replaying only the original pre-quench preparation then independently
counting bonds verified the first heat interval in all 248 trajectories, with
zero energy discrepancy. This replay shares the original dynamics kernel;
it is not an independent implementation or a literature replication.

Separate table recalculation also checked 48 original-study fits and 80 extension
fits, 1,080 ensemble rows and 450 matched-size rows. Differences were below
`1.78e-15`. The checks cover the chosen rules and their arithmetic, not whether
a window or length cutoff isolates an asymptotic regime.

The older aggregate CSVs reproduce Model A's exponent as `0.4998995432`
(19 retained points, 3–489 sweeps), and the anisotropic Model B directional
exponents as `0.1829456233` and `0.1381558280`. The older draft value `0.4841`
is not reproduced by this saved baseline and its current fit rule. The archived
bath-flow endpoints decrease by factors of approximately 30,402 and 23,014;
this is an endpoint comparison, not a proof of monotonicity or a calculation
of total entropy production. The stored droplet table contains 513 objects
of at least four sites. Numerical quadrature gives both the zeroth and first
moments of the LSW reference distribution as one to numerical precision.
That normalization does not validate its physical assumptions for 2D clusters.

### A separate reproducibility fix

Model A's temperature-sweep routine seeded the initial lattice but did not seed
Numba's random updates. Two calls with the same seed gave different final
lattices and mean energies. Future temperature runs now seed both generators;
tests check exact replay even with another run in between. This does not change
the spin-flip rule, Model A's raw correlation, its self-seeded quench routine,
or any Kawasaki kernel. The historical temperature CSV is preserved and is
not claimed to have been generated by the corrected routine.

The old temperature standard errors use a simple sample-count formula, not an
autocorrelation correction. Legacy quench summaries drop unresolved lengths
and divide their error estimates by the nominal replica count. Without the
original per-replica histories, those older error bars cannot be independently
reconstructed or corrected. Do not use them as a substitute for the newer
fixed-ensemble, whole-trajectory uncertainty analysis.

The historical LaTeX draft now gives the Boltzmann constant in the critical-
temperature equation, the actual Model A fit interval and a correct explanation
of reciprocal-space anisotropy. Overstrong statements about raw correlations
and statistical agreement were qualified. Model A's future plot title now
includes the division by site count in the per-spin bath-flow equation.
Historical figures and the stale PDF were not silently regenerated.

All 186 tests pass after these changes. The detailed records are in
[the follow-up audit results](../research/results/comprehensive_recheck_2026-09-20_v1/).
This does not certify every historic benchmark, citation or physical interpretation.

## What this means for the approach

The useful next step is to finish this bounded measurement study and invite
criticism of its question, observable and comparison with existing methods.
More model features or simulations without a specific unresolved test would
not by themselves strengthen the conclusion. A full published-method baseline
and a genuinely independent user's evaluation remain more valuable than an
additional visualiser feature. Originality and usefulness remain open questions.

## Reproduce

From the repository root, with the documented Python dependencies:

```bash
python -m unittest discover -s tests
python -m research.audit_fresh_measurements research/runs/growth_reliability_holdout_v1 research/results/growth_reliability_fresh_2026-09-19_v1 --output output/my_fresh_arithmetic_audit
python -m research.audit_archived_observables research/runs/main_065_multisize_v1 --output output/my_extension_observable_audit.json
python -m research.audit_campaign_contracts --output output/my_campaign_contracts.json
python -m research.audit_legacy_numbers --output output/my_legacy_numbers.json
```

Use a new output location. The fresh audit records hash checks on the original
sources, raw inputs and outputs, as well as every discrepant measurement.
The full direct-pair check takes longer than the ordinary unit tests.
