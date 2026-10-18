# What the audit can establish, and the possible methods-paper angle

Working synthesis, 15 October 2026. Prepared with substantial Codex assistance
for Django to check. This is not a student-approved paper, an exhaustive
systematic review, a novelty certificate or evidence of outside use.
Nothing was submitted, published, pushed or sent as part of this work.

## 1. Keep the question we already chose

**After reducing image resolution, is matching the native species-site
fraction sufficient to preserve the fitted finite-window coarsening exponent
in 2D Kawasaki simulations?**

In simpler terms: if I make the images coarser but keep the same proportion
of each species, do I still measure the same growth rate?

The reference is the native measurement on the same saved configurations,
using the same length definition and fit window. It is not a unique true
domain size, and the question is not whether processing can force the answer
to one third. The original below-one-third puzzle explains how the project
started; it does not become a claim that processing explains every native
shortfall. Keep this as one report, with the new budget analysis supporting
it rather than becoming another competing main question.

## 2. What the project actually contains

| Strand | What exists and why it was added | Boundary |
|---|---|---|
| Model A | Non-conserved Metropolis single-spin flips and interactive demonstration; a contrast for local interface motion. | Not Glauber acceptance, not a conserved binary-alloy ageing predictor. |
| Model B | Conserved nearest-neighbour Kawasaki exchanges; adjustable composition, quench and horizontal/vertical couplings in the visualiser. | A 2D idealised lattice, not a calibrated alloy. Controlled studies use Jx=Jy=1. |
| Longer physics campaigns | The 0.65 Tc extension has 128 trajectories: 16 per size/composition, sizes 32,64,96,128, two compositions, to one million sweeps. The separate 0.6 Tc symmetric reference has 40 L=128 trajectories to 4.5 million sweeps. | Do not pool them or call the single-size reference a completed replication of published finite-size scaling. Preparation also differs: 200 sweeps in the extension, zero in the reference. |
| Paired observation study | Known saved lattices are integrated, thresholded or fraction-matched. Development and fresh-seed cohorts are distinct. | Processing is applied after dynamics; it never feeds back into a simulation. |
| Primary fresh comparison | Sixteen trajectories total, eight per composition, L=128, 0.65 Tc. Twenty-four common checkpoints, 1,119-20,000 post-quench sweeps. | Early/severely reduced images are a stress test, not a demonstrated asymptotic or well-resolved microscopy regime. |
| Sensitivity and controls | Alternative windows/observables, five matching tie priorities, four grid origins, prescribed checkerboards and an exploratory chord/majority appendix. | Shared trajectories and ties are not independent additional simulations. Retain small and opposite-sign effects. Artificial scales are not MCS. |
| Real-image demonstrations | Static MetalDAM, Al-Ge, MicroAl and FeM comparisons, each with its own source/segmentation/calibration limitations. | Not an experimental ageing-law validation, independent specimens by image count, or external adoption. |
| Narrow mask audit | An owner supplies an approved binary 2D mask and scale; the tool compares its declared directional half-height measurement under direct 2x/4x digital reduction. | Not raw-image segmentation, particle radius, chemical mass balance, microscope acquisition modelling or strength prediction. |

The Ising Hamiltonian penalises unlike neighbours for positive couplings.
Metropolis accepts an attempted move with min(1, exp(-DeltaE/T)) in the chosen
kB=1 units. One sweep is L squared attempted moves, not one successful move
or one guaranteed visit to each site. Small-lattice balance and Hamiltonian
checks verify defined numerical properties, not the validity of an alloy model.

The expected diffusion-controlled late growth law follows the scaling
d ell/dt proportional to ell^-2, giving ell proportional to t^(1/3), under
the relevant assumptions. A finite-window fit need not equal that limit.
Composition, temperature, morphology, preparation, observable, finite time
and finite size must not be treated as interchangeable explanations.

## 3. What the primary data say

| Native species fraction | Native fit | Factor-four fraction-matched fit | Difference and paired 95% interval |
|---|---:|---:|---|
| 0.50 | 0.23141 | 0.18094 | -0.05047 [-0.05293,-0.04782] |
| 0.15 | 0.24214 | 0.16563 | -0.07651 [-0.08006,-0.07255] |

