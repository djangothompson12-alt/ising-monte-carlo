# External-review packet

This repository is a pre-university research project on how conservation of
composition and the choice of measurement affect reported phase-ordering
kinetics in a two-dimensional Ising model.
It implements non-conserved Metropolis single-spin-flip dynamics (Model A) and
conserved nearest-neighbour spin exchange (Model B/Kawasaki dynamics). The
work is intended as a controlled model study, not a quantitatively predictive
simulation of a specific commercial alloy.

## One-sentence research question

When a finite Kawasaki simulation appears to coarsen more slowly than the
expected late-time one-third law, how much of that result depends on the
time window, lattice size and definition of domain length?

## What is independently checkable

- The completed 0.65Tc campaign has 64 seeded raw trajectories in this
  snapshot: two compositions, four lattice sizes and eight runs per
  condition, each to 200,000 sweeps. The run manifest, code hashes,
  summaries and analysis scripts are included; see
  [the data guide](research/DATA_README.md).
- At the three larger sizes the selected late-start fits are around 0.26,
  but the fitted value moves when the window changes. A separate observation
  test shows that binning and thresholding can shift a fitted exponent on
  unchanged trajectories, with a small fresh-seed repeat. These facts do not
  identify a unique mechanism for the one-third shortfall.
- Deterministic automated tests check detailed energy bookkeeping, exact
  Kawasaki composition conservation, the anisotropic critical temperature,
  periodic component labelling, the normalized LSW distribution, and the
  Ising-to-regular-solution mapping.
- Model A intentionally keeps a raw-correlation length; Model B uses a
  normalized connected-correlation length for the off-critical study.
  Connected correlations are mathematically possible in Model A too, but
  would define a different observable and changed its established baseline.

## Questions for a technical reviewer

1. Is the Ising-to-regular-solution mapping and spinodal interpretation stated
   with the right mean-field caveats?
2. Is the connected-correlation threshold a useful length measure in both
   interconnected and droplet-rich structures? Which second observable
   would make the comparison more convincing?
3. Which finite-time or finite-size control should be run next to tell
   whether the approximately 0.26 effective slope is still drifting?
4. Are the controlled image operations relevant to a practical
   microstructure-measurement problem, and what metadata or segmentation
   checks are missing before trying this on a real alloy series?
5. Which claim in this snapshot is least supported by the evidence?

## Scope boundary

The lattice is two-dimensional, binary, nearest-neighbour, defect-free, and
uses Monte Carlo sweeps as algorithmic time. It omits elastic strain,
composition-dependent mobility, crystallography, vacancies, multicomponent
thermodynamics, and three-dimensional topology. The appropriate external use
today is reproducible teaching, methodological review, or a benchmark for
coarsening analysis—not industrial alloy qualification or process prediction.

The separate 0.6Tc literature benchmark is only 7/40 planned runs complete,
and the longer 0.65Tc extension has not started. No comparison from either is
presented as a finding. The manuscript is a working draft, not the review
packet's definitive account. No endorsement, recommendation letter or code
adoption is being requested. Please ask before naming any reviewer publicly.

Development has included substantial AI assistance, including execution of
numerical tests and new campaigns. See AI_USE_AND_CONTRIBUTIONS.md. The one-page
brief in docs/review_brief.html is a working draft for student verification.
