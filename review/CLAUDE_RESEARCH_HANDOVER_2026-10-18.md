# Ising/Kawasaki project: handover for a critical second reading

18 October 2026. AI-assisted consolidation requested by Django Thompson.
This is not a new experiment, exhaustive literature review, student-approved
manuscript or independent academic assessment. Frozen results are unchanged.

## Start here

**Current question: after reducing image resolution, is matching the native
species-site fraction sufficient to preserve the fitted finite-window
coarsening exponent in 2D Kawasaki simulations?**

Plain English: if I make the images coarser but keep the same proportion of
each labelled species, do I still measure the same rate of domain growth?

The reference is the **native finite-window fit**, not recovery of one third.
Native is a declared measurement of the original saved image, not uniquely
correct physical domain size. The original below-one-third puzzle motivates
the project; this experiment does not explain every cause of that shortfall.

Read next:

1. [Current short brief source](../docs/ACADEMIC_REVIEW_BRIEF_2026-09-20.md),
   updated 15 October despite its historical filename.
2. [Fresh-cohort results](../docs/GROWTH_RELIABILITY_RESULTS_2026-09-19.md),
   [arithmetic corrections](../docs/CALCULATION_AUDIT_2026-09-20.md) and
   [chord/majority appendix](../docs/CHORD_OBSERVATION_RESULTS_2026-09-26.md).
3. [Latest audit and methods scope](../docs/AUDIT_PROGRESS_AND_METHODS_SCOPE_2026-10-15.md)
   and [audit value/baseline specification](../docs/AUDIT_VALUE_AND_BASELINE_2026-10-15.md).
4. [Data inventory and reproduction](../research/DATA_README.md) and
   [AI/contribution record](../AI_USE_AND_CONTRIBUTIONS.md).

`review/review_brief.pdf` is the **1 October historical copy**, not the
15 October v2 local PDF. The linked Markdown brief is the current public text.
The old LaTeX paper is not the current report. Personal learning/admissions
notes are in a separate private handover, deliberately absent from GitHub.

## 1. Models, physics and application boundary

Both engines use a 2D nearest-neighbour Ising lattice with periodic simulation
boundaries and spins +1/-1. With horizontal and vertical couplings,

    H = -Jx sum(horizontal neighbouring spin products)
        -Jy sum(vertical neighbouring spin products).

An aligned ferromagnetic bond contributes -J, not +J. Metropolis acceptance
is min(1, exp(-Delta H/T)) in kB=1 units. Individual accepted moves need not
lower energy. Hamiltonian energy is not Helmholtz free energy.

- **Model A:** single-spin flips; magnetisation is not conserved. This models
  non-conserved ordering, not diffusion of fixed numbers of alloy atoms.
  Curvature-driven late scaling in the relevant regime is length ~ t^(1/2).
- **Model B:** nearest-neighbour exchanges preserve both species counts and
  magnetisation. Equal-spin exchanges leave the state unchanged. One sweep
  is N squared attempted updates on a width-N lattice, not accepted exchanges.
- Both have interactive visualisers. Model B permits unequal Jx/Jy, mixture
  changes and quench controls. Controlled campaigns use **Jx=Jy=1**, keeping
  anisotropy out of the primary comparison. Composition varies between
  conditions, not within a conserved trajectory.
- Tc is approximately 2.269 for isotropic J=kB=1, in model units, not kelvin.

For conserved diffusive coarsening the standard scaling argument is curvature
giving a chemical-potential difference ~1/ell, transport over a characteristic
distance ell, then d ell/dt ~1/ell^2 and ell ~t^(1/3). Ell is a typical domain
length, not the full box width N. This does not require every run or finite
fit window to yield 1/3. Conservation does not prohibit domain coalescence.

There is no calibration from sites to micrometres or sweeps to hours, no
material-specific diffusion data, and no prediction of alloy strength,
hardness or ageing time. The model omits important 3D, crystallographic,
elastic, defect and diffusion physics. Qualitative relevance is not a
quantitative model of a named alloy.

## 2. What changed, and why

1. Begin with flips, then introduce exchanges to study conserved composition.
   This changes the dynamics/physical interpretation, not just execution speed.
2. Add composition and coupling controls, but keep couplings isotropic in
   controlled studies rather than changing every variable together.
3. Remove the off-critical raw-correlation background using a normalised
   connected correlation. Model A and B measurements are deliberately not
   identical; their outputs cannot be compared as interchangeable lengths.
4. Increase durations, sizes and independent seeds to examine fit-window
   dependence, sampling variation and possible finite-size limitations. More
   runs reduce sampling uncertainty, not common bias, and do not force 1/3.
