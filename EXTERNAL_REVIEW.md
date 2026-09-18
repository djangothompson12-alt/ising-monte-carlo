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

- The first completed 0.65Tc campaign has 64 seeded raw trajectories in the
  public working snapshot: two compositions, four lattice sizes and eight runs per
  condition, each to 200,000 sweeps. The run manifest, code hashes,
  summaries and analysis scripts are included. The archive verification check
  confirms 64 unique seeds, 3,840 snapshots, matching frozen source hashes,
  exact composition conservation and later recorded energy intervals. A
  separate seeded-preparation replay checks the first recorded energy interval
  for all 64 main and eight repeat runs; it reuses the same engine and is not
  an independent dynamics implementation. See
  [the data guide](research/DATA_README.md).
- At the three larger sizes the selected late-start fits are around 0.26,
  but the fitted value moves when the window changes. A separate observation
  test shows that binning and thresholding can shift a fitted exponent on
  unchanged trajectories, with a small fresh-seed repeat. These facts do not
  identify a unique mechanism for the one-third shortfall.
- A separate **completed extension** has 128 new trajectories: 16 per
  composition–size condition to 1,000,000 sweeps at 0.65Tc. Its frozen
  five-window analysis reports every fit, including unresolved ones. At
  `L=128`, the broad 20,000–1,000,000-sweep effective slopes are 0.300
  [0.291, 0.309] at 50:50 and 0.281 [0.268, 0.293] at 15:85 (95% whole-
  trajectory bootstrap intervals). The nominal 200,000–1,000,000-sweep
  fits are **unresolved** under the declared factor-five time-span rule.
  The small 15:85 lattice flattens; some small 50:50 lengths become
  unmeasurable. This supports time-window and size sensitivity, not a
  unique finite-size onset or a demonstrated asymptotic one-third law. The
  [all-row appendix](research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md)
  and 128 raw files are included in this public research snapshot.
- A fixed **new-seed image-operation holdout** used all 32 extension
  `L=128` trajectories. Fourfold block averaging then thresholding shifted
  the 1,000–20,000-sweep fitted slope by −0.056 [−0.059, −0.053] at 50:50
  and −0.074 [−0.077, −0.069] at 15:85. It also changed the apparent +1
  fraction by +0.0214 and −0.0211 respectively. This repeats a direction
  observed before the holdout on fresh seeds, but it is not blind external
  confirmation, an image-instrument model, or a universal correction.
- A [paired post-result audit](docs/PAIRED_WINDOW_AUDIT_2026-09-18.md)
  resamples the same eight L=128 trajectories in both fitting windows. The
  late-minus-early shift is +0.061 [0.057, 0.065] at 50:50 and +0.064
  [0.057, 0.071] at 15:85 (95% conditional whole-run bootstrap). This
  supports a reproducible *window effect* in the archived data, not a
  chosen asymptotic window or a new physical law.
- A post-hoc [stage analysis](docs/BINNING_DECOMPOSITION_RESULTS_2026-09-17.md)
  separates the averaging and threshold steps of that image operation. Their
  relative contributions change with composition and fit window; this is a
  measurement-pipeline observation, not a universal correction.
- Deterministic automated tests check detailed energy bookkeeping, exact
  Kawasaki composition conservation, the anisotropic critical temperature,
  periodic component labelling, the normalized LSW distribution, and the
  Ising-to-regular-solution mapping. An exhaustive nearest-neighbour test on
  several small anisotropic lattices checks the local exchange energy change
  against the full Hamiltonian, including bonds across periodic seams. A
  separate exact 3×3, fixed-composition transition-matrix test enumerates all
  126 states and confirms the expected Boltzmann weights satisfy detailed
  balance and stationarity for the one-attempt exchange rule. Neither test
  establishes a large-lattice growth exponent. An actual three-seed sampler
  check on that sector gave mean energy −2.7314 against exact −2.7339;
  [its limitations are recorded separately](docs/SMALL_LATTICE_EQUILIBRIUM_CHECK_2026-09-17.md).
- A separate read-only audit recomputed all 8,288 archived directional
  correlation lengths directly from saved lattice snapshots, including all
  unresolved values; see
  [the observable audit](docs/ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md).
  It also independently reproduced the 48 reported growth fits and 480
  ensemble-mean rows from hash-matched raw trajectories. This is internal
  numerical verification, not external validation.
- The extension's internal checks include all 128 raw file/seed/source
  inventories, 9,600 snapshots and 19,200 archived directional lengths,
  all 80 declared fit rows, 450 matched-size rows, and first-interval energy
  replay. One correlation-threshold decision is ambiguous at approximately
  2×10⁻¹⁶ FFT roundoff; the audit counts it rather than altering the frozen
  engine or saved length. These are computational checks, not outside review.
