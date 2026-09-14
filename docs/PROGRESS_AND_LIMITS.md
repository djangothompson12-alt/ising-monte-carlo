# What this project has done so far

*Working research snapshot, 14 September 2026. This is not a peer-reviewed paper or a validated alloy model.*

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
   regular-solution *mean-field* spinodal. This places the simulated quenches
   on a simple phase diagram; it is not the exact 2D phase boundary or a
   phase diagram for a named commercial alloy.
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
   asymptotic growth law.
5. **Testing the observation method.** Four length observables disagree on
   identical archived lattices. In a controlled image test, 4x pixel binning
   followed by thresholding lowered the fitted slope by about 0.056 at 50:50
   and 0.072 at 15:85 in the original ensemble. The sign and approximate
   size of this effect repeated in four fresh trajectories per composition.
   Cropping behaved less consistently. These transformations change what is
   *observed*, not the simulated dynamics; they do not yield a universal
   correction for microscopy.
6. **Looking for a real-data test.** Five published Al-alloy tomography slices
   were inspected under their source licence. Different image dimensions,
   background levels and incomplete scale information prevent a defensible
   growth-rate comparison at present. No experimental coarsening exponent was
   extracted and no agreement with a real material is claimed.

## What is still unresolved

- The measured slopes below one-third do **not** prove a different asymptotic
  law. Finite time, size, initial length and observable choice have not been
  cleanly separated. The smallest lattice has additional unresolved lengths
  and late-time limitations; larger lattices do not show a one-third plateau
  in the completed window.
- A literature comparison at \(0.6T_c\), 50:50 and \(L=128\) has **7 of 40**
  planned independent runs complete. Its majority-filter/chord observation
  method is separate from the main study and still needs a student check
  against the published method. It is not a reproduction result yet.
- A separate \(0.65T_c\) million-sweep, 16-new-replica-per-condition extension
  has a written plan but has **not started**.
- The model is two-dimensional, binary, nearest-neighbour and defect-free.
  It has no calibrated mapping from sweeps to hours or lattice sites to
  micrometres, and no measured strength or lifetime prediction. Real alloys
  add crystallography, elastic strain, vacancies, 3D connectivity and
  composition-dependent diffusion.

## Where the evidence is

- [Main campaign results](OVERNIGHT_RESULTS.md) — conditions, fitted values,
  uncertainty and failures.
- [Observation study](MEASUREMENT_STUDY_RESULTS.md) — what changed under image
  operations and which comparisons did not repeat.
- [Five-workstream status](FIVE_WORKSTREAMS_STATUS_2026-09-13.md) — completed
  analyses versus plans.
- [Data guide](../research/DATA_README.md) — what raw simulations and summary
  tables are in this repository, and how to rerun the checks.
- [AI assistance and responsibilities](../AI_USE_AND_CONTRIBUTIONS.md) — what
  was assisted and what still needs independent student review.

The best next outside use is a **specific request for technical criticism**:
does the measurement comparison answer a useful question, and what control
would most convincingly separate time, size and measurement effects? No
academic or company has endorsed, adopted or validated this work.
