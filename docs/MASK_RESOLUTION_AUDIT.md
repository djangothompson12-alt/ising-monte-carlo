# Auditing the effect of resolution on a supplied phase mask

This is a **bounded, local prototype** for a materials-imaging researcher who
already has an approved binary phase mask and knows its physical pixel size.
It measures how a declared 2D correlation half-height length changes when the
*same field* is reduced to 2× and 4× coarser pixels. It also records apparent
phase fraction and how many 50:50 blocks invoke the chosen tie rule. It does
not create a phase mask from a microscope image, fit an ageing exponent,
identify precipitates, or predict alloy properties. Downsampling an existing
mask is **not** the same experiment as collecting a lower-resolution
micrograph and segmenting it again: instrument noise, contrast and
classification errors are deliberately held out of this test.

There is a second boundary that matters for this project. The fraction of a
binary image labelled as one **phase** is not generally the alloy's conserved
chemical composition. Real phases can have different solute concentrations,
and their area or volume fractions can change during a transformation even
though the total amount of each element in a closed specimen is conserved.
Therefore the `phase_fraction` column is only a geometrical check on the
supplied mask. It must not be described as a chemical mass-balance test. A
calibrated elemental-composition map would be needed for that different
question; even then, its field, registration and calibration would have to be
checked separately.

The reason for this route is empirical: on the published MetalDAM steel
images, simple raw-image thresholding failed to recover the producer-mask
length reliably. A mask supplied and checked by the problem owner is a more
honest starting point for a measurement-sensitivity conversation. The Al–Ge
test showed another limitation: a 2D region can contain no feature of
interest, leaving the length unresolved. This tool retains that failure.
Neither public-data result establishes that a laboratory wants this tool.

To try the workflow without sharing or preparing any real image, run the
[deterministic synthetic demo](../research/make_mask_resolution_demo.py):

```bash
python -m research.make_mask_resolution_demo \
  --output output/my-new-synthetic-mask-demo
```

Open its `audit/report.html`. The first artificial field contains two drawn
circles and produces three resolved rows; the second has no foreground and
retains three **unresolved** rows. These constructed pixels and arbitrary
units are a usability check, not a materials experiment or a validation set.

## What to declare

Copy [the template](../research/mask_resolution_audit.template.json) to a
private working folder and fill in its source, licence, phase definition,
materials context, specimen IDs and mask records. For a materials pilot, state
the material system, processing or ageing condition, imaging method, section or
acquisition geometry, spatial-calibration source and the measurement's intended
use. The program rejects a partly completed `materials_context` block rather
than displaying an apparently complete materials result with missing context.
Every mask must be a single 2D array with
exactly two declared integer values, such as 0/1 or 0/255. State who made the
mask and what the foreground means. Give the rectangular ROI, its reason,
pixel size and unit. The ROI must be at least 16 pixels per axis, and its
width and height must divide exactly by four;
the program will not silently trim a specimen field. Choose whether exact
50:50 blocks become foreground or background **before** viewing the output.
If the problem owner can state what relative change in measured length would
matter to their comparison, record it as `decision_tolerance_fraction` and
explain it in `decision_tolerance_reason` before running the audit. Otherwise
leave the tolerance null. The report will then show the measurements without
inventing an acceptable/unacceptable classification after seeing the result.
Multi-frame TIFF stacks are rejected: explicitly select and save one plane
first, so the tool cannot silently analyse the wrong slice.
Optional time metadata is retained but never used to fit kinetics.
The one-number pixel scale assumes **square pixels** with the same physical
spacing in x and y. Do not use it on anisotropic pixels or oblique sections
by entering an average spacing; that needs a separately checked estimator.

From the repository root, with the dependencies installed in an active
virtual environment (see the root README):

```bash
python -m research.mask_resolution_audit \
  path/to/approved-mask-plan.json --output output/new-mask-audit
```

The new folder contains `report.html`, `measurements.csv` and `manifest.json`.
The manifest hashes each input mask and the analysis source and records the
declared labels, field, physical pixel size and time for each image without
copying the input file path. No mask pixels or image previews are embedded in
the report. The HTML shows each image's mask authority, ROI, time, pixel
spacing and length unit explicitly; the CSV includes all three resolutions,
directional lengths, scale, phase fraction and unresolved status. Ratios are
to each image's own native measurement;
the table also reports phase-fraction change, percentage length change, a
directional X/Y geometry ratio and the minimum measured length in coarse-pixel
units. The X/Y ratio describes the selected mask, not mechanical anisotropy or
crystallographic texture. The three-pixel screen is a conservative warning,
not a validated materials standard.
do not compare raw lengths if their units or phase definitions differ.
The report and manifest do retain the supplied specimen IDs, source and
description, even though they omit mask pixels and file paths. Keep the
output private until the image owner approves sharing those details.
It will refuse to overwrite a prior output. A hash documents which file was
used; it cannot certify the accuracy of a segmentation or the declared scale.

