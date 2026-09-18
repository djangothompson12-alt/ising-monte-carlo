# What this project has done so far

*Working research snapshot, updated 18 September 2026. This is not a peer-reviewed paper or a validated alloy model.*

## The question

How much can a measured coarsening exponent change because of the length
measure, the image-processing steps, or the part of a simulation chosen for a
fit? That question grew out of a simpler comparison: domains in the
non-conserved spin-flip model appeared to grow faster than in the
composition-conserving spin-exchange model.

The point is not to make a 2D Ising lattice predict a real alloy's ageing
time. It is to learn which conclusions about phase separation remain reliable
when the measurements are examined more carefully.

## How the work developed

1. **Two working engines.** Model A uses Metropolis single-spin flips; Model B
   uses nearest-neighbour Kawasaki exchanges. Both start from a high-temperature
   state and are quenched below their critical temperature. Model B also allows
   different horizontal and vertical couplings. A Monte Carlo sweep means
   \(L^2\) *attempted* updates, not one accepted move at every site.
2. **A materials interpretation.** For Model B, +1 and -1 can represent the
   two components of an idealised binary mixture. Bond counting gives a
   regular-solution *mean-field* spinodal and binodal. This separates local
   instability from metastability in an approximate phase diagram. A separate
   exact infinite-2D Ising calculation now checks the equilibrium coexistence
   boundary: all six studied isotropic final compositions fall in its two-phase interval.
   That exact boundary is not a spinodal, a finite-time result, or a diagram
   for a named commercial alloy.
3. **A measurement correction.** At off-centre composition, Model B's raw
   spin correlation has a composition-dependent background. Its chosen length
   estimator now uses a normalised connected correlation. Trying to apply the
   same processing to Model A changed its established baseline, because Model
   A's magnetisation itself changes while it orders. The two measurements are
   therefore deliberately different; they must not be compared as though the
   observation pipelines were identical.
4. **Longer, replicated runs.** An isotropic Model B campaign finished 64
   independent trajectories: compositions 50:50 and 15:85, lattice widths
   32, 64, 96 and 128, eight runs per condition, each to 200,000 sweeps at
   \(0.65T_c\). For \(L=64,96,128\), the late-start fitted slopes are about
   0.26 in both compositions. At \(L=128,c=0.5\), changing the start of the
   fit from 2 to 1,000 sweeps changes the fitted value from 0.197 to 0.258.
   These are *effective, finite-window* slopes, not measurements of the
   asymptotic growth law. A later [paired, post-result audit](PAIRED_WINDOW_AUDIT_2026-09-18.md)
   resampled the same eight complete L=128 trajectories in both windows:
   the late-minus-early shifts were +0.061 [0.057, 0.065] and +0.064
   [0.057, 0.071] for 50:50 and 15:85. Those 95% conditional bootstrap
   intervals do not account for choosing the windows after seeing the data.
5. **Testing the observation method.** Four length observables disagree on
   identical archived lattices. In a controlled image test, 4x pixel binning
   followed by thresholding lowered the fitted slope by about 0.056 at 50:50
   and 0.072 at 15:85 in the original ensemble. The sign and approximate
   size of this effect repeated in four fresh trajectories per composition.
   A later fixed test on all 32 new L=128 extension trajectories found
   short-window shifts of −0.056 [−0.059, −0.053] and −0.074
   [−0.077, −0.069], but also changed apparent phase fraction. It was
   specified after the original effect was known, so it is a directional
   new-seed check, not blind discovery. Cropping behaved less consistently.
   These transformations change what is
   *observed*, not the simulated dynamics; they do not yield a universal
   correction for microscopy.
6. **Looking for a real-data test.** Five published Al-alloy tomography slices
   were inspected under their source licence. Different image dimensions,
   background levels and incomplete scale information prevent a defensible
   growth-rate comparison at present. No experimental coarsening exponent was
   extracted and no agreement with a real material is claimed.
7. **Checking a practical image-measurement failure.** A separate AI-assisted
   public annotated-steel test used 42 static micrographs. A simple threshold mask
   overlapped the published phase labels reasonably well but gave a much
   shorter correlation length. Median-filter cleanup reduced the length gap
   while worsening phase-fraction error. This is a caution about measurement,
   not a validation of the Kawasaki kinetics or a lab-ready segmentation tool.
8. **Testing resolution on published masks themselves.** A predeclared
   follow-up started from all 42 producer austenite annotations rather than
   trying to segment the source photographs. At 4× lower resolution, the
   static connected-correlation length increased in every mask (median
   coarse/native ratio 1.050) under the primary tie rule; at 8× the median
   ratio was 1.195. The analysis preserved matched fields and original-pixel
   units. The images may share specimens, and no physical scale or engineering
   tolerance was established. This is a concrete *measurement audit*, not a
   real-alloy ageing experiment or external adoption.
