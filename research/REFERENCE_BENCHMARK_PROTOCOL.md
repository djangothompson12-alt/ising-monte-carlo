# Reference-benchmark pathway

This module prepares a **separate** reproduction pathway for the older
two-dimensional symmetric Kawasaki studies that used a one-pass majority-spin
filter, chord-length distribution and first-zero raw correlation. It does not
change the primary engine, raw snapshots or off-critical connected-correlation
analysis.

Before calling a new result a reproduction, freeze and record:

1. the cited paper/version and every simulation parameter;
2. isotropic coupling, symmetric concentration and temperature convention;
3. the exact majority-filter pass count (one here), applied only after dynamics;
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