Lengths use finite, nonperiodic, globally centred directional covariance and
its interpolated half-height crossing. This is distinct from the periodic
engine correlation. Five fixed coordinate tie priorities are averaged within
each trajectory/time; whole trajectories are the paired bootstrap unit.
Matching is exact at 0.50 and nearest-count at 0.15, with a recorded rounding
residual. The comparison does not require every run to have exponent one third.

The supportable conclusion is **not necessarily**: matching fraction did not
preserve the native fit here. It can help at finer resolution. Equal fraction
does not specify boundary geometry, but that fact itself is not new.
Severe under-resolution limits how much can be inferred about ordinary good
microscopy. The chord appendix gives smaller fraction-matching shifts; keep it.

Two prior warning screens accepted zero of 18 declared comparisons, including
five with small exponent differences. They are not validated safe-resolution
selectors. A later direct arithmetic audit corrected 37 secondary factor-eight
positive-lobe lengths and four fits; primary factor-four results were unchanged.
Neither negative evidence should disappear from a methods paper.

## 4. Improvements completed in this work

The current static audit already had directional criteria, opposite exact-tie
checks, resolution warnings and an independent exact-rational reference.
This development adds:

1. **Exact-input provenance.** Load and hash the same mask bytes. Hash the
   actual input document parsed, not a second read after the calculation.
   Detect changed analysis sources before output creation. Record Python,
   NumPy, SciPy and Pillow versions.
2. **Delivery verification and optional local replay.** Check the four named
   output hashes, retain an old-source warning, and optionally reproduce the
   numerical tables from the original local plan and masks. Replay comparisons
   use relative rather than an arbitrary absolute physical-unit tolerance.
3. **Exhaustive small-grid verification.** All 65,536 possible 4x4 binary
   fields agreed with the independent rational reference; maximum absolute
   disagreement was 4.44e-16 in unit-pixel lengths. Both axes were resolved
   in 64,514 fields, one axis only in 1,020, neither in two. This exhausts
   only that smallest grid, not larger images or physical accuracy.
4. **A lighter local workflow.** A separate dependency file needs only NumPy,
   SciPy and Pillow. Tests block plotting, simulation and web-stack imports.
   This is not a fresh-machine or all-platform installation certificate.
5. **An allowlisted review bundle.** Source, minimal instructions and explicitly
   artificial example masks can be copied locally without original microscopy,
   raw campaigns, private planning or outreach. A prepared ZIP is not a release.
6. **A fixed-fit error-budget companion.** It replays known time-series results
   without turning the static tool into an experimental kinetics validator.

Hashes establish consistency with a manifest, not authentication or truth.
Someone could change a table and rehash it. Replay catches numerical
disagreement with the implementation and local inputs, but is not an
independent algorithm. The separately coded rational checker is a different
kind of verification. Neither validates segmentation or calibration.

## 5. The new supporting calculation

Write q_i = mean(processed length)_i / mean(native length)_i on the **same**
retained time grid. For equal-weight log-log OLS with an intercept,

    w_i = (log(t_i)-mean(log(t))) / sum((log(t)-mean(log(t)))^2)
    Delta alpha = sum(w_i log(q_i))

If every ratio lies in [a,b], a sharp interval-box bound is

    |Delta alpha| <= S log(b/a),  S = sum(abs(w_i))/2.

For a common relative tolerance epsilon, use a=1-epsilon, b=1+epsilon.
A sufficient epsilon for an exponent budget B is tanh(B/(2S)). This is
elementary regression error propagation, **not a new theorem**. The extremal
ratio pattern need not be realisable by a particular image operator. It
assumes every retained ratio is covered, not merely one checked image.

On the primary 24-point grid, keeping every length within 5% permits a
worst-case slope difference of approximately **0.04998**; 10% permits
approximately **0.10022**. To guarantee a difference at most 0.02 under this
conservative box assumption requires approximately **2.002%** per-time
agreement. These are illustrative numerical budgets, not lab standards.

