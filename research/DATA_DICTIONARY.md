# Research data dictionary

*AI-assisted reference for checking the archived data, 18 September 2026.
This is a description of files, not a claim that any model predicts an alloy.*

## The independent unit and the two coordinate systems

One `c{index}_L{width}_rep{number}.npz` file is **one independently seeded
Monte Carlo trajectory** at a specified nominal composition and lattice
width. Saved times and image crops within it are repeated observations of
that trajectory, not extra replicas. A sweep is `L²` attempted neighbour
exchanges; it is not a measured second. In the engine, distances are in
lattice sites with **periodic** boundaries. In the separate applied-image
analysis, distances are in pixels or explicitly supplied physical units and
image edges **do not wrap**. Their correlation lengths are not the same
observable simply because both use a half-height crossing.

The completed public main study has 64 files (`research/runs/overnight/`):
four widths, two nominal compositions, eight replicas each. The fresh
observation repeat has eight more files (`research/runs/imaging_validation/`),
four per composition at width 128. The 40-run 0.6 Tc literature-reference
archive is complete **locally but not Git-tracked**. The 0.65 Tc extension is
still running as of this note; use its live `status.json`, not this paragraph,
for the count. Do not combine the campaigns as though they share temperature,
length method, duration or sampling grid.

## Fields in a raw NPZ trajectory

The fields below were inspected in `research/runs/overnight/c0_L128_rep000.npz`
and are written by `research/campaign.py` using the Model B engine. Dimensions
below use `K` saved checkpoints and lattice width `L`.

| Field | Shape/type | Meaning and units |
|---|---|---|
| `t` | `(K,)`, integer | Cumulative sweeps after the temperature quench. The requested number of log-spaced samples can contain duplicate integer times; the stored array contains unique times. |
| `snapshots` | `(K,L,L)`, signed 8-bit integer | Saved ±1 lattice states. The +1 count, and hence realised composition, is exactly conserved by Kawasaki exchange. Coordinates are periodic in the simulation. |
| `magnetization` | scalar integer | Sum of spins, fixed for this replica. Divide by `L²` for magnetisation per site; `(1+magnetization/L²)/2` is the realised +1 fraction. |
| `realized_concentration` | scalar float | The realised +1 fraction after integer-site rounding of the requested composition. Do not silently relabel it as the exact nominal fraction. |
| `correlations` | `(K,2,L//2+1)`, float | Periodic directional spin correlations, horizontal then vertical. Model B's off-critical output is normalised and connected under its constant magnetisation. See the engine and its exact tests for the convention; do not substitute Model A's raw correlation. |
| `lengths` | `(K,2)`, float | Linearly interpolated first 0.5 crossing of those two correlations, in lattice sites. A missing crossing is `NaN`, not zero or half the box. Their mean is the primary domain-length proxy. |
| `delta_energy` | `(K,)`, float | Sum of accepted energy changes **between the previous and this checkpoint**, in the Hamiltonian's reduced energy units for the whole lattice. It is not energy per site, a direct free-energy difference, or entropy production. |
| `interfaces` | `(K,)`, float | Fraction of unlike nearest-neighbour bonds, counting horizontal and vertical bonds once each, divided by `2L²`. It is a morphology proxy, not a measured interfacial energy. |
| `config` | scalar JSON string | Actual per-replica run configuration, including seed, couplings, requested composition, temperatures, equilibration and final sweep. |

`manifest.json` freezes the plan, source-file SHA-256 hashes, Python and
numerical-library versions, base commit and initial worktree state. The
manifest's **identity** is checked on resume. `status.json` is a transient
progress record. Completed NPZ files are written through a temporary file
and then moved into place; a timed-out in-progress replica is restarted from
its seed rather than resumed from a hidden RNG state. `RUNNING.lock` should
never be removed without checking the recorded process.

## Main derived files

| File | Interpretation | Important qualification |
|---|---|---|
| `overnight/analysis/ensemble_lengths.csv` | Mean directional-average length and replica standard error at each saved time for each composition/width. | `n` is the number of trajectories, not pixels or snapshots. Any unresolved direction makes that trajectory's mean missing; the analysis does not silently use a changing subset. |
| `overnight/analysis/exponents.csv` | Log–log slope of the **ensemble mean** length in stated nominal windows, with 500 whole-trajectory bootstrap percentiles. | It is an effective finite-window exponent. Different windows reuse the same trajectories. `n_points` and actual first/last retained times need checking before comparing rows, particularly `L=32`. |
| `overnight/estimator_analysis_v1/paired_fits.csv` | Four defined observables measured on the same saved lattice sequence. | They are not four interchangeable physical radii. Paired intervals resample trajectories, not timepoints. |
| `{overnight,imaging_validation}/imaging_v1/paired_fits.csv` | Treatment-minus-reference image-length slopes over matched checkpoints inside each ensemble. | The finite-image estimator and observation operators differ from the engine estimator. `bin4` includes block averaging **and** re-thresholding. The two ensembles have different time grids and replica counts. |
| `overnight/analysis/analysis_manifest.json` and corresponding later manifests | Analysis-source and input-file hashes. | A hash proves which bytes were analysed, not whether a scientific interpretation is correct. |

## Minimal checks before quoting a number

1. Identify the campaign, temperature, nominal and realised composition,
   lattice width, independent-replica count and the actual retained times.
2. Name the length definition, boundary convention, observation treatment
   and whether a missing direction excluded a checkpoint.
3. State whether the displayed uncertainty is standard error, a
   whole-replica bootstrap interval or spread across method choices. They
   answer different questions.
4. Verify raw data/source hashes with `research.verify_study` and inspect
   the relevant figure and table. Internal checks are not outside validation.

For run and verification commands, see [the data guide](DATA_README.md) and
[the prospective protocol](PROTOCOL.md). The 40-run literature comparator
requires the separate [method crosswalk](../docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md)
before it can be described as a reproduction.