## Checked public-data example

A **post-hoc usability replay** selected one already-resolved plane from the
earlier fixed 44-plane public Al–Ge audit: the producer's segmented 315-minute
stack at z = 12.0 µm, within its recorded 300×300 field. With the published
0.06 µm voxel size and Ge label as foreground, this tool returned a native
length of 0.13456 µm and a 4×-reduced length of 0.16064 µm (ratio 1.19388).
These match the earlier table exactly because the same length estimator and
field are used. The replay is therefore a **workflow/units check**, not a new
independent result or a second specimen. The derived mask and HTML stay in
ignored local `output/alge_mask_tool_replay_2026-09-19_v5/`; a fresh replay
after adding the explicit report context and single-plane input check again
matched the earlier numerical table. The materials-context update was replayed
locally in `output/alge_mask_tool_replay_2026-09-22_v6/`. It also flags the
selected measurement as poorly resolved: the smaller native directional length
spans about 2.15 pixels and the 4x result about 0.63 coarse pixels. A numerical
half-height crossing can still be interpolated in that situation, but it should
not be presented as recovered sub-pixel microstructural information.
The [replay script](../research/replay_alge_mask_tool.py) checks the public source
hash, fixed field and earlier table before making that local report. The
published source is Jonas Fell's
[CC BY 4.0 Al–Ge dataset](https://doi.org/10.17632/hj9njz3rxp.1).

A second, independent public-sample check used the heat-treated optical
metallography Si-particle mask from
[MicroAl-Dataset](https://github.com/neulmc/MicroAl-Dataset), with its stated
0.1 micrometres-per-pixel scale. The whole 256x256 field was fixed before the
run, black Si-particle pixels were foreground and exact block ties went to
background. The native, 2x and 4x mean lengths were 0.832499, 0.832193 and
0.851150 micrometres. The 4x row was flagged because its smaller directional
length occupied only 1.94 coarse pixels. This is a useful independent workflow
stress test, not evidence that numerical downsampling recreates a lower
resolution microscope acquisition. The source restricts the data to academic
research and prohibits unauthorised redistribution, so its raw pixels remain
outside this repository. Full limitations and dataset screening are recorded
in [the validation record](MASK_RESOLUTION_AUDIT_VALIDATION_2026-09-22.md) and
[public-data scope](PUBLIC_MASK_DATA_SCOPE_2026-09-22.md).

The most extensive public-data check uses all 81 registered fields in the
[FeM iron-ore dataset](https://doi.org/10.5281/zenodo.5014700). Each producer
reference separates ore from embedding resin at 1.05 micrometres per pixel.
Using a fixed field and ties to background, the median length changed by
-0.898% at 2x and +1.610% at 4x; all 81 fields remained resolved and none
triggered the three-pixel warning. A clearly labelled post-hoc opposite-tie
sensitivity changed the median shifts to +1.925% and +2.530%. Thus the sign of
the small 2x effect depends on how exactly balanced blocks are classified.
Nine directional measurements were also reproduced by a separate direct
real-space calculation to `1e-10`. See the
[full FeM record](FEM_PUBLIC_MASK_AUDIT_2026-09-22.md). The 81 fields come from
one mounted sample and must not be presented as independent specimens.

## The first outside test

Ask a researcher which phase and downstream measurement *they* use, what
change would matter to their decision, and whether they have a reference mask
and scale they are allowed to share. Agree on an ROI and tie rule in advance.
Use the [small pilot record](MASK_AUDIT_PILOT_RECORD.template.md) to write
those choices down before inspecting a new result table.
Then give them the full table, including unresolved rows, and ask whether the
audit exposed a relevant sensitivity, was redundant with their present
checks, or was misleading. Record their actual criticism and any revision.
Do not call a download, conversation, or unapproved demonstration
"deployment" or "endorsement." Multiple slices from one specimen remain
correlated; they are not independent experimental repeats.

The full boundary between a binary phase-mask pilot and a quantitative
composition-map pilot is set out in the
[external-pilot decision document](CONSERVATION_AWARE_EXTERNAL_PILOT_2026-09-19.md).