All **72 related half-height comparisons** were replayed, preserving the
archived common time masks and tie averaging. Their fitted slopes match the
archived table; the maximum slope-accounting disagreement was below 2e-16.
This is a supporting analysis of known data, not a new holdout.

An important qualification: four actual comparisons stayed within 5% at every
time, and eight stayed within 10%; **none** of those had a point exponent
shift above 0.02. No comparison met the 2% static criterion throughout.
Thus the general bound permits a failure that these qualifying observed
cases did not exhibit. Do not advertise the theoretical witness as an
observed Kawasaki or experimental counterexample. Constant scale bias also
shows why the bound is sufficient but not necessary.

Code: `research/kinetic_error_budget.py` and
`research/audit_kinetic_error_budget.py`. Dated design:
`research/KINETIC_ERROR_BUDGET_PROTOCOL_2026-10-15.md`. The local report is
`output/kinetic_error_budget_2026-10-15_v2/report.html`; recreate in a new
folder with `python -m research.audit_kinetic_error_budget --output NEW_FOLDER`.

### Final local verification record

The full repository suite passed **262 tests** after the code changes, and
the 11 error-budget tests were rerun after the report wording qualification.
The final independent exact checker again passed 324 measurements; the final
exhaustive run reproduced all 65,536 fields and its reference-result digest.
The cached single Al-Ge mask and the synthetic demonstration were rerun with
the final audit sources and passed delivery hashes plus local numerical replay.
The Al-Ge result remains a reused static plane, not a new specimen or an
experimental kinetic test. The 81-field FeM replay recorded on 13 October was
not repeated here; its former temporary raw-data location is no longer present.

The local synthetic-only pilot ZIP is
`output/mask_audit_pilot_2026-10-15_v1/mask-audit-pilot.zip`: **39,233 bytes**,
23 allowlisted files. An extracted copy, outside the working repository,
passed source matching and numerical replay; its 324-case exact checker was
also rerun. This uses the existing installed Python environment, not a new
machine or a fresh dependency installation. The minimal-stack test separately
blocks the optional plotting, simulation and web dependencies.

No frozen source, original image, saved trajectory or historical result was
overwritten. No commit, push, outside contact or submission was performed.

## 6. Closest literature and software, checked again

This is a **bounded scoping search**, not a search of every published paper.
It combined the existing repository comparisons with scholarly-web queries
on conserved coarsening, resolution, binning, thresholding, fraction/volume
preservation, correlation lengths, temporal bias, error budgets and existing
microstructure software. Recent 2025-2026 records and primary institutional/
publisher/software sources were included. A missing exact match is not proof
of a gap. Some direct publisher fetches were blocked; record-level or indexed
primary-source content was used where stated.

