# Research review snapshot

This snapshot brings together the current Ising/Kawasaki measurement study for
technical criticism. It was selected for public sharing on 4 October 2026.
The documents are AI-assisted working drafts, not a completed student-approved
paper, peer review or laboratory endorsement.

## Start here

1. [Two-page brief](review_brief.pdf): the question, main result and limitations.
2. [Full short brief](../docs/ACADEMIC_REVIEW_BRIEF_2026-09-20.md): supporting context
   and three questions for a reviewer.
3. [Scope and closest literature](../docs/RESEARCH_SCOPE_2026-09-26.md): what is
   being tested, what is already known, and what would be an overclaim.
4. [Portable evidence ZIP](focused_review_evidence_2026-10-01_v2.zip): 16 raw
   primary trajectories, analysis tables, selected source dependencies,
   reproduction instructions, hashes and aggregate context. Download and unzip
   it to inspect the included README and CONTEXT documents.

The archive and PDF are unchanged copies of the 1 October evidence package.
Their historical wording says they had not yet been published or delivered;
this page records the later decision to share them as research drafts. It does
not change the recorded data, provenance, student-review status or results.
The archive is deliberately narrower than the whole repository. Its campaign
manifest omits a private Git-status field; the redaction record explains the
hash difference without changing the simulation identity.

## The question and result

After reducing image resolution, is matching the native species-site fraction
sufficient to preserve the fitted finite-window coarsening exponent?

The fresh experiment uses 16 independent L=128 trajectories, eight at each of
two compositions, with isotropic couplings and T=0.65 Tc. In the declared
fourfold-reduction, half-height comparison, native and fraction-matched fits
are 0.23141 versus 0.18094 at 50:50 and 0.24214 versus 0.16563 at 15:85.
These are fits over 1,119–20,000 sweeps, not asymptotic exponents.
The paired uncertainty, rounding residual and sensitivity choices are in the brief.

Matching fraction did not recover the native fit in this comparison. That
does not prove a different growth law, explain every cause of the original
native shortfall, or show that fraction matching always fails. The native
length is itself an operational reference, not a unique true domain radius.

## What to challenge

- Does the paired design and whole-trajectory uncertainty support the stated,
  bounded conclusion? Check finite-image versus periodic lengths and severe
  under-resolution, rather than treating every length as interchangeable.
- Do the interpretation and novelty claims stay within the closest literature?
  A bounded literature search cannot establish that no similar study exists.
- Could the static mask audit help a real imaging decision, and what validation
  is missing? Real phase area fraction is not generally elemental composition.

Preserve the negative and corrective evidence: the two warning screens accepted
zero of 18 comparisons, and the direct arithmetic audit found 37 secondary
factor-eight discrepancies affecting four fits. The primary factor-four result
was unchanged. See [calculation audit](../docs/CALCULATION_AUDIT_2026-09-20.md).
The [chord comparison](../docs/CHORD_OBSERVATION_RESULTS_2026-09-26.md) is
exploratory and includes smaller or opposite-direction effects; do not select
only findings that make processing look important.

## Reproduction and boundaries

From the repository root, install `requirements.txt` in a Python 3.11 virtual
environment and run `python -m unittest discover -s tests -v`. For the smaller
primary-result replay, follow the numerical-only instructions inside the ZIP.
The recorded replay was local; a fresh-machine reproduction is not claimed.

Both simulation engines and visualisers are included in the repository. The
[data guide](../research/DATA_README.md) describes the larger campaigns.
Some applied audits require separately obtained source images; those originals
and private planning/outreach/essay notes are intentionally not redistributed.
The older `manuscript/main.pdf` is stale and must not be cited as the current paper.

Please distinguish code review, numerical reproduction, physical validation and
outside usefulness. An AI review is not independent academic endorsement.
[AI assistance and contributions](../AI_USE_AND_CONTRIBUTIONS.md) remain explicit.
