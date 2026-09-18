# Independent recomputation of archived Model B measurements

**Read-only AI-assisted audit, 17 September 2026.** This checks internal
calculation and storage consistency. It is not an independent experiment,
external academic review, or evidence that the simulated lengths represent
real alloy features.

The earlier `research.verify_study` check established exact replica inventory,
unique plan-derived seeds and configurations, conserved magnetisation, source
hashes and successive energy intervals. It did **not** recompute the domain
correlations and lengths that
underlie the reported growth exponents. The new
`research/audit_archived_observables.py` does so from each saved spin lattice,
without calling the engine's FFT/correlation or length-extraction functions.
It uses NumPy's independent FFT, a separately written first-crossing routine,
and selected explicit spin-pair products to check FFT normalization and the
x/y axis convention. It also recomputes the interface fraction.

| Completed campaign | Replicas | Snapshots | Directional lengths | Unresolved values, saved/recomputed | Largest absolute correlation difference | Largest absolute length difference |
|---|---:|---:|---:|---:|---:|---:|
| 0.65 Tc main | 64 | 3,840 | 7,680 | 35 / 35 | 8.88×10⁻¹⁶ | 2.84×10⁻¹⁴ |
| Fresh-seed image repeat | 8 | 304 | 608 | 0 / 0 | 2.22×10⁻¹⁶ | 1.33×10⁻¹⁵ |

All checked values agree within a pre-set absolute tolerance of 10⁻¹⁰.
Interface-fraction differences were exactly zero. The largest difference
between selected explicit spin-pair products and reconstructed FFT raw
correlations was 4.44×10⁻¹⁶ for the main campaign. A test deliberately
corrupts a saved length and confirms that the audit fails. The main campaign
manifest SHA-256 is
`398c39d581e15c4f24368ff99f2e12ede790025d9a6f76023e4ad842006adbb7`;
the repeat's is
`7c86317e43b52a43af2160c7432eaf80cd8eb6c86c9eb15813de32a73a2fc1e5`.

## Separate audit of the published growth tables

`research/audit_reported_fits.py` then independently rebuilt the original
analysis arithmetic from the saved trajectory lengths. It checked all **48
finite-window fit rows**, including the fixed `length/L < 0.15` mask, actual
point counts, and 500 whole-replica bootstrap draws, plus all **480
ensemble-length/standard-error rows**. The 64 input files were matched to
their recorded SHA-256 hashes before comparison. The largest absolute
difference in any fitted slope or bootstrap endpoint was 1.67×10⁻¹⁶; ensemble
means and standard errors likewise agreed to floating-point precision. The
saved result is `output/archive_fit_audit_2026-09-17.json`.

This confirms that reported values such as 0.197 and 0.258 were calculated
from the declared archived data and recipe. It does **not** decide that the
chosen fit windows, length/L cutoff, observable, bootstrap interval or 2D
model give an unbiased estimate of the asymptotic growth law.

## First heat interval, checked separately

The original archive verifier compared energy differences **between** saved
states, leaving the first post-quench interval unchecked. A separate read-only
replay now reconstructs each seeded, high-temperature **prepared state** with
the source-hash-matched engine, then computes the whole-lattice Hamiltonian
there and in the first saved post-quench snapshot. Its difference agrees
exactly with the recorded first-interval heat in all **64 main** and **8
fresh-repeat** files. The initial and first saved spin counts also agree.
The source and raw-file hashes are in
`output/first_interval_replay_{overnight,repeat}_2026-09-17_v2.json`; see
`research/replay_first_energy_interval.py` and its corruption test.

This closes a storage/energy-accounting gap; it is **not** an independent
implementation of the Monte Carlo dynamics. The pre-quench preparation is
replayed with the same frozen engine, so a shared dynamics error would remain.

Run from the repository root, writing to **new** output paths:

```bash
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.audit_archived_observables \
  research/runs/overnight --output output/archive_observable_audit_main_new.json
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.audit_archived_observables \
  research/runs/imaging_validation --output output/archive_observable_audit_repeat_new.json
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.audit_reported_fits \
  research/runs/overnight --output output/archive_fit_audit_new.json
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.replay_first_energy_interval \
  research/runs/overnight --source-root research/frozen_sources/2026-09-10 \
  --output output/first_interval_replay_main_new.json
```

The detailed local results of this pass are
`output/archive_observable_audit_overnight_2026-09-17.json` and
`output/archive_observable_audit_repeat_2026-09-17.json`. The script, tests and
this note can be shared with a reviewer, but the student must understand the
normalization and half-height definition before claiming to have checked it.

**What remains untested:** These checks cannot prove that the Monte Carlo
dynamics correctly generated the saved snapshots. They do not test whether the
half-height correlation length is the best observable for droplet-rich
morphologies, distinguish finite time from finite size, establish the
asymptotic one-third law, or calibrate any physical length or ageing time.
