# First 3D real-data audit: results and limits

This is an exploratory **static measurement** test, not a growth-law fit.
The [method and source attribution](THREE_DIMENSIONAL_AUDIT.md) describe the
four supplied Al–Ge masks and fixed-region protocol. No original simulation
trajectory or engine was changed for this test.

## What happened

All four fixed 256³-voxel boxes contained only the two declared phase labels.
The 60 comparisons produced 40 resolved three-axis half-height lengths and
20 unresolved values. The smaller 192³ and 128³ fields at 15 and 105 minutes
contained no Ge; their variance and lengths were therefore undefined. They
were not replaced with other regions.

For the 195-minute **full box**, changing from native 0.06 µm voxels to
fourfold block-averaged 0.24 µm voxels changed the mean directional
half-height length from 0.15717 to 0.32173 µm: a factor of 2.047. The field
mean was preserved. Thresholding that averaged field produced 0.21005 µm,
a factor of 1.336 relative to native. It changed the Ge volume fraction from
0.0041834 to 0.0027008. This illustrates two different observation effects;
it does not show that thresholding is generally better or worse.

For the 195- and 315-minute native boxes, halving each field dimension
reduced the measured length to 0.690 and 0.707 of its full-box value,
respectively. These are paired crop comparisons, not independent specimens.

## Why these numbers require care

The selected full boxes have very little Ge (roughly 0.029–0.671% by volume).
Even a resolved crossing may therefore describe a small, unrepresentative
set of features. In some processed cases the inferred length is comparable
to or smaller than one coarse voxel: interpolation gives a number but does
not recover missing sub-voxel information. Native segmentation is also an
assumed reference, not established physical truth.

The scan time labels do **not** justify fitting a coarsening exponent:
region representativeness and cross-time registration remain unestablished.
No error bars from independent specimens, optimum field size, alloy property
prediction, or external validation are claimed.

The useful finding is a demonstrable measurement failure and sensitivity
on real labelled volumes, alongside synthetic tests of the calculation.
The next external test should use regions selected by a researcher for a
specific question, with independent specimens if population inference is
needed. Do not retrofit region selection to make this example look cleaner.

## Verification

Eight new automated tests cover direct-pair versus FFT correlations,
physical-spacing scaling, complementary labels, censored chords,
mean-preserving integration, segmentation ties, missing phases, undeclared
labels, TIFF/NPY agreement, bounds checks, source hashes, escaped report
content and refusal to overwrite. The complete suite passed 139 tests.

The generated report and measurements are in
`research/results/alge_volume_audit_2026-09-19_v3/`. Version 3 uses streamed
hashing and reduced dependencies; all 60 measurement rows reproduce version
2 exactly. That folder contains
derived measurements, not the original tomography stacks. Its manifest
records input hashes, coordinates, labels, spacing and analysis-source
hashes. Results do not constitute independent peer review.
