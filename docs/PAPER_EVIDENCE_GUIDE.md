# Your writing and review pack

Start with [the measurement results](MEASUREMENT_STUDY_RESULTS.md), then read
the actual figures and raw tables. This guide organises evidence; it is not
text to submit as an independently written paper.

## A supported central argument

In these finite Kawasaki simulations, the inferred growth rate depends on the
observable and observation pipeline. Controlled image operators can shift an
effective exponent without changing the underlying dynamics. Some shifts repeat
on new trajectories; the smallest-field result is less consistent. A real
experimental image series exposes further comparability problems that must be
resolved before quantitative transfer.

This is a claim about measurement robustness in tested conditions, not a new
growth law, a universal correction or a prediction of alloy properties.

## Figure-to-argument map

| Section | Evidence | What you must explain |
|---|---|---|
| Thermodynamic setting | Existing regular-solution spinodal figure | Mean-field map, conserved composition, why this is not an exact 2D spinodal |
| Simulation verification | Tests and verify_study outputs | Energy, conservation, seeds, limits of these checks |
| Finite time / size | Overnight growth and window figures | Effective vs asymptotic slopes; unresolved L=32 values |
| Observable dependence | Long-run four-estimator figure | Four definitions are not interchangeable particle radii |
| Controlled observation | Operator images and ratio figures | Binning/blur/threshold are observation changes, not dynamics changes |
| Independent repeat | Original/fresh paired results | Different seeds, four fresh replicas, shorter time range |
| Real-material feasibility | Original AlGe slices, histograms and headers | Not registered, background/scale inconsistency, no experimental exponent |
| Discussion | Prior-art comparison and limitations | What was reproduced, what remains untested, who could use the benchmark |

## Methods facts you need to be able to defend

1. Model A is Metropolis single-spin flip; Model B uses conserved Kawasaki
   exchange. The new study primarily concerns Model B, not a new Model A result.
2. Finite-image covariance uses zero-padded axis FFTs and lag-dependent counts
   of valid pairs. Cropped edges never wrap. The observed image mean is estimated.
3. After 4x binning, one pixel represents four original lattice sites. A length
   conversion alone cannot undo lost structure or segmentation bias.
4. Each crop tracks a fixed location; four crops belong to one replica. Explain
   why treating them as independent would overstate evidence.
5. Missing directions produce unresolved means. Fit masks can differ between
   comparisons; quote actual retained times and number of points.
6. The bootstrap resamples whole trajectories. It does not account for every
   source of uncertainty and it is not a test of a physical theory by itself.

Write a short explanation of each yourself before drafting the introduction.
Then reproduce one exact test and one figure. Record which parts you understand
and which need help. Clearly describe AI assistance and your own contribution.

## What remains human / external

- Read the 2011 paper, reconcile its observables and initial-length treatment
  with this study, and decide with a reviewer whether a matched reproduction is
  needed before claiming a publishable contribution.
- Have a microscopist assess the AlGe data-quality findings. The software does
  not replace phase identification, registration or a sound sampling design.
- Approve every source, figure and claim before sharing. Current public prose
  and source manuscript remain drafts; the tracked PDF is stale.
- Seek substantive criticism and revise. Only someone who has actually reviewed
  the work and observed your contribution can decide whether to recommend you.
- Choose a venue only after checking its AI and author-eligibility policies.
  Submission, a DOI and informal review must not be described as peer-review
  acceptance or institutional endorsement.

## Suggested review questions (not sent)

**Coarsening specialist:** Does the study distinguish measurement effects from
finite initial length and finite-size effects adequately? Which published
benchmark should be reproduced before drawing a stronger conclusion?

**Materials microscopist:** Does the proposed finite-window analysis address a
useful measurement problem? What segmentation, specimen masking and metadata
checks are needed before applying it to the AlGe series?

**Dataset author:** The central 195-minute reconstruction has a different image
shape/intensity range, and the current parser did not recover its voxel size.
Could you clarify its reconstruction metadata and whether the volumes are
registered? Is there an existing segmented or registered ROI appropriate for
an educational reproducibility study?

Ask for feedback first. Do not ask someone to certify originality, endorse a
student they do not know, or describe a methods demonstration as industrial
deployment. No messages have been sent by this work.
