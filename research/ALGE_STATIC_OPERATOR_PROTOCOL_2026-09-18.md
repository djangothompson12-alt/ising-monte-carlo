# Fixed bounded Al–Ge image-operator test

*AI-assisted exploratory protocol, written on 18 September 2026 after obtaining
the public stacks and inspecting their metadata plus one displayed plane. It
is fixed **before computing the correlation lengths or 4×-operator shifts**
reported by this test. This is not a blind preregistration, an independent
specimen series, or a Kawasaki-to-alloy validation.*

## Source and purpose

Use only Fell's four labelled Al–Ge ROI TIFF stacks at 15, 105, 195 and 315
minutes ([dataset DOI](https://doi.org/10.17632/hj9njz3rxp.1), CC BY 4.0).
The dataset says voxel spacing is 60 nm, Al label 2, Ge label 3 and air label
0. Local QA found occasional labels 1 and 4. The initial `Sample_0min` file
has a different 260 nm voxel and is **excluded**. The source paper has
already studied its 3D feature evolution. Our question is narrower: does a
fixed 4× block-averaging-plus-binary-threshold step alter a 2D correlation
length on these published *real* segmented microstructures?

No stage is treated as an independent alloy specimen. Different z planes
within a stack are correlated. Do not fit a growth exponent from the four
stages, align their minutes to Monte Carlo sweeps, or infer strength.

## Sampling fixed now

For each ROI TIFF, inspect exactly 11 physical z planes at 12.0, 12.6, ...,
18.0 µm, using the TIFF `BoundingBox` z origin and 0.06 µm spacing. At every
plane, calculate the centroid of pixels labelled 2 or 3. Take a 300×300 pixel
(18×18 µm) square centred on that centroid, rounding to the nearest pixel.
Record its bounds and its 0/1/2/3/4 label counts. This is an image-specific
interior ROI, **not** a registered same-particle track. If a square falls
outside the image, contains more than 0.5% labels other than 2 or 3, or has
an unresolved correlation crossing, retain it in the raw table and mark the
stage analysis unresolved. Do not replace or cherry-pick planes.

The primary binary field is +1 for Ge (3) and −1 for Al (2); any sparse
non-2/3 labels within an otherwise eligible square are set to −1 for the
primary calculation and their fraction is reported. Recompute each length
with those labels set to +1 as a **worst-case encoding sensitivity**. If that
bound materially changes the result, do not claim a robust operator effect.

## Observation and summary

Use `research.imaging.image_length` with **non-periodic** axis correlations,
connected/normalised using each image's observed mean, and first 0.5
crossing. Native pixel spacing is 0.06 µm. Altered observation is exactly
`observe(field, factor=4, threshold=0)` on the binary field: arithmetic
4×4 block means, tie assigned +1, then `image_length` with 0.24 µm pixel
spacing. Retain both x/y crossings and the average, plus apparent Ge
fractions. No other threshold, blur, rescaling or crop is chosen after seeing
the values. The ratio altered/native is defined only when both are resolved.

For each stage report all 11 rows, the median ratio, its min–max range and
the median apparent Ge-fraction change, **descriptively**, not as an
independent-sample confidence interval. Also report whether all 11 pass the
fixed ROI and resolution checks. The sign of the length shift is not assumed.
Do not compare this ratio directly with the simulation's *growth-exponent*
shift: one is a static length ratio and the other a slope over time. The
real-data result can at most show transfer of a sensitivity question to
published segmented alloy images.

The TIFFs remain in ignored local storage; code, a source citation, hashes,
numerical tables and appropriately attributed illustrative panels may be
shared after student review. No claim is made that Fell or a company used or
endorsed this workflow.
