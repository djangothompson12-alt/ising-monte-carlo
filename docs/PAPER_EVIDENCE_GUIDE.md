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
| Thermodynamic setting | Regular-solution diagram plus exact-2D coexistence check | Mean-field binodal/spinodal versus exact coexistence; why neither is a real alloy diagram |
| Simulation verification | Tests and verify_study outputs | Energy, conservation, seeds, limits of these checks |
| Morphology | [Fixed-selection snapshots](../figures/fig_archived_morphology_v1.png) | Why a 50:50 network and 15:85 patches look different; why one run is only illustrative |
| Finite time / size | [Core window figure](../figures/fig_core_window_sensitivity_v1.png), [paired-window check](PAIRED_WINDOW_AUDIT_2026-09-18.md) and complete growth table | Effective vs asymptotic slopes; same-run paired uncertainty; unresolved L=32 values |
| Observable dependence | Long-run four-estimator figure | Four definitions are not interchangeable particle radii |
| Controlled observation | [Core paired-shift figure](../figures/fig_core_observation_shift_v1.png) and operator images | Binning/blur/threshold are observation changes, not dynamics changes; the image length is not the periodic engine length |
| Independent repeat | Original/fresh paired results | Different seeds, four fresh replicas, shorter time range |
| Known-input challenge | [Geometric control](SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md) | Its imposed one-third growth does not explain the Kawasaki shortfall or establish a universal imaging bias |
| Earlier real-material feasibility | Five selected AlGe slices from a different Zenodo release | Not registered, background/scale inconsistency, no experimental exponent |
| Fixed real-image observation test | [Four public segmented Al–Ge ROI stacks](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md) and [44-row table](../research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv) | Why early central regions have no Ge, why unresolved measurements stay in the result, and why late-stage static length ratios are not an ageing exponent |
| Static experimental-mask audit | [All 42 published steel masks](METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md) | Pixel-unit resolution sensitivity; no independent-specimen claim or alloy-ageing kinetics |
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
- Read the [2013 Majumder–Das composition study](https://doi.org/10.1039/C3CP50612F)
  and the [source comparison](LITERATURE_COMPARISON_2026-09-17.md). Composition
  dependence and off-critical droplets are established prior work, not this
  project's novelty by themselves.
- Read the relevant results of [König et al. (2021)](https://doi.org/10.1039/D1CP03229A),
  which finds off-critical sub-one-third fitted values in a different 2D
  Cahn–Hilliard model. Identify its length definition and initial-time/length
  fit before deciding what, if anything, your Kawasaki result can be compared
  with.
- Have a microscopist assess both AlGe data-quality findings and the newer
  Al–Ge central-ROI failure. The software does not replace phase
  identification, registration or a sound sampling design.
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

**Dataset author or imaging specialist:** In Fell's segmented Al–Ge ROI
stacks, the four TIFFs have different x/y extents; a fixed central 18-µm
square contains no Ge on seven of eleven chosen early planes. Is the TIFF
page order physically increasing z, and are features registered across
stages? Since the published method separates lamellae from precipitates,
is our combined all-Ge 2D correlation length useful for *any* decision,
or should a pilot use a population-specific 3D measure and specimen region?

Ask for feedback first. Do not ask someone to certify originality, endorse a
student they do not know, or describe a methods demonstration as industrial
deployment. No messages have been sent by this work.
