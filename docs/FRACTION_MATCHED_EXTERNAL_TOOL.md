# Fraction-matched external audit

## Purpose

Check whether preserving a supplied mask's phase volume fraction is enough
to preserve its measured correlation length when voxels are coarsened.
This is the static counterpart of the simulation's fraction-matched
growth-exponent control. It is not a kinetic comparison or a new segmentation
algorithm. The original mask is an assumed reference, not independent truth.

## Run on an owner-approved mask

Use the existing project dependencies, then:

```bash
python -m research.fraction_matched_external path/to/plan.json \
  --output output/new_external_fraction_audit
```

The plan has `source`, `license`, and a `records` list. Every record requires:
`id`, `specimen`, `path`, `unit`, `spacing_zyx`, `foreground`, `background`,
`roi_zyx`, `roi_reason`, `phase_definition`, and `mask_authority`.
An optional `sha256` is checked against the input. Paths are relative to the
plan. Spacing must be equal and positive along z/y/x. Anisotropic voxels are
rejected rather than silently miscalibrated. Masks are 3D NPY or multipage
scalar TIFF; declare two distinct integer labels. Air/missing/other labels
inside the selected box are rejected. Each side must be at least 32 voxels,
divisible by eight, and the box no larger than 256³ voxels in total.

Open the generated `report.html`. It includes a field selector, native
physical lengths, factor/stage comparisons, all five tie seeds in a download,
fraction residuals, spatial-resolution diagnostics and source hashes. Nothing
is uploaded or transmitted. An existing output folder is never overwritten.

## Public example

The supplied Fell Al-Ge example is at
`research/results/fraction_matched_external_2026-09-19_v1/report.html`.
It uses the previous four fixed boxes, not new regions chosen for nicer results.
Original data: Jonas Fell (2023), Mendeley Data v1,
[doi:10.17632/hj9njz3rxp.1](https://data.mendeley.com/datasets/hj9njz3rxp/1),
CC BY 4.0. The tool derives cropped, averaged and resegmented measurements;
it does not reproduce the authors' separate lamellar/precipitate analysis.

The side-by-side research report is at
`research/results/fraction_matched_benchmark_2026-09-19_v1/report.html`.
Its first table contains **simulated exponent differences**; the second
contains **real static length ratios**. They cannot be treated as the same
quantity. Experimental raw stacks are not redistributed here.

## Honest limits

The control knows the reference fraction; real raw images may not provide
that quantity reliably. Ranking can preserve a count while changing shapes
or connectivity. At coarse resolution, matching is only accurate to half a
voxel count divided by the total voxel count. At least one directional length
below a voxel flags interpolation at an inadequate scale, not super-resolution.
Five tie outcomes do not supply specimen uncertainty. No claim of external
validation is supported until a data owner evaluates the tool for a defined
measurement decision and the student records their criticism and response.

## Reproduce the public-data comparison

Obtain the original stacks from the cited dataset. The existing preparation
script checks their expected hashes and produces the declared fixed regions;
it does not choose regions by the outcome of this new control. Replace the
source-directory placeholder with the directory containing `ROI_15min.tif`,
`ROI_105min.tif`, `ROI_195min.tif` and `ROI_315min.tif`.

```bash
python -m research.prepare_alge_volume_audit \
  --source /path/to/original/stacks --plan output/new_fraction_plan.json
python -m research.fraction_matched_external output/new_fraction_plan.json \
  --output output/new_external_fraction_audit
```

To reproduce the combined simulation and external analysis, after restoring
the raw extension archives from the project's data guide:

```bash
python -m research.fraction_matched_benchmark \
  research/runs/main_065_multisize_v1 output/new_fraction_plan.json \
  --output output/new_fraction_benchmark
python -m research.verify_fraction_matched_control \
  research/runs/main_065_multisize_v1 output/new_fraction_benchmark \
  --output output/new_fraction_verification
```

Use new output names for every run. Input hashes are checked; missing data
are not replaced with synthetic observations. The external tool is a local
command-line prototype producing a readable HTML report, not a hosted upload
service. Browser interaction checks and a genuine outside usability pilot
remain outstanding.