| Closest work | What was checked | Consequence |
|---|---|---|
| [Bray, Theory of phase-ordering kinetics](https://arxiv.org/abs/cond-mat/9501089) | Established theoretical background; retained from the earlier project search. | Growth laws and universality classes are not this project's novelty. |
| [Majumder and Das 2010](https://arxiv.org/abs/1001.3985) | Primary record rechecked; finite-size scaling in conserved 2D Ising dynamics. | Compare methods, finite windows, temperature and preparation; do not claim a new one-third law or a completed method-matched replication. |
| [Zabler et al. 2007](https://doi.org/10.1016/j.actamat.2007.05.028), [author manuscript](https://www.alexanderrack.eu/papers/zabler2007.pdf) | Section 5.1 and Fig.8 discussion; relevant page visually checked. | Threshold-versus-fitted-exponent analysis already exists, including a relatively stable fraction range. Generic threshold sensitivity and claims that every change is large are unavailable. |
| [Werz et al. 2014](https://doi.org/10.1016/j.matchar.2014.01.022), [author manuscript](https://pure.hw.ac.uk/ws/files/10435481/WeBaWo14_preprint.pdf) | Printed pages 7-8 visually checked: factor-two downscaling, watershed/boundary treatment and adjusted effective fraction. | Downsampling combined with fraction adjustment in real coarsening analysis is prior art. Their morphological adjustment is not the same algorithm as our rank matching. |
| [Ledesma-Alonso et al. 2018](https://arxiv.org/abs/1712.03183) | Descriptor definitions and page-11 algorithm visually/text checked. | Resolution-dependent descriptors and a reduction criterion already exist. Our directional-only adaptation does not reproduce their three descriptors, both phases and sequential decimation. |
| [Eidel, Fischer and Gote 2021](https://doi.org/10.1002/zamm.202000245) | Full-text section 4.1 on mixed pixels, majority coarsening and phase-ratio-aware ties. | Even order-dependent tie decisions are discussed already. Do not claim the tie audit or conserving an image mean is a new idea. Their response quantity is mechanical, not our kinetic fit. |
| [Lendvai, Kabel and Schneider 2025/2026](https://doi.org/10.1007/s00466-025-02716-z) | Open full text: subvoxel fractions, interface geometry and homogenisation controls. | Quantified resolution-error analysis and analytic-geometry controls are established; retaining fractions alone does not encode interface normals. Their contribution is not a kinetic exponent audit. |
| [Hoefler et al. 2025](https://doi.org/10.1016/j.matdes.2025.114279) | Indexed primary article sections on superalloy image analysis/coarsening; direct full-page access was blocked in this run. | Resolution cutoffs, magnification-dependent errors and propagated coarsening-fit uncertainty are practical existing concerns. Do not say no engineer has addressed this issue. |
| [Dahari et al., ImageRep 2025](https://doi.org/10.1002/advs.202414149) | Open article and official project context. | Phase-fraction representativity uncertainty from one image is already a research-software problem. Sampling representativity and processing sensitivity are different questions. |
| [PoreSpy](https://porespy.org/autoapi/porespy/metrics/two_point_correlation.html), [AQUAMI](https://github.com/JStuckner/aquami), [MorphoLibJ](https://imagej.net/plugins/morpholibj) | Official documentation/repositories; AQUAMI's [2017 paper record](https://doi.org/10.1016/j.commatsci.2017.08.012). | Correlation, feature lengths, phase fractions, calibrated image geometry and reusable analysis software already exist. Our workflow should complement them, not claim to replace them or invent metrology. |

The strongest possible distinction is the **specific paired dynamic benchmark**:
explicit fraction matching; known, conserved simulation histories; common
time windows; trajectory-level uncertainty; several observables; success and
failure cases; and a traceable account of what static agreement can or cannot
guarantee for a stated finite-window fit. No retrieved source established this
exact package as a mature standard, but its novelty and significance remain
questions for an expert, not established findings of this search.

## 7. Candidate methods paper, without changing scope again

Working title: **Auditing finite-window coarsening fits after
fraction-preserving image reduction**.

Potential contribution: a small reproducible benchmark and audit workflow
that tests whether fraction preservation and static descriptor agreement
are adequate checks for a kinetic conclusion. The practical outcome would
be a justified processing choice or an explicit refusal to trust that fit,
not a new physical exponent or a claim to predict an alloy.

Three connected outputs are enough: (1) the paired simulated-image result,
(2) the verified static-mask audit, (3) a calibrated outside demonstration
with the right limitations. A new visualiser, 3D simulation, AI segmentation
system, neural network or unrelated physical build is not needed for this angle.

What is still missing before describing it as a publishable methods study:

1. **Independent specialist judgement of the question and closest work.**
   Ask whether the comparison adds useful evidence, not whether the expert
   will endorse a university application.
2. **A defensible adequately resolved success/failure domain.** The current
   stress test is not enough to establish broad practical performance.
   The saved long-run inventory does not provide a long common window passing
   both of its conservative planning screens. Do not relax them by outcome.
3. **A justified baseline.** Compare a relevant established descriptor/
   processing workflow. Do not say we outperform the full Ledesma method
   without a faithful implementation and matched outcome.
4. **One legitimate outside question.** An image owner should specify the
   descriptor, field, pixel calibration and useful tolerance before a pilot.
   A static mask can test a static decision, not validate a dynamic exponent.
5. **Human ownership and review.** Django must understand the estimand,
   controls, failures and code-assistance statement and write/revise the
   scientific argument. A numerical checker cannot supply that contribution.

The targeted question for a reviewer is:

> Does this paired fraction-matching benchmark add a useful methods question
> beyond the published threshold/resolution work, and what single missing
> control or adequately resolved comparison would you require before a short
> methods-paper submission?

An honest answer of "not enough for publication" is still useful direction.
Keep the first contact to the existing concise brief; offer the code/evidence
or the small static-tool copy as optional supporting material, not a demand
to read every experiment at once.

### A small paper outline, if the specialist thinks it adds something

1. **Problem:** fraction matching is a plausible check on processed two-phase
   images, but the decision of interest is a fitted kinetic quantity.
2. **Design:** unchanged paired saved configurations; declared observation
   operators, length definitions, common fit windows and trajectory resampling.
3. **Result:** the primary differences above, then the smaller/helpful cases
   and the chord qualification. Do not show only the largest discrepancy.
4. **Error accounting:** time-dependent length ratios explain the fit shift;
   the elementary box bound separates a static tolerance from a slope budget.
5. **Useful workflow:** input contract, numerical reference, failure handling,
   exact-version reproduction and one owner-defined static decision.
6. **Limits:** severe resolution loss, small ensembles, non-unique lengths,
   incomplete published-method baseline, no experimental kinetic validation.

The publication-shaped output is not a polished version of every project
experiment. It is this one argument, with only the controls needed to defend
it. The longer engine history belongs in the technical report or supporting
material. Do not write an abstract claiming utility, novelty or adoption
before those claims have evidence.

## 8. Additional public-data routes screened, not analysed

The [Gesch and Hu Ostwald-ripening dataset](https://doi.org/10.18126/ccqv-t437)
lists binary NumPy time frames, multiple labelled phases and a CC BY 4.0
licence. It is an **independent simulation source**, not real experimental
alloy data. Access is via Globus and parameters are separately available
from the authors; no transfer, permission request or parameter recovery was
performed here. A small declared subset could later test transportability
after conventions are confirmed.

The [GelMA-Dextran supporting record](https://zenodo.org/records/15546716)
lists phase-separation movies and AQUAMI length-analysis archives. It is a
potential **experimental materials-imaging** source, not a binary-alloy
benchmark. Acidification and evolving phase behaviour complicate a conserved
coarsening interpretation. The inspected record's licence field was blank;
calibration, supplied masks, current version and reuse conditions need checking.
No files were downloaded or new experimental exponents fitted.

The [OPMD record](https://zenodo.org/records/7702179) describes phase-field
image data but the inspected ZIP subset is final-time rendered images,
not automatically a calibrated time series of raw composition fields.
Do not treat its image count or RGB renderings as ready kinetic evidence.

These leads do not justify another large download or a new campaign before
the existing brief is understood and criticised. Previously inspected real
Al-Ge planes remain static demonstrations with missing/unresolved cases.

## 9. Publication route and stopping rule

A methods article is a possible later outcome, not a present credential.
[Elsevier's Research Elements description](https://www.elsevier.com/en-gb/researcher/author/tools-and-resources/research-elements-journals)
and [methods-transparency discussion](https://www.elsevier.com/en-gb/connect/reproducibility-why-it-matters-and-how-it-can-be-nurtured)
make MethodsX a scope to investigate **after** method validation and expert
criticism; current article type, requirements, costs and any waiver must be
checked before selecting a venue. No cost or eligibility is assumed.

[JOSS's current submission rules](https://joss.readthedocs.io/en/latest/submitting.html)
require substantial research software, demonstrated use, human contribution,
open practices and more than six months of public development. A small
single-job utility is not automatically eligible; neither today's test count
nor a polished ZIP makes it a quick publication route. The rules also require
accurate AI disclosure. Do not manufacture public history or outside use.

Stop autonomous expansion at verified local software, a reproducible
supporting calculation and a candid scope memo. The next new evidence that
matters is the student's approved explanation and an actual specialist's
criticism or owner-led pilot. No amount of additional automatic checking can
supply human review, novelty judgement, adoption or authorship by proxy.
