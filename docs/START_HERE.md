# Start here

For a quick, honest account, read [expected versus observed](EXPECTED_VS_OBSERVED_2026-09-18.md)
and [progress and limits](PROGRESS_AND_LIMITS.md).
For the materials-science bridge, read the [mean-field binodal derivation](REGULAR_SOLUTION_BINODAL_2026-09-18.md),
the [exact 2D coexistence check](EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md),
and the [published Fe–Cr structure–hardness case](FECR_MATERIALS_CASE_STUDY_2026-09-18.md)
as **separate** theory and experimental context, not a model calibration.
Then read [the completed long-run results](OVERNIGHT_RESULTS.md) and
[the observation study](MEASUREMENT_STUDY_RESULTS.md). The newer, released
[128-run extension appendix](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md)
contains all declared fits and unresolved rows; its [fixed new-seed image
test](../research/runs/main_065_multisize_v1/image_holdout_v1/REPORT.md)
is a directional measurement check, not alloy validation. A later
[paired check](PAIRED_WINDOW_AUDIT_2026-09-18.md) quantifies the
fitting-window shift on the same eight L=128 runs; it is post-result and
does not pick an asymptotic window. The raw trajectories
for those studies are described in [the data guide](../research/DATA_README.md).
For the separate 40-run reference comparison, use the
[paper-to-code method crosswalk](MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md)
before approving any comparison declaration or fitted result.
The later [independent observable audit](ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md)
checks calculations against the saved lattices, while the
[binning decomposition](BINNING_DECOMPOSITION_RESULTS_2026-09-17.md) separates
block averaging from thresholding. Both are AI-assisted follow-ups to the
original study, not independent physical validation.
A [known-growth synthetic control](SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md)
tests the image estimator on a constructed exact one-third growth law. It
checks interpretation of the measurement, not the Kawasaki dynamics or an alloy.
Earlier experimental slices were inspected for feasibility. A separate
[segmented Al–Ge test](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md) now checks a
fixed 4× observation choice on four public solid-state-ageing stacks and
retains failed early-stage measurements. Neither is a validated
quantitative coarsening benchmark.
The separate [40-run, L=128 long-reference dataset](REFERENCE_RUN_INTEGRITY_2026-09-17.md)
has completed and passed internal checks, but has **not** yet produced a
student-verified comparison to the published paper. A [public 4D Al–Cu data
candidate](EXTERNAL_DATASET_SCOUT_2026-09-17.md) has been identified, not
analysed or used by an outside lab.
For a possible external test, use the [bounded partner-pilot
protocol](PARTNER_PILOT_PROTOCOL_2026-09-17.md) to ask a real imaging expert
what quantity matters before offering code or claiming use.

A separate [annotated-steel image pilot](METALDAM_STATIC_PILOT_2026-09-17.md)
and [mask-cleanup follow-up](METALDAM_CLEANUP_SENSITIVITY_2026-09-17.md) test
whether an image-processing choice changes a measured length. They are
exploratory measurement stress tests, not real-alloy ageing validation.
The later [expert-mask resolution audit](METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md)
tests the same static length measurement on producer annotations at several
pixel resolutions; it also is not kinetic or external-use validation.

The priority is to understand the replicated Kawasaki study well enough to
explain its figures and limits. [The research design](../research/STUDY_DESIGN.md)
connects data to questions and report figures. The tennis-string study is a
separate, optional mechanics experiment; it does not validate Ising.

## For a technical review

1. Read the [fixed extension protocol](../research/MAIN_EXTENSION_PROTOCOL.md),
   [all-row appendix](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md),
   and [claim audit](CLAIM_AUDIT_2026-09-17.md). Explain why a finite-window
   slope near one-third is not a demonstrated asymptotic law.
2. Read [the writing guide](../manuscript/WRITING_GUIDE.md) and write the short
   explanation yourself. Mark what you do not yet understand.
3. Open [the review brief](review_brief.html). Check every sentence against what
   has actually been done and understood. It is a draft, not a sent message.
4. Ask a reviewer for one narrow technical criticism, not general endorsement.

## Completed computation

The 24-replica pilot and all 64 replicas of the 200,000-sweep campaign are
complete. Read [the overnight results](OVERNIGHT_RESULTS.md) for the primary
analysis, its source/input provenance and the small-lattice missing-data caveat.
A separate 0.6Tc, 50:50, L=128 raw campaign completed 40 of 40 trajectories;
its paper-method comparison is still gated. The separate 0.65Tc size/time
extension completed all 128 trajectories, along with internal raw-file,
observable and table audits. Its released results are finite-window
measurements, not a growth-law proof. The [matched-size
addendum](../research/MAIN_EXTENSION_MATCHED_SIZE_ADDENDUM_2026-09-17.md)
specified a limited comparison before results were read; it did not
predeclare a finite-size onset or treat L=128 as an infinite-system reference.

The pilot already shows strong fitting-window sensitivity at c=0.5: about
0.17 using the wide window and 0.24 when fitting from 1,000 sweeps, with similar
values across L=32,64,96. This is preliminary evidence, not proof of the
asymptotic exponent or a finite-size explanation.

## What the software can measure

| Tool | Output | What is needed for a physical test |
|---|---|---|
| Ising engine / paused dashboard export | Raw directional length in sites, heat, lattice, parameters | Comparable observable and justified material/time mapping; not supplied by changing axis labels |
| Campaign analyser | Replica growth curves, effective exponents, candidate scaling plots | Independent review of estimator and fitting windows |
| Tennis string tool | Predicted frequency (Hz), conditional force estimate (N), validation residuals | Known load, loaded density and span, checked fundamental, real recordings |

No code here predicts racket performance or an industrial alloy's ageing time.
See [physical measurements and calibration limits](PHYSICAL_MEASUREMENTS.md)
for what would be needed to make those further claims.
There is no need to buy tennis-testing equipment to progress the Kawasaki
paper. Prioritise the numerical evidence and understanding it well enough to
discuss it with a materials researcher.

## Before publication or claims of validation

The source code and selected completed simulation archives are public working
materials, not a peer-reviewed release. A reply, introduction, submission or
DOI is not endorsement. Ask permission before naming or quoting a reviewer.
Keep specific criticism and any resulting revisions as part of the record.