5. Add a separate 0.6 Tc literature-reference campaign. Matching temperature
   alone does not reproduce Majumder and Das's preparation/measurement/scaling.
6. Compare observables and image processing on the **same snapshots**, isolating
   observation sensitivity from changes in the underlying simulation.
7. Add fraction matching to ask whether removing observed fraction changes is
   sufficient. Restoring a count cannot necessarily restore erased boundaries.
8. Add a frozen-method fresh-seed check, synthetic controls, direct numerical
   references and a separate static materials-mask audit.
9. Narrow the contribution argument as closer prior work is identified. Do not
   pretend the full design or publication angle existed from the outset.

The [progress history](../docs/PROGRESS_AND_LIMITS.md) retains earlier stages.
Later dated records supersede old status wording, not immutable numerical data.

## 3. Dataset identities: do not pool or double-count

| Dataset | Conditions/count | Duration and role |
|---|---|---|
| Original `overnight` | 64 trajectories; widths 32/64/96/128; c=.50/.15; eight per condition; .65 Tc | 200,000 sweeps; exploratory time/size/measurement work |
| Earlier imaging repeat | Eight new width-128 trajectories, four per composition | 20,000 sweeps; not the primary fresh cohort |
| `main_065_multisize_v1` | 128 trajectories; same four sizes/two compositions; 16 per condition; .65 Tc | One million sweeps each; longer finite-window physics study |
| `majumder_das_2010_l128` | 40 width-128 symmetric trajectories; .6 Tc | 4.5 million sweeps each; raw campaign complete, literature-method interpretation unfinished |
| Measurement development set | 32 already-known width-128 extension trajectories, 16 per composition | Reanalysis, not 32 extra trajectories to add to the 128 |
| `growth_reliability_holdout_v1` | **16 fresh trajectories total**, eight per composition, width 128, .65 Tc | 20,000 sweeps; primary frozen-method fraction-matching check |
| Chord/majority appendix | Reuses those same 16 | Exploratory remeasurement, not another holdout/campaign |

The earlier 24-run pilot is retained, not independent confirmation. Exact
seeds, integer compositions, preparation and versions are in each manifest.
The extension has 200 preparation sweeps; the reference has zero. Do not
claim one preparation applies to every cohort. No runs were launched for
this handover; old promises do not establish current background processes.

Time checkpoints within a run are correlated, not independent replications.
Whole-trajectory bootstrapping samples complete runs with replacement and
uses the same selected indices across paired measurements. It does not edit
an exponent by hand or resample time points as independent runs.

## 4. Observations versus measurements

The engine's periodic correlation differs from finite-image, non-wrapping
directional covariance. Phase labels, centring, boundaries, crossing rules
and units must match before calling two calculations equivalent.

For binary spins the familiar connected correlation is
(C(r)-m squared)/(1-m squared). Grey block-mean images need the declared
covariance/variance normalisation, not indiscriminate reuse of that binary
formula. Primary image lengths are interpolated horizontal/vertical half-height
crossings; missing crossings stay unresolved. Positive-lobe integrals and
complete foreground chords are different operational lengths, not radii.

- **4x4 block averaging:** keep the real mean of each 16-pixel block. Over a
  complete equal-block field this preserves the global mean. It does not
  itself round to a majority spin.
- **Thresholding:** convert those means to binary labels using a declared
  threshold and exact-tie rule; observed fraction and geometry can change.
- **Fraction matching:** rank means and choose the required foreground count.
  Five fixed coordinate tie priorities are averaged within each trajectory/time;
  these are not five extra replications.

At c=.15, native fraction is approximately .1500244 and nearest-count coarse
fraction .1503906. Matching is nearest-count, not exact. At .50 it is exact.
Observation processing does not alter saved states or simulated conservation.
In real materials, phase area fraction is not generally chemical composition.

## 5. Headline result, accounting and limits

The fresh primary comparison uses **24 shared checkpoints, 1,119-20,000
sweeps**. The nominal window starts at 1,000; the first retained saved point
is 1,119. It is an early, severely reduced stress test, not asymptotic scaling.

| Species fraction | Native half-height exponent | Fourfold fraction-matched exponent | Paired difference, 95% interval |
|---|---:|---:|---|
| .50 | .23141 | .18094 | -.05047 [-.05293, -.04782] |
| .15 | .24214 | .16563 | -.07651 [-.08006, -.07255] |

Intervals use 1,000 paired whole-trajectory bootstrap draws; they do not cover
every systematic/model/processing uncertainty. The positive-lobe shifts are
-.03403 and -.04986; four block-grid origins retain the fourfold direction.
These are correlated robustness checks, not extra independent cohorts.
Some coarse lengths approach or fall below one pixel.