9. **Testing a real ageing-image series, narrowly.** Four published,
   segmented Al–Ge ROI stacks from one specimen were checked at their
   stated 60-nm voxel spacing. A fixed interior 2D length comparison was
   unresolved in seven of eleven planes at 15 minutes and one at 105
   minutes. The two later stages had descriptive median static 4×/native
   length ratios of 1.200 and 1.082, but no experimental growth exponent
   was fitted. The source
   paper separates Ge lamellae from later precipitates; our first
   all-Ge length combines them and cannot be read as precipitate size or
   a hardness predictor. See the [full failure and source audit](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md).
10. **Finishing the longer time-and-size test.** A separate 0.65Tc extension
    completed 16 new trajectories for each of the same eight composition–size
    conditions, to one million attempted-exchange sweeps. At L=128 its broad
    20,000–1,000,000-sweep effective slope was 0.300 [0.291, 0.309] at
    50:50 and 0.281 [0.268, 0.293] at 15:85, using whole-trajectory
    bootstrap intervals. The smallest 15:85 lattice flattened; some
    small 50:50 lengths became unresolved. The nominal 200,000–1,000,000
    fits did not meet the predeclared factor-five time-span rule, so no
    late-window exponent is reported for them. All 80 declared fit rows,
    including failed ones, are in the released
    [neutral appendix](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md).

## What is still unresolved

- The measured slopes do **not** prove either a different asymptotic law or
  convergence to one-third. Finite time, size, initial length and observable
  choice have not been cleanly separated. The smaller 50:50 lattices have
  unresolved late lengths, and the small 15:85 lattice flattens. A broad
  L=128 50:50 fit moving near 0.30 is not a measured one-third plateau;
  its nominal later fit is unresolved. A longer run is a test, not a promise that every
  off-critical effective slope must converge to one-third; different
  conserved models and observables already give differing published results
  (see the [literature comparison](LITERATURE_COMPARISON_2026-09-17.md)).
- The separate \(0.6T_c\), 50:50, \(L=128\) reference campaign completed all
  40 independent trajectories to 4.5 million sweeps. Saved-state and
  energy-accounting checks passed; see the [integrity record](REFERENCE_RUN_INTEGRITY_2026-09-17.md).
  Its majority-filter/chord observation method still needs a student check
  against the published method. The [method crosswalk](MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md)
  identifies known matches and unresolved choices. No fitted exponent or
  reproduction claim is made from this new campaign yet.
- The completed 0.65Tc extension's raw files and derived analysis are in the
  public research snapshot. Its internal raw, observable and table audits are
  not outside review. Student verification of the scientific interpretation
  and a critical external reading are still needed before a paper submission.
- The model is two-dimensional, binary, nearest-neighbour and defect-free.
  It has no calibrated mapping from sweeps to hours or lattice sites to
  micrometres, and no measured strength or lifetime prediction. Real alloys
  add crystallography, elastic strain, vacancies, 3D connectivity and
  composition-dependent diffusion.

## Where the evidence is

- [Main campaign results](OVERNIGHT_RESULTS.md) — conditions, fitted values,
  uncertainty and failures.
- [Completed extension appendix](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md)
  — all five declared windows, both compositions, four widths, missing
  measurements and matched-size coverage in the selected public archive.
- [Mean-field binodal derivation](REGULAR_SOLUTION_BINODAL_2026-09-18.md) —
  common-tangent check and the limits of the materials phase diagram.
- [Exact 2D coexistence check](EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md) —
  established theory benchmark against the approximate diagram, not a kinetic
  or experimental validation.
- [Completed reference-run integrity audit](REFERENCE_RUN_INTEGRITY_2026-09-17.md)
  — what 40 long trajectories passed, and why method-matched analysis is
  still gated.
- [Observation study](MEASUREMENT_STUDY_RESULTS.md) — what changed under image
  operations and which comparisons did not repeat.
- [Paired window audit](PAIRED_WINDOW_AUDIT_2026-09-18.md) — conditional
  whole-trajectory uncertainty for the early-to-late fitting-window shift.
- [Segmented Al–Ge image test](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md) — fixed
  within-image resolution test, unresolved early planes and source-defined
  feature limits, not experimental model validation.
- [Static public-image test](METALDAM_STATIC_PILOT_2026-09-17.md) and
  [cleanup follow-up](METALDAM_CLEANUP_SENSITIVITY_2026-09-17.md) — why the
  threshold-only workflow is not ready for practical phase measurement.
- [Expert-mask resolution audit](METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md)
  — static real-micrograph sensitivity with a predeclared protocol, not a
  growth-law or industrial validation.
- [Historical five-workstream setup](FIVE_WORKSTREAMS_STATUS_2026-09-13.md)
  — what was in place on 13–14 September, not a current campaign count.
- [Data guide](../research/DATA_README.md) — what raw simulations and summary
  tables are in this repository, and how to rerun the checks.
- [AI assistance and responsibilities](../AI_USE_AND_CONTRIBUTIONS.md) — what
  was assisted and what still needs independent student review.

The best next outside use is a **specific request for technical criticism**:
does the measurement comparison answer a useful question, and what control
would most convincingly separate time, size and measurement effects? No
academic or company has endorsed, adopted or validated this work.
