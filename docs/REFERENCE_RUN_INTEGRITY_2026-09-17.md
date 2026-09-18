# L=128 reference run: completed-data integrity check

*Working, AI-assisted audit note, 17 September 2026. This is not a replication of Majumder and Das (2010), an exponent result, or student-authored paper text.*

The frozen `research/plans/majumder_das_2010_l128.json` campaign finished all **40 of 40 independent seeded trajectories** on 17 September. It used an isotropic 128×128 conserved-spin lattice at `0.6 Tc`, 50:50 composition, and 4.5 million attempted sweeps per trajectory. There are 3,600 saved snapshots. The plan says `T_initial_over_tc=3.0` but `equilibration=0`: the actual start is a random fixed-composition lattice, **not** a thermally equilibrated `3 Tc` sample. State this accurately in any comparison.

## Checks actually run

| Check | Result | What it does not establish |
|---|---|---|
| `research.verify_study` against current source root | 40 distinct seeds; plan configurations, seeds and source hashes match; all magnetisations and later recorded energy intervals pass. | It does not independently implement Kawasaki dynamics or prove physical material validity. |
| `research.audit_archived_observables` | All 3,600 stored snapshots and 7,200 directional lengths recomputed within tolerance `1e-10`; largest absolute correlation difference `6.66e-16`, length difference `7.11e-14`, interface-fraction difference zero. One directional length remained unresolved in both saved and recomputed data. | The checks test saved-value consistency, not whether this length is the best physical observable. |
| `research.replay_first_energy_interval` | 40 seeded preparation replays and independent whole-lattice Hamiltonian checks; largest first-recorded-interval energy difference zero. | With `equilibration=0`, this is principally an initial-state/energy check, **not** an independent trajectory replay. |

Machine-readable records are `output/benchmark_observable_audit_2026-09-17.json` and `output/benchmark_first_interval_replay_2026-09-17.json`. The first stores manifest hash `bea148061be1af4f6f0881b9d6d71a3cb48594a3ca8fab31f284409201325ba1`; the second stores individual raw-file hashes. The original campaign has its own manifest and status file. No file was rejected or removed after looking at an exponent.

## What still needs to happen before a literature comparison

1. The student reads the [2010 paper](https://doi.org/10.1103/PhysRevE.81.050102), then completes `research/reference_benchmark.template.json` with page-specific evidence for the majority filter, chord weighting, correlation definition and initial-length treatment. The template currently has `student_verified=false`; do not mark it true on the student's behalf.
2. Run the frozen comparison analysis with that declaration and inspect its unresolved cases, fit windows and uncertainty over whole trajectories. Do not choose settings because they produce a slope near one-third.
3. Ask a specialist whether the methods are actually comparable. If not, present this as a **40-replica, long-time independent sensitivity study**, not a reproduction.
4. A single 128-site lattice cannot establish the paper's finite-size onset or multi-size scaling collapse. The separate queued `0.65 Tc` extension can test a related question, but its temperature, composition, time range and observables differ.

Recheck all counts and paths from the raw records before putting them in an external report. The integrity checks are reproducible with:

```bash
.venv311/bin/python -m research.verify_study research/runs/majumder_das_2010_l128 --source-root .
.venv311/bin/python -m research.audit_archived_observables research/runs/majumder_das_2010_l128 --output output/benchmark_observable_audit_2026-09-17.json
.venv311/bin/python -m research.replay_first_energy_interval research/runs/majumder_das_2010_l128 --source-root . --output output/benchmark_first_interval_replay_2026-09-17.json
```