- Model A intentionally keeps a raw-correlation length; Model B uses a
  normalized connected-correlation length for the off-critical study.
  Connected correlations are mathematically possible in Model A too, but
  would define a different observable and changed its established baseline.
- The regular-solution binodal and spinodal are checked against the
  [exact infinite-2D Ising coexistence boundary](docs/EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md).
  All six studied isotropic final compositions lie in its equilibrium two-phase interval;
  this does not supply an exact spinodal or identify their kinetic pathway.
- A separate [real-mask resolution audit](docs/METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md)
  used all 42 published MetalDAM austenite annotations. At 4× coarser
  resolution, its static correlation length increased in all 42 masks
  (median ratio 1.050), using matched fields and original-pixel units.
  This is a descriptive image-measurement result, not a Kawasaki or
  real-alloy ageing validation.
- A [bounded test on public segmented Al–Ge ageing stacks](docs/ALGE_REAL_IMAGE_AUDIT_2026-09-18.md)
  moved the exact 4× image operation onto a **real solid-state alloy**.
  The predeclared interior-region test could not resolve all chosen planes
  at the two earlier stages; at 195 and 315 minutes it produced descriptive
  static length ratios. The source authors already studied 3D feature
  evolution, the four stacks come from one specimen, and this is not a
  test of simulation kinetics or external adoption.
- A separate [local mask-resolution audit](docs/MASK_RESOLUTION_AUDIT.md)
  accepts a researcher-supplied binary phase mask and declared physical pixel
  size. It records native, 2× and 4× correlation lengths and unresolved cases
  without attempting raw-image segmentation or fitting a growth exponent.
  The HTML exposes time and length units, and the output records input
  settings and hashes without embedding mask pixels. A [pilot-record
  template](docs/MASK_AUDIT_PILOT_RECORD.template.md) asks an image owner to
  define the useful decision before seeing a result. A deterministic
  [synthetic demo](research/make_mask_resolution_demo.py) shows both resolved
  and unresolved output without any real image. Synthetic tests pass,
  but no researcher has used or validated this workflow.

## Questions for a technical reviewer

1. Does the separation between the exact 2D coexistence result and the
   **mean-field-only** spinodal make sense? What thermodynamic language in
   the report risks overinterpreting the dilute quenches?
2. Is the connected-correlation threshold a useful length measure in both
   interconnected and droplet-rich structures? Which second observable
   would make the comparison more convincing?
3. Given the full five-window extension, what additional observable or
   independent analysis would best distinguish initial-length effects,
   genuine finite-size influence and continued time-window drift without
   declaring a finite-size onset from a single threshold?
4. In the Al–Ge failure case, which feature and region would a materials
   microscopist actually measure? The published analysis separates Ge
   lamellae from precipitates, whereas our present length combines them.
   Is a 2D population-specific resolution audit useful at all, or should
   the pilot stop in favour of the source paper's 3D feature measures?
   What registration and independent-specimen checks would be needed?
5. Which claim in this snapshot is least supported by the evidence?
6. How far is it scientifically fair to compare this Kawasaki model with the
   [composition-dependent 2D Cahn–Hilliard result of König et al. (2021)](https://doi.org/10.1039/D1CP03229A),
   given different kinetics, initial-length treatment and observables?

## Scope boundary

The lattice is two-dimensional, binary, nearest-neighbour, defect-free, and
uses Monte Carlo sweeps as algorithmic time. It omits elastic strain,
composition-dependent mobility, crystallography, vacancies, multicomponent
thermodynamics, and three-dimensional topology. The appropriate external use
today is reproducible teaching, methodological review, or a benchmark for
coarsening analysis—not industrial alloy qualification or process prediction.

The separate 0.6Tc L=128 campaign has completed **40 raw trajectories** and
passed internal integrity checks, but no student-approved paper-method fit
or reproduction claim has been released; see the
[method crosswalk](docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md).
The 0.65Tc extension and its fixed image holdout are complete and released
as research data. The [working report](manuscript/REPORT_DRAFT_2026-09-18.md) is
AI-assisted and still needs student rewriting and checking. A private,
hash-checked review copy is available for **technical criticism** alongside
the selected public data. No endorsement, recommendation letter or code
adoption is being requested. Please ask before naming any reviewer publicly.

Development has included substantial AI assistance, including execution of
numerical tests and new campaigns. See AI_USE_AND_CONTRIBUTIONS.md. The one-page
brief in docs/review_brief.html is a working draft for student verification.
If feedback arrives, record the actual criticism, response and permission
to name or quote the reviewer in the private
[response-log template](docs/REVIEW_RESPONSE_LOG.template.md). An affiliation
alone is not endorsement.