**Supported conclusion: matching fraction is not necessarily sufficient to
preserve the native finite-window fit.** It can help at finer resolution.
This does not mean all changes are large, always negative, or present in
ordinary adequately resolved microscopy.

For identical times and equal-weight log-log OLS with an intercept,

    alpha_processed - alpha_native
      = slope of log(mean processed length / mean native length).

A constant multiplicative error changes the intercept, not slope. A varying
ratio can alter the slope, but need not: its fitted association with log time
must be nonzero. Use the ratio of ensemble means, not generally the mean of
run-wise ratios. This is established algebra, not a new theorem or unique
identification of the geometric cause.

Qualifications that must remain visible:

- Fraction matching shifts **chord** exponents only about -.00738 and -.01281,
  much less than half-height. Majority filtering lowers half-height slopes
  but raises chord slopes. Matched minority chords and half-height nearly
  agree, without establishing exact equivalence. Edge-censored chord selection
  changes over time and is not corrected away.
- Two predeclared warning screens accepted **zero of 18 comparisons**, including
  five with small exponent differences. Neither is a validated safe selector.
- A direct arithmetic audit found a first-zero roundoff issue in **37 secondary
  factor-eight lengths**, changing four fits, but not primary fourfold results
  or tolerance classes. The original records and correction remain disclosed.
- The width-128 .65 Tc extension gives broad **periodic** fits about .300 at
  .50 and .281 at .15 over **21,336-1,000,000** sweeps. These are not one-third
  plateaux. Nominal later fits fail the declared fivefold time-span requirement.
- An inventory inspected 72 width-128 runs / 6,000 snapshots. Under **both
  conservative planning heuristics**, no common window has the required four
  points across a fivefold span. These are not validated finite-size/physical
  accuracy criteria or proof that every image is unusable. They illustrate why
  duration alone does not solve the resolution/finite-field tradeoff.

This does **not** establish a new growth law, full explanation of the native
shortfall, exact literature reproduction, universally best length, or universal
finite-size-onset threshold. Choosing an estimator closer to 1/3 is not validation.

## 6. Prior research and the narrowed contribution

This table consolidates earlier bounded searches/primary-source checks; it is
not a new 18 October internet search or a census. No exact retrieved duplicate
does not mean no duplicate exists, nor prove publishability.

