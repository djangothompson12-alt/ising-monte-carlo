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
.venv311/bin/python -m research.make_mask_resolution_demo \
  --output output/my-new-synthetic-mask-demo
```

Open its `audit/report.html`. The first artificial field contains two drawn
circles and produces three resolved rows; the second has no foreground and
retains three **unresolved** rows. These constructed pixels and arbitrary
units are a usability check, not a materials experiment or a validation set.

## What to declare

Copy [the template](../research/mask_resolution_audit.template.json) to a
private working folder and fill in its source, licence, phase definition,
specimen IDs and mask records. Every mask must be a single 2D array with
exactly two declared integer values, such as 0/1 or 0/255. State who made the
mask and what the foreground means. Give the rectangular ROI, its reason,
pixel size and unit. The ROI must be at least 16 pixels per axis, and its
width and height must divide exactly by four;
the program will not silently trim a specimen field. Choose whether exact
50:50 blocks become foreground or background **before** viewing the output.
Optional time metadata is retained but never used to fit kinetics.

From the repository root, with the working environment installed:

```bash
.venv311/bin/python -m research.mask_resolution_audit \
  path/to/approved-mask-plan.json --output output/new-mask-audit
```

The new folder contains `report.html`, `measurements.csv` and `manifest.json`.
The manifest hashes each input mask and the analysis source and records the
declared labels, field, physical pixel size and time for each image without
copying the input file path. No mask pixels or image previews are embedded in
the report. The HTML shows each image's time and length unit explicitly; the
CSV includes all three resolutions, directional lengths, scale, phase fraction
and unresolved status. Ratios are to each image's own native measurement;
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
ignored local `output/alge_mask_tool_replay_2026-09-18_v2/`; a fresh replay
after the report/provenance update again matched the earlier numerical table.
The [replay script](../research/replay_alge_mask_tool.py) checks the public source
hash, fixed field and earlier table before making that local report. The
published source is Jonas Fell's
[CC BY 4.0 Al–Ge dataset](https://doi.org/10.17632/hj9njz3rxp.1).

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
