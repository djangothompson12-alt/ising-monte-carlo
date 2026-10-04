# One question for the current report

Scope recommendation, 26 September 2026. Prepared with AI assistance for
Django to check. This is not a new experimental protocol, a student-approved
manuscript, or evidence of external review. Nothing has been published or sent
as part of this scope check.

## Recommended question

**After reducing image resolution, is matching the native species-site
fraction sufficient to preserve the fitted finite-window coarsening exponent
in 2D Kawasaki simulations?**

In plain English: if I make the images coarser but keep the same proportion of
each species, do I still measure the same growth exponent?

Suggested report title: *Does preserving species fraction preserve measured
coarsening? A resolution-sensitivity study of 2D Kawasaki simulations.*

The question is about recovering the **native finite-window fit**, not forcing
the answer to one third. Native means the original saved lattice analysed
with the same image-length definition and time window. It is a reference
measurement, not a uniquely correct physical domain size.

The original puzzle—why early fitted exponents were below one third—belongs
in the motivation. The longer runs, multiple sizes and literature comparison
explain the route to this question. The processing experiment does not resolve
all causes of the original native shortfall. Changes in processed measurements
cannot retrospectively explain an unprocessed result on their own.

This recommendation keeps the existing fraction-matching question. The broader
convergence question in `ACADEMIC_METHOD_CHALLENGE_AUDIT_2026-09-22.md` is useful
background and possible later work, not an additional requirement for the
Monday criticism package. Change scope again only for a specific scientific
objection, not to make the title sound more ambitious.

## Evidence to lead with

Use the [current short brief](ACADEMIC_REVIEW_BRIEF_2026-09-20.md) and
[fresh-cohort evidence](GROWTH_RELIABILITY_RESULTS_2026-09-19.md), not the older
PDF or an exploratory result presented as fresh confirmation.

The primary fresh experiment has 16 trajectories **in total**, eight at each
composition, with L=128, isotropic couplings and T=0.65 Tc. It is separate from
the 32-trajectory development set, the 128-trajectory long extension, and the
40-run T=0.6 Tc reference campaign. Its 24 retained checkpoints span
1,119–20,000 sweeps; these are not 24 independent replications.

| Native species ratio | Native exponent | Fraction-matched exponent | Paired difference, 95% bootstrap interval |
|---|---:|---:|---|
| 50:50 | 0.23141 | 0.18094 | −0.05047 [−0.05293, −0.04782] |
| 15:85 | 0.24214 | 0.16563 | −0.07651 [−0.08006, −0.07255] |

These are the factor-four, origin-zero, half-height results. The simulation
snapshots do not change between the paired analyses. Fraction matching is
exact at 50:50 and nearest-integer matching at 15:85. Report that rounding
residual. Whole-trajectory resampling estimates sampling uncertainty, not all
model or experimental uncertainty.

The supportable answer is **not necessarily**: matching fraction did not
preserve this exponent in the primary comparison. Matching can help at finer
resolution, so do not claim that it always fails or never helps. The same
fraction can describe different boundary arrangements. In these measurements,
the processed/native mean-length ratio also changes with time, explaining
the fitted slope difference without establishing a unique geometric cause.

The early window is a declared measurement stress test, not a demonstrated
asymptotic regime. Deliberately severe resolution loss makes a useful failure
example but does not establish how common the problem is in good microscopy.

A later [bounded chord/majority-filter appendix](CHORD_OBSERVATION_RESULTS_2026-09-26.md)
reuses this already-known cohort. It finds smaller fraction-matching shifts
for chords and opposite-sign majority-filter shifts across the two definitions.
Retain those qualifications. This exploratory check is supporting evidence,
not a replacement question, new holdout, or reason to claim every processing
choice has a large effect. The existing primary brief is unchanged.

## What the literature already covers

This was a bounded scoping search, not a systematic review of every paper.
Searches covered combinations of Kawasaki, coarsening exponent, segmentation,
phase/volume fraction, thresholding, image resolution, fraction matching and
microstructure representativity. Older project literature notes were checked
against primary sources and current tool documentation. An exact matching
study was not identified in the retrieved sources; that is not proof of
absence or a guarantee of publishability.