| Prior work | Consequence for this project |
|---|---|
| [Bray](https://arxiv.org/abs/cond-mat/9501089); [Majumder and Das 2010](https://arxiv.org/abs/1001.3985) | Conserved growth laws, transients and finite-size scaling are established physics. |
| [Roland and Grant 1989](https://doi.org/10.1103/PhysRevB.39.11971) | Block-spin processing and multiple lengths were already used on conserved Ising histories. |
| [Zabler et al. 2007](https://doi.org/10.1016/j.actamat.2007.05.028) | Threshold-dependent experimental coarsening fits, including a stable range, already exist. |
| [Werz et al. 2014](https://doi.org/10.1016/j.matchar.2014.01.022) | Real alloy analysis already combined downsampling, fraction adjustment and coarsening. |
| [Ledesma-Alonso et al. 2018](https://arxiv.org/abs/1712.03183) | Resolution-dependent descriptors and a reduction criterion exist. Our adaptation is not the full published method. |
| [Korneev et al. 2018](https://doi.org/10.1002/2018WR022886) | Porosity matching did not protect unresolved geometry/conductivity. Fraction-is-not-geometry is not new. |
| [Eidel et al. 2021](https://doi.org/10.1002/zamm.202000245) | Resolution errors and phase-ratio-aware mixed pixels/ties are established engineering concerns. |
| [Hoefler et al. 2025](https://doi.org/10.1016/j.matdes.2025.114279) | Practical materials work already addresses resolution and coarsening-fit uncertainty. |
| [ImageRep](https://doi.org/10.1002/advs.202414149), [PoreSpy](https://porespy.org/autoapi/porespy/metrics/two_point_correlation.html), [AQUAMI](https://github.com/JStuckner/aquami) | Representativity, correlations, geometry and reusable image software are existing capabilities. |

The possible incremental angle is a **specific paired kinetic benchmark**:
known conserved histories, explicit fraction matching, common fit masks,
trajectory uncertainty, justified observables, resolved success/failure cases
and a useful account of processing-induced fit changes. Not a new law,
segmentation algorithm or universal resolution criterion. Journal-level
novelty/significance remain unresolved; severe-resolution failure alone is
not enough. An adequately resolved comparison, justified baseline and
specialist criticism remain missing. Any costly new campaign needs its own
design, compute pilot and approval, not a larger number chosen for appearances.

## 7. Audit tool: one job and distinct levels of accuracy

**One job:** for an owner-approved binary mask, square-pixel calibration and
fixed rectangular field, compare declared directional correlation half-height
length at native, 2x and 4x resolution. Compare change with a tolerance chosen
by the owner beforehand; keep tie sensitivity, unresolved cases and warnings.
An owner can test mean length or both directions; errors can cancel in a mean.

The tool does not segment raw microscopy, restore boundaries, fit experimental
kinetics, infer chemistry from phase area or certify physical particle radii.
It has exact-input provenance, source-change detection, output hash checks/
local replay, minimal NumPy/SciPy/Pillow dependencies and a synthetic-only
allowlisted pilot-copy builder.

Recorded internal checks include:

- 324 synthetic measurements against a separately implemented rational reference.
- All **65,536 binary 4x4 fields**, agreeing within 4.44e-16 in unit-pixel
  lengths. This exhausts that small grid, not arbitrary images or materials.
- 216 convention comparisons / 432 directional checks on 18 known synthetic
  fields, agreeing within 4.44e-16. This is not running/outperforming PoreSpy.
- **268 repository tests** on 15 October and 14 subsequent focused tests.
  Dated developer checks are not student hours or independent human validation.

Numerical correctness, source consistency, image adequacy, segmentation,
calibration, physical validity and usefulness are different. Hashes establish
consistency, not truth/authentication. An experienced user could build the
comparison with existing packages. Convenience, traceability and failure
reporting are possible practical advantages, not demonstrated novelty/adoption.

## 8. Public data and the error-budget companion

| Public-data example | Bounded interpretation |
|---|---|
| MetalDAM, 42 static annotated steel fields | Thresholding, cleanup and reduction change static lengths. Cleanup can improve one statistic while worsening fraction error. Not independent ageing histories, calibrated kinetics, physical ground truth or deployment. |
| FeM, 81 iron-ore fields | Median changes about -.898% at 2x and +1.610% at 4x; opposite ties give about +1.925% at 2x. One mounted specimen, not 81 independent specimens; no owner tolerance/known engineering failure. |
| Published Al-Ge ROI stacks | Calibrated static 2D audit with unresolved planes/provenance. Sparse/unmatched regions and combined Ge morphologies prevent an experimental growth exponent claim. |

Producer annotations are references, not guaranteed truth. Original third-party
images are not broadly redistributed here. Public-data tests are not an
independent owner pilot, lab adoption or validation of Kawasaki alloy kinetics.

The equal-weight OLS companion gives a conservative slope bound from assumed
per-time length-ratio limits. On the primary grid, 5% agreement permits a
worst-case shift about .04998; an illustrative .02 exponent budget requires
about 2.002% agreement under the box assumption. **All four observed known
comparisons meeting 5% at every time had shifts below .02.** The permitted
worst-case failure is not an observed qualifying Kawasaki counterexample.
All 72 replayed comparisons are known-data analysis, not a new holdout or new
theorem. [Protocol](../research/KINETIC_ERROR_BUDGET_PROTOCOL_2026-10-15.md).

## 9. Current status and next gates

The latest two-page local PDF and current public Markdown source are prepared.
The historical long report needs consolidation. Student approval of every
claim/figure and any sent request are **not confirmed by the available record**.
No academic criticism, mentorship, owner adoption or publication acceptance
is established. Another AI cross-check is not independent human review.

The student has practised explanations, but dialogue agreement does not prove
independent derivation/coding proficiency. Private learning notes are not
published; the public AI contribution record must remain explicit.

Next: student explains/approves the question, test, result and limit; one
approved targeted criticism request; a justified resolved comparison and
existing-method baseline; a permitted owner-defined pilot if useful; then a
paper-readiness decision. Keep null/unresolved effects, criticism and changes.
A submission target is not acceptance/preprint, and publication is not required
for the project to be worthwhile. Do not launch another app or literature
marathon merely to postpone that first honest criticism request.

## Suggested prompt for Claude

> Read this and the linked evidence before proposing new work. Audit cohort
> counts, native-versus-processed comparisons, observables, uncertainty,
> resolution limits, corrections, closest prior art and AI disclosure. Identify
> supported, overstated and unverified claims. Is there a defensible incremental
> methods contribution, or a useful student replication/measurement report?
> Name the single smallest missing comparison that would change your judgement.
> Do not reward code volume, force an exponent to 1/3 or prescribe large runs
> without explaining the necessary decision they would support.

Ask Django for the separate private handover for learning/application context.
Those personal records are intentionally not in this public repository.
