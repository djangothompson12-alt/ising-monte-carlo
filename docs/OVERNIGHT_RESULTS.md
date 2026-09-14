# Completed Kawasaki campaign — 10 September 2026

All **64/64 replicas reached 200,000 sweeps**. The campaign finished at
03:48:38 UTC (04:48:38 UK). At the scheduled completion check, the recorded
process (PID 15620) had exited and its run lock was absent. No replacement
simulation was launched and the six-hour compute budget was not extended.

## What the results show

The three larger lattices give similar effective growth exponents in the
declared late-start window. These remain below 1/3:

| Nominal composition c | L | Effective exponent, nominal 1,000–200,000 sweeps | 95% replica bootstrap interval |
|---|---:|---:|---:|
| 0.50 | 64 | 0.263 | 0.255–0.268 |
| 0.50 | 96 | 0.258 | 0.252–0.263 |
| 0.50 | 128 | 0.258 | 0.253–0.263 |
| 0.15 | 64 | 0.263 | 0.254–0.271 |
| 0.15 | 96 | 0.257 | 0.249–0.263 |
| 0.15 | 128 | 0.260 | 0.252–0.268 |

Each row uses eight independent replicas and 28 retained checkpoints from
1,069 to 200,000 sweeps. The observable is the mean of the two directional
0.5 connected-correlation crossing lengths. Fits are slopes of the logarithm
of the ensemble mean length against log time, not averages of per-replica slopes.

**Fitting-window dependence remains substantial.** At c=0.50, L=128, the
2–200,000 window gives 0.197, the 100–200,000 window gives 0.233, and the
1,000–200,000 window gives 0.258. At the same size and composition, extending
the nominal 1,000–20,000 window to 200,000 sweeps changes 0.236 to 0.258.
The local-slope plots also show drift rather than an established 1/3 plateau.
These fits use overlapping trajectories and are correlated; their difference
is not an independent-replica hypothesis test.

**The smallest lattice has additional late-time problems.** At c=0.15, L=32,
the mean threshold length flattens near four sites and ends at 4.182 sites;
L=96 and 128 end at 5.568 and 5.689 sites. This size-dependent departure is
consistent with finite-size limitation. It occurs despite the small lattice's
maximum ensemble length/L being about 0.134: the protocol's 0.15 cutoff is
not a guarantee against finite-size effects.

At c=0.50, L=32, 35 saved directional length values are unresolved across the
eight replicas. The full-ensemble mean is consequently missing at late times;
the nominal 1,000–200,000 fit actually retains only 19 checkpoints ending at
34,974 sweeps. Its reported 0.247 slope is **not a matched-time comparison**
with the larger lattices above. The abrupt small-lattice local-slope rise must
not be presented as evidence for a new growth regime. No missing lengths were
replaced and no changing subset of replicas was silently averaged.

**The candidate z=3 plots do not demonstrate a successful collapse across
all sizes and times.** The rescaled curves remain separated over much of the
plotted range. Late portions of some larger-size curves approach one another,
but there is no quantitative collapse analysis or demonstrated asymptotic
regime here. No exponent or horizontal shift was tuned to improve overlap.

The defensible interpretation is therefore: the effective exponent is strongly
observation-window dependent, while the smallest system develops additional
size/measurement limitations. Increasing L from 64 to 128 does not move these
late-window fitted exponents to 1/3. These data do **not** establish that the
original sub-1/3 exponent was caused solely by finite size. Shared finite-time
and observable-dependent effects remain plausible; the current analysis does
not uniquely isolate their mechanisms.

The two compositions' late-window slopes are similar over the larger sizes.
This is consistent with, but does not prove, composition-independent
asymptotic growth. Equal finite-window slopes are not a demonstration of
universality, and the amplitudes/morphologies can still differ.

## Dataset, verification and provenance

- Four sizes (32, 64, 96, 128), two nominal compositions (0.50, 0.15), eight
  replicas per group; 3,840 saved lattice snapshots in 64 immutable NPZ files.
- Jx=Jy=1; initial temperature 6.807555942639066, final temperature
  1.4749704542384643; 200 initial equilibration sweeps; plan seed 20260912.
  The requested 64 logarithmic sample points produce 60 unique integer times.
- The realised dilute compositions are 0.150390625, 0.14990234375,
  0.1499565972222222 and 0.1500244140625 for ascending L. This integer-site
  rounding is small but is not hidden by claiming exactly identical fractions.
- Rechecked every raw replica: final checkpoint 200,000; snapshot magnetisation
  constant and equal to the saved value; successive Hamiltonian energy changes
  equal the archived interval energy changes. This does not independently
  recheck the first interval, whose initial lattice is not in the saved series.
- The engine hash still matches the source frozen at launch. The campaign
  runner was subsequently extended for a different benchmark; the exact
  original runner and engine are archived in
  `research/frozen_sources/2026-09-10/` and match the recorded hashes.
  Base commit: `fb717d105af4644bb8bd8e5c64bd5dec1967f3df`, **with uncommitted
  work recorded in the manifest**; the commit alone does not reproduce this run.
- Python 3.11.16, NumPy 2.0.2, SciPy 1.17.1, Numba 0.60.0. Full configuration,
  per-replica seeds, code hashes and initial worktree status are in the archive.
- Campaign manifest SHA-256:
  `398c39d581e15c4f24368ff99f2e12ede790025d9a6f76023e4ad842006adbb7`.
- Primary analysis source SHA-256:
  `0f1923c2818fcbcb3604a3311a013178d53dd04636d40eac752cf3bc87136f2e`.

Analysis command, executed from the repository root:

```bash
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.analyse_campaign research/runs/overnight
```

Outputs are in `research/runs/overnight/analysis/`: `REPORT.md`,
`exponents.csv`, `ensemble_lengths.csv`, `analysis_manifest.json`, and four
figures (`growth_c0.png`, `growth_c1.png`, `exponent_vs_size_c0.png`,
`exponent_vs_size_c1.png`). All four figures were visually inspected. The
analysis manifest contains hashes for all 64 input files. The selected NPZ
archives and these outputs are included in the public working snapshot; keep
a separate backup, and review them independently before any paper submission.

## Limits and next use

Intervals are percentile intervals from 500 whole-replica bootstrap draws,
using a fixed ensemble-derived fit mask. They do not cover mask-selection,
observable or model uncertainty. Eight replicas are still a modest ensemble.
The late-start fit spans a transient as well as the latest observations; it
is an effective exponent, not an asymptotic measurement. The c=0.15, L=64
late local-slope excursion likewise needs replica/morphology inspection rather
than interpretation from the ensemble curve alone.

The materials contribution is a careful study of interpreting microstructure
growth under conservation, not a prediction of an alloy's ageing time or
strength. The calculations remain 2D and uncalibrated to physical units.

Next, apply the already documented exploratory four-observable comparison to
this completed dataset, then decide whether a targeted measurement/temperature
control or longer large-lattice runs is most informative. That secondary
comparison has **not** been executed in this scheduled primary-analysis pass.
No further simulation is started here. The [research design](../research/STUDY_DESIGN.md)
sets out the choices and their limitations.

This summary and the analysis were prepared by the coding assistant and await
independent student review. At the time of the original report nothing had
been emailed or published as a paper. The selected raw archives and summaries
are now part of a public working-code snapshot; that does not amount to peer
review or independent experimental validation. There is no continuing
unattended computation.
