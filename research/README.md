# Simulations and measurement checks

[Project overview](../README.md) · [Research summary](../docs/ACADEMIC_REVIEW_BRIEF_2026-09-20.md)

This folder contains the batch experiments and analysis, separate from the
interactive visualisers. Simulation settings and measurement choices are
recorded so that results can be checked without relying on screenshots.

## Start with a small example

From the repository root, after installing the dependencies:

```bash
python -m research.geometry_controls --output output/my_geometry_check
```

Open `output/my_geometry_check/report.html`. This uses designed images with
known lengths. It needs no new Monte Carlo run and no external image download.
Use a new output directory rather than replacing an existing result.

## Find the evidence

| What you need | Where to look |
|---|---|
| Raw trajectories, seeds and reproduction commands | [Data guide](DATA_README.md) |
| Current result tables and figures | [Results index](results/README.md) |
| Declared fresh-run measurement design | [Growth-reliability protocol](GROWTH_RELIABILITY_PROTOCOL_2026-09-19.md) |
| Known-geometry controls | [Geometry protocol](GEOMETRY_CONTROL_PROTOCOL_2026-09-20.md) |
| Long-run size/composition study | [Extension protocol](MAIN_EXTENSION_PROTOCOL.md) |
| External mask tool | [Instructions](../docs/THREE_DIMENSIONAL_AUDIT.md) |

`campaign.py` runs independent seeded trajectories. Analysis scripts read
saved snapshots; image processing is never fed back into the spin dynamics.
`plans/` holds run settings, `frozen_sources/` preserves older campaign code,
and selected completed raw data are under `runs/`.

Most new output is ignored by Git. Named datasets in the data guide are
deliberately included. Third-party source images and private review packs are
not included. Do not infer physical validation from a completed calculation.
