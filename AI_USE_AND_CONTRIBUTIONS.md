# AI use and contribution record

This project has been developed with assistance from generative-AI systems.
That assistance has included help with code generation and revision, debugging,
literature discovery, mathematical checking, figure generation through Python
code, and drafting or editing technical prose. AI systems are tools, not
authors, and cannot take responsibility for the work.

Django Thompson is the project maintainer and is responsible for deciding what
to retain and approving every public claim. On 10 September 2026, the coding
assistant executed the automated tests, numerical checks and new simulation
campaigns, drafted the new protocols and correspondence, and implemented the
analysis/export tools. Those actions must not be represented as independently
performed or fully understood by the student. Independent student review,
re-derivation and rerunning are still required before submission. No physical
tennis measurements were supplied or collected by the assistant.

The assistant subsequently designed the exploratory four-observable analysis,
implemented its analytic tests and paired bootstrap, ran it on all 24 pilot
replicas, and drafted `research/STUDY_DESIGN.md` and
`docs/PILOT_ESTIMATOR_RESULTS.md`. These are not independently student-derived
results or prose. The new comparison was specified after viewing the pilot;
it is not a preregistered confirmatory analysis.

The assistant then specified and implemented the controlled observation study
(`research/IMAGING_PROTOCOL.md`, `research/imaging.py`, `research/imaging_benchmark.py`),
executed it on the 64 completed long runs and eight newly seeded shorter runs,
and wrote its tests, source audit, experimental import utility and evidence-pack
builder. The new seeds were used for an independent repeat, not a claim of
external preregistration or validation of a fitted reliability classifier.
The assistant retrieved five original licensed AlGe slices, inspected their
metadata and images, and documented comparability problems. It did not collect
those experimental data, validate their segmentation, or establish agreement
between experimental kinetics and the Ising model. The student still needs to
review, reproduce, interpret and write the paper in their own words.

On 14 September, the student supplied an earlier Model A paper opening in
their own words. The assistant archived it privately, checked its numerical
and physical claims against the current code and CSV, and drafted a public
progress/limitations page and clearer repository documentation. The student
has not yet approved those draft words as their own academic writing. The
0.6Tc literature campaign is incomplete at 7/40 planned runs; no benchmark
result or external endorsement has been obtained.

Before any external submission, this record should be expanded
with the exact tools, dates, and sections affected, and the target venue's
current AI policy must be checked in writing.

The repository must not be submitted to a venue whose rules prohibit the ways
AI was used. In particular, the current Journal of Emerging Investigators
policy prohibits AI assistance for modelling, calculations, analysis, figures,
literature work, and manuscript writing; the present project is therefore not
eligible there in its current form.

## Human-verification checklist before a release

- Re-run every script that contributes a claimed number or figure.
- Read every cited source directly and confirm it supports the associated claim.
- Re-derive the Ising/regular-solution map and LSW normalization independently.
- Review all fitting windows and distinguish fit standard error from replica or
  model uncertainty.
- Confirm that Model A is described as Metropolis single-spin-flip dynamics,
  not Glauber dynamics.
- Confirm that connected correlations are used only where the conserved
  magnetization makes the subtraction physically appropriate.
- Record every external review comment and the resulting change.

This document is a transparency record, not proof that those checks have all
been completed. Release notes should state which checks were actually run.
