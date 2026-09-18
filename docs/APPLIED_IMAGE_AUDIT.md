# Applied image-measurement audit: prototype

For a **supplied binary phase mask**, use the newer
[mask-resolution audit](MASK_RESOLUTION_AUDIT.md). It holds the declared
segmentation fixed and tests spatial resolution. The threshold-based tool
below remains useful for explicitly exploratory threshold sensitivity, but
the public steel pilot showed that threshold-only masks can badly misstate
the producer-mask length. Neither tool is externally validated.

`research/image_audit_report.py` turns a declared set of calibrated, single-
plane images into a local HTML report plus CSV and hash manifest. It uses the
already-tested finite-window, non-wrapping correlation length. It **does not**
segment phases automatically, fit growth laws, infer alloy properties or
certify a microscope measurement.

## What a user must supply

Copy `research/image_audit.template.json` to a new location and replace every
placeholder. Each record needs a real image path, one rectangular ROI in
`[row_start,row_stop,col_start,col_stop]` format, a reason for that ROI, at
least three candidate thresholds and a reason they were chosen, a foreground
convention, a calibrated physical pixel size and length unit. `time` and
`time_unit` may be added as metadata for an ageing series; the program will
**not** infer a growth exponent from them. An expert should identify which
phase the foreground represents. The same nominal ROI coordinates across
unregistered images do not imply the same specimen volume.

From the repository root, after checking the manifest and rights:

```bash
.venv311/bin/python -m research.image_audit_report path/to/approved.json \
  --output path/to/new-audit-folder
```

This writes `report.html`, `measurements.csv`, `summaries.csv` and
`manifest.json`. To embed cropped image previews in the HTML, add
`--include-previews` and declare `preview_threshold` for every record. The
default **does not embed images**; check sharing permission before enabling
previews or sending the resulting file to someone else. The report never
overwrites a prior output directory.

To see the report format, generate a new local synthetic example:

```bash
.venv311/bin/python -m research.make_image_audit_demo \
  --output output/my_synthetic_demo
```

Open `output/my_synthetic_demo/audit/report.html` locally. The generated
image is not experimental microstructure data and does not validate the
method on real materials images. Generated `output/` files are local work,
not part of the public source snapshot.

The CSV retains every declared threshold at the original scale and, where the
ROI dimensions permit it, after 2× and 4× block averaging *before*
thresholding. Pixel spacing is multiplied by the binning factor. If reduction
is impossible or a directional crossing is unresolved, the row remains in the
CSV with a status instead of disappearing. Apparent phase fraction is recorded
so that a threshold-induced change in composition is visible. The summary
quotes a descriptive range across thresholds; it is **not** an uncertainty
interval or universal reliability score. No threshold is selected as “best.”

## Validation path and limits

1. The deterministic unit tests check ROI boundaries, retained thresholds,
   physical pixel spacing, non-divisible binning, immutability, overwrite
   guards and HTML escaping. Existing tests separately check the finite-image
   FFT against explicit non-periodic pair products.
2. A public annotated metallography dataset such as the
   [NIST ultrahigh-carbon-steel images](https://www.nist.gov/publications/high-throughput-quantitative-metallography-complex-microstructures-using-deep-learning)
   can test static segmentation/length sensitivity against reference masks.
   That would **not** validate an ageing exponent or the Kawasaki dynamics.
   A first exploratory test on the published MetalDAM austenite annotations is
   now recorded in [the static-image pilot](METALDAM_STATIC_PILOT_2026-09-17.md).
   It stress-tests the shared length estimator and simple threshold masks,
   **not** the full user-facing audit workflow or its value to a laboratory.
3. The [five AlGe feasibility slices](https://doi.org/10.5281/zenodo.14923133)
   do not justify a growth exponent. A distinct
   [fixed test on four labelled Al–Ge stacks](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md)
   measured static resolution sensitivity but failed on some early
   interior regions. Their source authors separate Ge lamellae from
   precipitates, while that first 2D test does not. A meaningful kinetic
   or feature-specific study would require expert decisions about phase,
   region, registration and independent specimens.

The tool currently supports only rectangular ROIs, single-plane scalar
images and threshold segmentation. It cannot account for irregular specimen
masks, 3D topology, changing instrument response, annotation disagreement,
registration or correlations between slices of the same volume. A researcher
can use the report to inspect sensitivity and propose a better protocol; it
is not yet an externally validated instrument or a claim of lab adoption.