| Closest source | What it rules out as a novelty claim | Possible distinction here |
|---|---|---|
| [Bray (1994)](https://arxiv.org/abs/cond-mat/9501089); [Majumder and Das (2010)](https://arxiv.org/abs/1001.3985), [2013](https://arxiv.org/abs/1305.2556) | Conserved coarsening, finite-size/temperature/composition effects and measuring effective exponents are established. | Use as physics context, not a discovery of the growth law or a completed exact replication. |
| [Zabler et al. (2007), Fig. 8 and section 5.1](https://www.alexanderrack.eu/papers/zabler2007.pdf) | Testing fitted coarsening exponents against segmentation threshold/solid fraction was already done in experimental Al–Ge. They also found a relatively stable threshold range; effects need not always be large. | A paired, known-fraction control after defined resolution reduction on saved trajectories. |
| [Ledesma-Alonso et al. (2018)](https://arxiv.org/abs/1712.03183) | Image reduction changes normalized microstructure descriptors; fraction-related and shape changes are distinguished. A resolution criterion and real-image example already exist. | Quantify a time-series exponent difference after explicit fraction matching, rather than claim a new static descriptor or resolution-audit concept. |
| [Eidel, Fischer and Gote (2021)](https://doi.org/10.1002/zamm.202000245) | Resolution error in image-based materials modelling is an established engineering concern. | The target here is coarsening inference, not homogenized mechanical properties. |
| [Dahari et al., ImageRep (2025)](https://doi.org/10.1002/advs.202414149), [software](https://github.com/tldr-group/ImageRep); [PoreSpy](https://porespy.org/autoapi/porespy/metrics/two_point_correlation.html) | Correlation-based microstructure software and phase-fraction uncertainty tools already exist. | ImageRep addresses representativity; this paired audit addresses sensitivity to processing. It is not a replacement for existing tools. |

The candidate contribution is a reproducible, quantified dynamic benchmark
with specified processing, two compositions, paired uncertainty, fresh seeds
and disclosed failures. The fact that equal fractions do not specify geometry
is not itself new. Ask a specialist whether the benchmark adds enough beyond
the closest studies to justify a methods note. If not, an honest replication
and educational research report remain valid outcomes.

## Materials application and tool boundary

The practical question is whether downsampling or segmentation changes the
microstructural length someone intends to report. Existing public alloy-mask
tests demonstrate a workflow, not independent ground truth, experimental
growth-law validation or laboratory adoption. In a real alloy, segmented
phase area/volume fraction is not generally the same as chemical composition:
each phase can contain both species.

Two current warning screens accepted zero of 18 comparisons, including five
within the declared exponent tolerance. Keep that negative result. Do not
present the tool as a validated automatic selector of safe resolution, or the
partial directional literature adaptation as the full published method.

A useful next external test would be one owner-approved mask, a fixed region,
pixel scale, length statistic and owner-chosen tolerance, set before running.
Compare native and reduced-resolution measurements and ask whether the output
changes a real imaging decision. This establishes bounded usability if it
succeeds, not physical accuracy. Physical validation needs an independent
reference or appropriate paired measurements. Do not fit real ageing exponents
from unmatched, sparse regions simply because their scan labels contain times.

## Finish the initial criticism package

Revised target: Monday 5 October 2026, conditional on passing the checks below.
This is a target for a request for feedback, not publication or endorsement.

1. Agree the question above and keep one primary result. Django explains the
   comparison and its limitation in his own short paragraph; no new full
   theory quiz is required.
2. Assemble a concise two-page brief with the main result, an image comparison,
   uncertainty and three reviewer questions. Keep historical modelling work
   and extended tables in supporting material, not a second competing story.
3. Check every number, caption and run count against its own cohort. Explain
   the finite-image versus periodic estimator distinction and retain failed
   cases. The current source and old PDFs are not interchangeable.
4. Verify an accessible evidence copy: actual included data, working links,
   figure sources, dependencies and reproduction instructions. Do not promise
   that an unpublished local archive is already available through GitHub.
5. Django approves all claims, figures and the contribution/AI-use statement.
   The record should distinguish his decisions and understanding from
   AI-assisted design, programming, analysis and drafting.
6. Approach a relevant coarsening researcher and/or materials-characterization
   researcher with specific criticism questions, not a request to endorse an
   admissions profile. Sending requires Django's explicit approval.

Estimated student work for this compact first package: roughly 4–6 focused
hours across the weekend and Monday, depending on how much writing is already
approved. This excludes completing the full paper, waiting for replies and
addressing new scientific issues. Treat it as a planning estimate, not a
guarantee. Prioritize claim/caption approval Saturday, final reading and a
short spoken explanation Sunday, and recipient-specific approval Monday.

For the full technical report, use the same question: motivation and minimum
theory; paired methods; primary result and sensitivity checks; separate static
materials demonstration; limitations and criticism-driven revisions. Existing
Model A, anisotropy, phase-diagram and long-run work can supply background or
appendices. Do not start 3D engines, new hardware, a new app or additional
simulation campaigns before the first review unless a concrete error demands it.

## Checks performed on 26 September

The local orientation, README, both engines, historical LaTeX manuscript,
current result/limitations notes and relevant earlier task context were read.
The documented test command was rerun in the existing Python 3.11 numerical
environment: **192 tests passed**. An initial pytest invocation found pytest
absent; the project uses unittest, which completed successfully. No dependency
installation was needed. This test run is not a fresh recalculation of every
archived result or an external review. No simulation was launched, and no
commit, push, publication or outreach was performed.
