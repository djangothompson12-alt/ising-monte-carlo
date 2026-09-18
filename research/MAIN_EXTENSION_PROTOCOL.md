# Prospective 0.65 Tc main-study extension

Frozen 13 September 2026, before this new campaign is run. This is independent
of the `0.6 Tc` Majumder–Das benchmark and of the previous eight-replica
`0.65 Tc` campaign. The complete plan is
`plans/main_065_multisize_v1.json`: two compositions, four sizes, 16 fresh
replicas per condition, one million sweeps, 80 requested logarithmic samples.
The initial high-temperature equilibration is 200 sweeps, matching the earlier
main study. No source or old NPZ is overwritten.

## Question and decision rule

Is the observed sub-1/3 fitted slope shared across the larger systems as time
increases, or does a smaller lattice depart at matched times? Use the existing
connected-correlation 0.5 crossing as the primary Model B length. Report
directional lengths and unresolved values; do not replace missing values or
silently use a changing subset of replicas. Analysis uses all 16 independent
trajectories as units and separately shows sensitivity to time window.

Predeclared candidate comparison windows: 1,000–20,000, 1,000–200,000,
20,000–200,000, 20,000–1,000,000, and 200,000–1,000,000 sweeps. A fit needs
at least four jointly resolved checkpoints spanning a factor of five in time.
These are finite-window effective exponents, not asymptotic measurements.
At each checkpoint plot length, length/L and local slope by size; compare
sizes at the same sweep counts. A small-size departure alongside continued
growth of larger systems supports a size effect for that comparison. Shared
drift among larger sizes supports finite-time behaviour. Both may occur.
No onset time is assumed from another paper's L=128 trajectory.

The previously used heuristic `length/L < 0.15` is reported as a sensitivity
filter only; the earlier L=32 results show that it is not a guarantee against
size effects. Any quantitative onset criterion must be specified and tested
against all sizes before claiming an onset, including its uncertainty.

## Execution

Run this only after the active 0.6 Tc benchmark stops, to avoid competing
heavy Monte Carlo jobs on the same computer. This is a large, resumable job;
start in bounded blocks and inspect the status and run lock before restarting:

```bash
NUMBA_CACHE_DIR=.numba_cache_campaign MPLCONFIGDIR=.mplconfig \
  .venv311/bin/python -m research.campaign \
  --plan research/plans/main_065_multisize_v1.json \
  --output research/runs/main_065_multisize_v1 --hours 6
```

The runner records source hashes, versions, seeds and configuration; each
completed replica is an immutable NPZ. If the engine or runner changes before
launch, the new run manifest will record the new source identity. Do not edit
either during a resumable campaign. Keep the original campaign untouched.

After all 128 planned replicas are complete, run the dedicated analysis (it
rejects incomplete inventories and applies the declared windows without a
length-fraction cut in the primary fit):

```bash
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.analyse_main_extension \
  research/runs/main_065_multisize_v1 \
  --output research/runs/main_065_multisize_v1/analysis_declared_v1
```

The output includes directional and mean lengths, unresolved counts, fixed
window fits, whole-replica bootstrap intervals, and matched-time size plots.

Presentation-only note, 18 September while the campaign was still running
(114/128 recorded at the last check): `render_extension_appendix.py` was
added to place **all 80** declared fit rows, group missingness counts and
matched-size coverage into a neutral Markdown appendix. It requires the
completed campaign and passing independent raw-to-table audit. It cannot
choose a fit window, infer a finite-size onset or add a new growth estimate;
the underlying CSVs remain the authoritative numerical outputs. This is a
reporting convenience added before final extension results were read, not a
change to the frozen physical analysis.

## Report interpretation

The earlier pilot suggested that short windows and single trajectories were
not sufficient. The eight-replica, 200,000-sweep campaign reduced random
uncertainty and still showed window and estimator dependence. This extension
increases both independent-run count and duration. More replicas improve the
precision of an ensemble mean; they cannot remove estimator, observation,
finite-time or physical-model bias. Report all failures and unresolved fits.
