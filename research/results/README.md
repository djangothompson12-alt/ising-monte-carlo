# Small checked results, not raw research data

This folder holds **aggregate or derived** results small enough to review in
Git. The source campaigns and third-party tomography TIFFs remain under
ignored `research/runs/` paths. A result is not a paper conclusion merely
because it appears here; read its protocol and limitations before citing it.

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
