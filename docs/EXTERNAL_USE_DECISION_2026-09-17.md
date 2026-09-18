# Research-to-use decision (working note, 17 September 2026)

This note is an AI-assisted planning and evidence record, **not** a student-authored
application statement, claim of external validation, or paper conclusion.

## Decision

Keep the scientific paper centred on **how composition, fit window and
observation method affect the measured growth of conserved 2D domains**. The
40-replica literature benchmark and its queued longer-temperature extension
must be checked before interpreting the apparent sub-1/3 exponent. Compare
methods on identical archived snapshots. A low finite-window slope by itself
is not a discovery, and finite size is not yet an established explanation.

Develop **one separate applied pilot**: a microstructure-image measurement
audit that exposes how phase fraction and correlation length change with a
declared segmentation choice. Its immediate user would be an imaging researcher
deciding whether a length measurement is robust enough to report. The Ising
data supply a known controlled microstructure sequence for methodological
testing; they do not calibrate an alloy or predict its strength.

Why this route rather than another model dimension, drone analogy or alloy
strength curve now: it asks for an independently checkable result on real
micrographs, is close to the existing measurement-sensitivity finding, and
offers a specific question an external researcher can challenge. It could
also fail. If an imaging researcher already has a superior workflow or does
not need this metric, the honest result is a negative pilot, not adoption.
Published materials-imaging papers already compare segmentation scores with
downstream size and thickness errors (for example
[this 2022 study](https://www.nature.com/articles/s41524-022-00878-5));
therefore the general idea is **not novel**. A distinctive contribution would
need to come from a useful, reproducible protocol or partner-specific result.

## What “external use” would require

1. **Public-data test.** State the material, phase label, image/annotation
rights, sample grouping, image scale and outcome definition. Report failure
cases and keep any mask-optimised threshold separate from image-only choices.
2. **Problem-owner conversation.** Ask a materials microscopist or engineer
which quantity they currently extract, what decision it informs, and what
current method they use. Do not offer the current tool as a validated solution.
3. **Bounded partner pilot, if invited.** Use only approved images and a
pre-agreed comparison, such as annotated phase fraction or a blinded manual
length reading. Record whether the partner found the audit useful, useless,
or misleading; no testimonial is owed.
4. **Independent review of the paper.** Ask the reviewer to critique the
definitions, statistics, literature positioning and physical limits. A
recommendation letter is appropriate only if they have actually mentored the
student enough to describe his intellectual contribution and response to
criticism.

Steps 1 and the preparation for 2 can be done locally. Steps 2–4 depend on
other people's time and consent. No industry or academic endorsement, paper
acceptance, adoption, or admissions category follows automatically.

## Bounded public-data pilot selected

The [MetalDAM producer release](https://github.com/ari-dasci/OD-MetalDAM)
contains 42 annotated SEM images of additively manufactured steel. Its
authors explicitly warn that most tiny precipitates were omitted from labels.
Therefore class 3 must **not** be used to validate precipitate detection.
The first stress test uses the much more prevalent published class 1
(austenite), and compares two image-only Otsu polarities and an explicitly
in-sample, label-optimised ceiling. It measures correlation half-height
length in pixels only; no calibration is inferred from a magnification label.
The dataset consists of static images of a different material system, so it
does not validate phase-ordering kinetics. Images remain in ignored local
storage; the public repository should contain code, source citation, hashes
and aggregate measurements, not redistributed micrographs. The release page
does not clearly state a reuse licence; resolve that before publishing any
image or derived preview.

## Stop/go gate after the pilot

- If threshold-only segmentation disagrees substantially with expert masks,
do **not** sell the present audit as a practical phase-measurement product.
Write the failure and consider whether an expert-provided mask should be the
input instead.
- If it agrees on one dataset, that is only feasibility. Repeat across a
different material/imaging condition and seek expert interpretation before
claiming usefulness.
- A pilot counts as external use only when a real researcher elects to apply
the workflow to their own approved problem and can say what decision it
helped. A meeting, preprint, or downloaded report alone is not deployment.

## Status after the public-image stress test

The [42-image steel pilot](METALDAM_STATIC_PILOT_2026-09-17.md) and its
[post-hoc cleanup test](METALDAM_CLEANUP_SENSITIVITY_2026-09-17.md) now make
the threshold-only workflow a **no-go for practical phase measurement**.
Although the raw dark-Otsu mask's median Dice against the published austenite
labels is 0.825, its median measured/reference correlation-length ratio is
only 0.426. A 3×3 median cleanup raises that length ratio to 0.609 but
worsens median absolute phase-fraction error from 0.179 to 0.194. Published
labels themselves have limits, and this post-hoc result is not a held-out
validation. It shows why overlap score or a cleaner image alone cannot be
used to promise a reliable material measurement.

The next external conversation should ask a microscopist **which downstream
measurement matters and what mask/scale they trust**. A bounded tool that
audits expert-supplied masks may eventually be useful; building it without a
problem-owner definition would be more code, not evidence of use. No company
or lab has applied the current workflow as far as this record establishes.

**18 September update:** an [exploratory expert-mask resolution audit](METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md)
now supplies a more defensible *static* demonstration than thresholding the
raw photographs. It holds the producer mask and field fixed, degrades pixel
resolution by predeclared factors, and records the resulting length and phase
fraction. At 4× coarser resolution the measured length rises in all 42
masks (median ratio 1.050); at 8× the median is 1.195. This still lacks
physical pixel calibration, independent specimens, a partner's decision
threshold and any external user. It strengthens the **question to ask**, not
a deployment or endorsement claim.

A separate [public 4D Al–Cu dataset scout](EXTERNAL_DATASET_SCOUT_2026-09-17.md)
identifies a potentially better *time-series measurement* test. Access,
licence, common specimen/scale and appropriate outcome remain unverified, and
its solid–liquid mechanism is not this model's solid-state binary analogue.
It is not a reason to restart the threshold-only steel pilot or announce
experimental validation. Relevant correlations were already studied on the
Al–Cu system by [Sun et al. 2017](https://doi.org/10.1016/j.actamat.2017.04.054).
The [bounded partner-pilot protocol](PARTNER_PILOT_PROTOCOL_2026-09-17.md)
states what would count as a useful test and when to stop.

**18 September Al–Ge update:** four CC BY 4.0 solid-state-aged, segmented
Al–Ge ROI stacks were downloaded and checked under a separate
[fixed exploratory image-operator protocol](../research/ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md).
The [result](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md) is mixed and deliberately
bounded: early interior crops often contain no Ge and have no defined
correlation length; two later stages show a static resolution-dependent
length, but all images come from one specimen. This is more relevant to
materials characterisation than the threshold-only steel photos, yet it
does **not** turn the Ising model into an experimentally validated ageing
predictor or an externally used lab tool. An expert still needs to define
the feature/ROI that matters to their actual decision. The source paper
itself distinguishes Ge lamellae and newly formed precipitates, while our
first all-Ge binary length combines both. It cannot be treated as a
precipitate radius or compared with hardness without a new, expert-led
population definition and independent material measurements.

## Work estimate from this state

These are *active-work ranges*, excluding unattended simulation time and
unpredictable waits for reviewers or companies:

| Outcome | AI/assistant work | Student work | External elapsed time |
|---|---:|---:|---|
| Audit completed runs, verify figures and prepare a concise review packet | 8–15 h | 5–10 h to rederive, inspect and explain | none |
| Student-authored, defensible paper plus revisions | 8–15 h for checks/figures/editing support | 15–25 h writing and source verification | 1–4+ weeks for feedback |
| Real-image test and partner-ready pilot, if method survives | 6–12 h | 3–6 h to understand and present it | days to weeks for a technical partner |

The ranges overlap, so they should not be read as a contractual total.
Roughly **35–60 active hours shared between student and assistants** could
produce a strong *review-ready package* if the long runs and dataset checks
cooperate. Genuine external use or a detailed mentor letter cannot be bought
with a fixed number of hours. There is no official “Tier 1” admission label
or reliable guarantee of one; the controllable target is a precise,
reproducible contribution with independent criticism and honest authorship.
