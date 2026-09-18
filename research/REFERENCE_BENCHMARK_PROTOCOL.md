# Reference-benchmark pathway

This module prepares a **separate** comparison pathway for older
two-dimensional symmetric Kawasaki studies that used majority-spin filtering,
chord-length distributions and correlation diagnostics. Our post-processing
implementation uses **one simultaneous filter pass**; the precise pass
schedule in the cited papers has not been established as identical. It does not
change the primary engine, raw snapshots or off-critical connected-correlation
analysis.

Before calling a new result a reproduction, freeze and record:

1. the cited paper/version and every simulation parameter;
2. isotropic coupling, symmetric concentration and temperature convention;
3. the majority-filter pass count (one here), applied only after dynamics,
   and whether that choice actually matches the paper;
4. the chord, correlation and spectrum definitions; and
5. replica count, time range, random-seed plan and all failed/unresolved cases.

The post-processing filter can change the apparent composition and morphology.
It must never be passed back into Kawasaki evolution, and it is not a default
for the main `c=0.15` analysis. Agreement or disagreement with a published
curve needs discussion with a technical reviewer before it is treated as a
new result.

## Predeclared L=128 reference campaign

`plans/majumder_das_2010_l128.json` is a separate benchmark plan for the
L=128, symmetric, isotropic case reported by Majumder and Das, *Physical
Review E* **81**, 050102(R) (2010), DOI: 10.1103/PhysRevE.81.050102. It fixes
40 independent random starts, a direct quench to `0.6 Tc`, and 4.5 million
post-quench sweeps. The count and time scale match their reported L=128
conditions; the implementation, random-number generator, checkpoint schedule,
and analysis remain independent.

**17 September status:** all 40 raw trajectories completed. A separate
[integrity audit](../docs/REFERENCE_RUN_INTEGRITY_2026-09-17.md) verifies stored
states and observables. The paper-method declaration remains unverified and
no comparison exponent or reproduction claim has been released. The plan has
`equilibration=0`, so its random fixed-composition initial states must not be
described as equilibrated at the listed `T_initial_over_tc` value.
The [source-to-code crosswalk](../docs/MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md)
sets out which choices are documented in the paper and which remain uncertain;
it is not a substitute for the student's gated declaration.

It deliberately contains **only L=128**. It can compare a long symmetric
trajectory ensemble and its measurement convention, but cannot reproduce the
paper's multi-size finite-size scaling claim by itself. The plan must not be
changed, selectively filtered or extended in response to a fitted exponent.

Run it resumably in bounded wall-time blocks while the machine remains awake:

```bash
NUMBA_CACHE_DIR=.numba_cache_campaign MPLCONFIGDIR=.mplconfig \
  .venv311/bin/python -m research.campaign \
  --plan research/plans/majumder_das_2010_l128.json \
  --output research/runs/majumder_das_2010_l128 --hours 6
```

Each completed replica is retained atomically. Re-run the identical command to
continue after a planned stop; do not edit the plan or remove a lock without
first inspecting the recorded status.
