# Controlled images: what the measurement pipeline can and cannot recover

These checks were designed after the Kawasaki results. They are exploratory
sanity checks, not a new holdout, new physical law or experimental validation.

Open the [illustrated control report](../research/results/geometry_controls_2026-09-20_v3/report.html).
It contains 480 stage-level observations and 192 fits, including 20 unresolved
fits. They share designed images and must not be counted as independent runs.
All cases and all five fraction-matching tie measurements are retained in
`results.json`. Earlier local renderings of the same numerical experiment are retained
privately. This public v3 uses repository-relative provenance paths; its
numerical results are identical to v1 and v2.

## Why these controls help

The periodic checkerboard has a known covariance: for displacement r between
zero and square width w, C(r)=1-2r/w. Both its half-height length and positive
lobe area are w/4. Direct pair products reproduce this exactly for all five
widths. Independent finite-pair sums agree with our FFT measurement to within
4.45e-16. This verifies the particular synthetic reference and correlation
implementation, not every component of the full physics model.

Assigning the scale coordinate t=w^3 gives a one-third slope by construction.
Those coordinates are not sweeps or real ageing times. Even the native
*finite-image* estimator need not reproduce the periodic formula exactly.
For the clean series translated by (1,1), its half-height slope is 0.35575.
At factor four the fraction-matched slope is 0.35719, a difference of +0.00144.
This is not the negative shift seen in Kawasaki data. The difference is worth
keeping: the sign and size of measurement bias are not universal.

At width four and factor eight, every averaged block is exactly 0.5. There is
no contrast left and the integrated length is correctly unresolved. Forcing
the result to contain exactly 50% foreground creates a tie-dependent binary
pattern. For tie seed 110 its measured finite half-height is 3.974 native
pixels, despite the clean periodic reference being one pixel. That number
is not recovered physical information. All five tie choices remain in the
complete table rather than this example being treated as a typical result.

## Limits

- Checkerboards are ordered synthetic geometry, not isotropic alloy domains.
- The paired-defect variant conserves fraction but is not thermal equilibrium.
- Translations change both sampling-grid phase and finite observation edges.
- Pixel interpolation, boundary weighting and segmentation can all contribute;
  these controls do not uniquely attribute the Kawasaki bias to one cause.
- No confidence intervals are inferred from designed origins or widths.
- This check does not implement the full published three-descriptor criterion.

## Reproduce without downloading simulation archives

From the repository root, in its scientific Python environment:

```bash
python -m unittest tests.test_geometry_controls -v
python -m research.geometry_controls --output output/my_geometry_check
```

The output directory must not exist. The generated record hashes the protocol,
measurement sources and outputs. A fresh re-run should reproduce `results.json`;
the timestamp in the manifest will differ. No external data, engine changes,
long simulation or academic endorsement is involved.

The assistant specified and executed these controls and drafted this note.
The student should explain the known-length example and reproduce it before
using it as evidence in their own write-up.
