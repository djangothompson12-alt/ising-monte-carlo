# Data included in the repository

The main evidence is a set of seeded Model B simulations, not a measured
alloy time series. Files are under `research/runs/`; most generated output is
ignored by Git, but the named campaigns below were deliberately selected for
this release. A complete archive is not automatically a validated physical
result.
[Field names, units, missing-value rules and the independent sampling unit](DATA_DICTIONARY.md)
are defined separately so a reader can check a number without guessing what
an NPZ array means.

| Folder | What it contains | Status |
|---|---|---|
| `runs/overnight/` | 64 raw NPZ trajectories, plan/manifest/status, growth summaries, estimator and image-operation analyses | Complete to 200,000 sweeps |
| `runs/imaging_validation/` | Eight fresh raw NPZ trajectories and image-operation repeat | Complete to 20,000 sweeps |
| `runs/pilot/` | Earlier 24-replica exploratory campaign and summaries | Pilot; not an independent confirmation |
| `runs/measurement_reliability_map_v1/` | Compact comparison of original and fresh image-operation results | Exploratory |
| [`runs/majumder_das_2010_l128/`](runs/majumder_das_2010_l128/) | 40 new 0.6 Tc, L=128 trajectories to 4.5 million sweeps; raw manifest and integrity audit | Complete raw archive; no student-approved paper-method fit or multi-size reproduction |
| [`runs/main_065_multisize_v1/`](runs/main_065_multisize_v1/) | 128 completed 0.65 Tc million-sweep trajectories over four sizes and two compositions, with analysis and new-seed image holdout | Complete, internally audited release; not independently peer reviewed |

The main comparison used `Jx=Jy=1`, `T_final=0.65Tc`, compositions 0.50 and
0.15, widths 32/64/96/128 and eight independent runs per condition. The
fresh observation repeat used different seeds at width 128, four runs per
composition. Exact integer compositions, seeds, code hashes and dependency
versions are in each campaign manifest. NPZ files include archived times,
lattice snapshots, directional lengths, energies and magnetisation.

The completed 0.6 Tc reference raw run and million-sweep extension are now
selected Git-tracked datasets. The local review packs under `output/` are
duplicate private packaging, not a second source of observations; they are
**not** in this repository. The reference raw trajectories do not themselves
give a paper-method-matched exponent. The extension files include the
[complete fit table](runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md),
unresolved rows, source hashes, independent table audit and
[new-seed image-holdout result](runs/main_065_multisize_v1/image_holdout_v1/REPORT.md).
Internal reproducibility is not independent laboratory replication or
external endorsement.
A separate synthetic known-growth **measurement control** is not a Kawasaki trajectory.
The third-party Al-alloy images and large duplicate evidence ZIPs are likewise
not public repository data. Small aggregate outputs and an attributed
inspection panel from the public CC BY 4.0 Al–Ge source are under
[`research/results/`](results/README.md); the four original Mendeley ROI
volumes are **not** included. Those outputs record exact source TIFF hashes
and include unresolved rows from a fixed image-operator test, not an
experimental coarsening rate. No physical tennis-string measurements exist
yet.

From the repository root, with dependencies installed:

```bash
python -m unittest discover -s tests -v
python -m research.verify_study research/runs/overnight \
  --source-root research/frozen_sources/2026-09-10
python -m research.analyse_campaign research/runs/overnight
```

After installing `requirements.txt` in an active virtual environment (as in
the root README), first check both newly released raw campaigns:

```bash
python -m research.verify_study research/runs/majumder_das_2010_l128 --source-root .
python -m research.verify_study research/runs/main_065_multisize_v1 --source-root .
```

Both commands have also passed from a fresh checkout of the public commit.
The older 64-run `overnight` campaign, unlike these two, needs the frozen
2026-09-10 source directory shown above. This distinction follows the source
hashes recorded at each campaign's launch.

To **recheck the completed extension from a fresh checkout**, use new output
names rather than replacing the published tables. The campaign must have a
`complete` status with all 128 declared files. The independent audit recalculates every declared
growth-fit, ensemble-length and matched-size table entry from raw NPZ files;
it checks arithmetic and provenance, not the physical interpretation:

```bash
python -m research.verify_study research/runs/main_065_multisize_v1 --source-root .
python -m research.audit_archived_observables \
  research/runs/main_065_multisize_v1 \
  --output research/runs/main_065_multisize_v1/observable_audit_recheck.json
python -m research.replay_first_energy_interval \
  research/runs/main_065_multisize_v1 --source-root . \
  --output research/runs/main_065_multisize_v1/first_interval_replay_recheck.json
MPLCONFIGDIR=.mplconfig python -m research.analyse_main_extension \
  research/runs/main_065_multisize_v1 \
  --output research/runs/main_065_multisize_v1/analysis_recheck
python -m research.audit_main_extension \
  research/runs/main_065_multisize_v1 \
  research/runs/main_065_multisize_v1/analysis_recheck \
  --output research/runs/main_065_multisize_v1/analysis_recheck/independent_table_audit.json
python -m research.render_extension_appendix \
  research/runs/main_065_multisize_v1 \
  research/runs/main_065_multisize_v1/analysis_recheck \
  --output research/runs/main_065_multisize_v1/analysis_recheck/appendix_recheck
```

The [separate new-seed image holdout](PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md)
also refused to run before full completion and used its own saved-state
measurement. It is not part of the original physics fit. Its local result is
[`research/runs/main_065_multisize_v1/image_holdout_v1/REPORT.md`](runs/main_065_multisize_v1/image_holdout_v1/REPORT.md).
On 18 September, the analysis and holdout were also run from an unpacked
private review copy into a **fresh separate output folder**. The three
primary CSV tables, all-row Markdown appendix and two holdout CSVs were
byte-identical to the archived local results; the observable audit again
checked 19,200 directional lengths and the first-interval replay passed all
128 trajectories. This is a same-code reproducibility check, not an
independent laboratory replication or a different dynamics implementation.

**Public-checkout replay, 18 September:** A clean local clone of release
commit `ec3fb87` (with the same tested Python environment) passed all 119
tests and both new raw-campaign verifiers. Its archived-observable audit
checked 9,600 snapshots and 19,200 directional lengths, retaining the one
strict-threshold FFT-roundoff ambiguity; its first-interval energy replay
passed all 128 extension trajectories. Reanalysis in a new directory passed
the independent 80-fit/450-matched-size-row audit. The three principal CSVs
and rendered all-row appendix were byte-identical to the published versions.
This checks that the Git snapshot contains enough information to rerun the
analysis on that environment; it is not an independent implementation or
scientific validation of the model.

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
