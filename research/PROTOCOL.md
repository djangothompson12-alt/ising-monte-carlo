# Finite-time and finite-size study

Prospective plan created 10 September 2026. This tests an explanation; it does
not start from the conclusion that finite size causes the exponent below 1/3.

The primary question is whether effective growth exponents change with time,
lattice size, or both. Use unchanged Model B Kawasaki kernels, Jx=Jy=1,
c=0.50 and 0.15, and the engine's default temperatures (recorded in each NPZ).
Initial composition is rounded to an integer spin count and then exactly
conserved; the realised value is saved. Model A is not altered.

## Campaigns

| Plan | L | Independent replicas per c,L | Sweeps | Purpose |
|---|---|---|---|---|
| smoke | 16,24 | 2 | 100 | Execution/restart check only |
| pilot | 32,64,96 | 4 | 20,000 | Runtime and estimator diagnostics |
| overnight | 32,64,96,128 | 8 | 200,000 | Longer, larger replication |

```bash
NUMBA_CACHE_DIR=.numba_cache_campaign MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.campaign --plan research/plans/overnight.json --output research/runs/overnight --hours 6
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.analyse_campaign research/runs/overnight
```

The runner saves each completed replica atomically. It checks magnetisation at
every checkpoint and saves raw directional connected correlations, lengths,
lattice snapshots, interval energy changes, interface fractions, seeds and
configuration. A manifest records source hashes and package versions. An
interrupted replica restarts from its seed; this is not a checkpoint of the
Numba random-number generator. Completed replicas are not rerun. Resume with
the identical plan, code and environment, or choose a new directory.

The six-hour budget is a cap, not a promise to keep a sleeping computer running.
Inspect status.json and the process before removing any stale RUNNING.lock.
Avoid simultaneous writers to the same run directory. New output in
`research/runs/` is ignored by default; the selected completed archives in
the working public snapshot were deliberately tracked. Back up all runs
separately, including ones not tracked by Git.

## Analysis fixed before the long campaign

Use ℓ=(ℓx+ℓy)/2 from the same 0.5 correlation threshold as the original study.
Plot mean trajectories with standard errors across whole replicas. Do not
replace unresolved lengths or average over a changing subset silently.

Compare shared windows beginning at 2, 100 and 1,000 sweeps, ending at 20,000
and the final time where available. The earliest window is a legacy sensitivity
check, not a late-stage fit. Restrict fits to ensemble ℓ/L<0.15; require four
points spanning at least a factor of five in time. This cutoff is a heuristic,
not proof that finite-size effects vanish. Inspect correlations and interfaces
before treating a fitted exponent as meaningful.

Resample whole replica trajectories 500 times for percentile intervals. Do not
bootstrap time points as independent measurements. The fit mask is fixed from
the ensemble; its selection uncertainty is not included. Intervals from four
replicas are exploratory. Different fitted windows are correlated.

The ℓ/L versus t/L³ panel tests a proposed dynamic exponent z=3 without tuning
horizontal shifts or fitting z. Visual overlap alone is not a scaling-collapse
demonstration, especially before saturation. Report where curves fail to agree.
Compare matched times across sizes and matched sizes across time. A shared
time drift among large sizes supports finite-time corrections; a size-dependent
deviation at matched times supports finite-size effects. Either can coexist
with observable-dependent, composition-dependent or temperature-dependent
transients. More sizes/runs may be needed; do not prewrite the conclusion.

## Pilot observation, not a new established result

All 24 pilot replicas completed. At c=0.5, the 2–20,000-sweep slopes are about
0.17 across L=32,64,96; the 1,000–20,000-sweep slopes are about 0.24 across
those sizes. This makes the fitting window important. It does not establish
1/3, or show that finite size explains the original value. See the generated
`research/runs/pilot/analysis/REPORT.md` and underlying NPZ files. Do not quote
these rounded numbers without retaining that provenance.
