# Data included in the repository

The main evidence is a set of seeded Model B simulations, not a measured
alloy time series. Files are under `research/runs/`; most new run output is
ignored by Git, but the selected completed campaigns listed below are tracked
as a public snapshot.

| Folder | What it contains | Status |
|---|---|---|
| `runs/overnight/` | 64 raw NPZ trajectories, plan/manifest/status, growth summaries, estimator and image-operation analyses | Complete to 200,000 sweeps |
| `runs/imaging_validation/` | Eight fresh raw NPZ trajectories and image-operation repeat | Complete to 20,000 sweeps |
| `runs/pilot/` | Earlier 24-replica exploratory campaign and summaries | Pilot; not an independent confirmation |
| `runs/measurement_reliability_map_v1/` | Compact comparison of original and fresh image-operation results | Exploratory |

The main comparison used `Jx=Jy=1`, `T_final=0.65Tc`, compositions 0.50 and
0.15, widths 32/64/96/128 and eight independent runs per condition. The
fresh observation repeat used different seeds at width 128, four runs per
composition. Exact integer compositions, seeds, code hashes and dependency
versions are in each campaign manifest. NPZ files include archived times,
lattice snapshots, directional lengths, energies and magnetisation.

The incomplete 0.6Tc literature benchmark (7/40 planned runs at this
snapshot), the planned million-sweep extension, the third-party Al-alloy
images, and large duplicate evidence ZIPs are **not** included as completed
public datasets. No physical tennis-string measurements exist yet.

From the repository root, with dependencies installed:

```bash
python -m unittest discover -s tests -v
python -m research.verify_study research/runs/overnight \
  --source-root research/frozen_sources/2026-09-10
python -m research.analyse_campaign research/runs/overnight
```

Reanalysis tools write new outputs; they do not alter completed NPZ archives.
Run them in a separate output directory if preserving the published snapshot
byte-for-byte matters. The checks test contracts and reproducibility, not
whether the model predicts a particular material. See
[`docs/PROGRESS_AND_LIMITS.md`](../docs/PROGRESS_AND_LIMITS.md) for the
interpretation and limitations.

The main campaign was executed before `research/campaign.py` gained the
temperature-ratio option used by the later literature benchmark. Its frozen
original runner and engine are under `research/frozen_sources/2026-09-10/`;
their hashes match the completed campaign's manifest. Running the verifier
against the **current** campaign runner correctly reports a source mismatch.
