# Results index

This folder holds **aggregate or derived** results small enough to review in
Git. Selected raw simulation campaigns are included separately in
[the data guide](../DATA_README.md); third-party source TIFFs are not.
A result is not a paper conclusion merely
because it appears here; read its protocol and limitations before citing it.

## Current study

| Result | Start here |
|---|---|
| Fresh 16-run measurement check | [Interpretation](../../docs/GROWTH_RELIABILITY_RESULTS_2026-09-19.md), [fits](growth_reliability_fresh_2026-09-19_v1/fits.csv) and [figures](growth_reliability_summary_2026-09-19_v1/) |
| Fraction-matched control on 32 earlier trajectories | [Results](../../docs/FRACTION_MATCHED_RESULTS_2026-09-19.md) and [data](fraction_matched_benchmark_2026-09-19_v1/) |
| Known-geometry checks | [Explanation](../../docs/GEOMETRY_CONTROLS_2026-09-20.md) and [all observations](geometry_controls_2026-09-20_v3/results.json) |
| Static 3D Al–Ge image check | [Scope and limits](../../docs/ALGE_VOLUME_RESULTS_2026-09-19.md) and [two-observable follow-up](external_length_reliability_2026-09-19_v1/) |

HTML reports are intended to be opened locally after cloning. GitHub normally
shows their source; the Markdown notes above are the readable online entry points.
Versioned directories preserve provenance, not independent extra experiments.

## Earlier checks

- `paired_window_sensitivity_2026-09-18/`: a post-result paired bootstrap
  on eight archived trajectories per composition. The CSV is numerically
  identical to its first local run; `provenance.json` names the exact 16 raw
  NPZ hashes and analysis source. See
  [the interpretation](../../docs/PAIRED_WINDOW_AUDIT_2026-09-18.md).
- `alge_time_series_metadata_qa_2026-09-18/`: source hashes, dimensions,
  sampled labels and an adapted inspection panel for the four public
  segmented ROI stacks by Jonas Fell, Mendeley Data V1,
  [DOI 10.17632/hj9njz3rxp.1](https://doi.org/10.17632/hj9njz3rxp.1),
  CC BY 4.0. The panel is not registered 3D evidence; the original TIFFs
  are not redistributed here.
- `alge_static_operator_2026-09-18/`: all 44 planned plane measurements,
  including unresolved rows, plus a strict-JSON summary. The four source
  TIFF hashes, protocol hash and analysis-source hashes are recorded. See
  [the fixed protocol](../ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md)
  and [bounded outcome](../../docs/ALGE_REAL_IMAGE_AUDIT_2026-09-18.md).

The real-image test is a within-image observation sensitivity check on one
specimen, not a new measured ageing law, simulation calibration, alloy
property prediction or external endorsement.
