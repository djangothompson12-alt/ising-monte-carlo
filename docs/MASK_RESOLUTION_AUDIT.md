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

The practical question is: **does digital 2x or 4x reduction keep this
declared length measurement within a tolerance the image owner chose in
advance?** The report now checks both exact 50:50 block-tie conventions on
the same field. It keeps the declared rule as the primary measurement and
shows when the conclusion changes under the opposite rule. It never chooses
the rule giving the better-looking result. This helps an owner judge a
particular processing choice; it does not supply a universal resolution limit.

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
Declare `decision_scope` as `mean_length` (the backward-compatible default)
or `both_directions`. The latter requires **each** horizontal and vertical
length to stay within the owner tolerance. For example, changes of +20% and
-20% cancel in the mean when the native directional lengths are equal;
agreement of that mean alone is not agreement of the directional geometry.
The report records both directional percentage changes and their maximum
absolute change, whichever scope is chosen. These are paired sensitivity
measurements, not uncertainty intervals or physical-accuracy estimates.
A tolerance classification never removes a separate low-resolution warning.
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

For this static CLI, demo and verification only, install
`requirements-mask-audit.txt` instead of the full visualiser environment.
Only NumPy, SciPy and Pillow are required. The workflow is tested with the
plotting, simulation and UI imports blocked, but a fresh-machine installation
is not claimed. Python 3.11 is the tested runtime. The exact runtime versions
are recorded in each new audit manifest.

The new folder contains `report.html`, `measurements.csv`, `tie_sensitivity.csv`,
`decision_summary.csv` and `manifest.json`. The HTML opens with a short summary
of what needs checking. Detailed measurements, method and source information
are available underneath. `measurements.csv` retains the declared primary rule;
`tie_sensitivity.csv` has both rules at 2x and 4x; `decision_summary.csv` records
whether the declared criterion depends on the tie rule and retains any
resolution warning even when the numerical tolerance is met. The two rules
are a sensitivity comparison, not a statistical uncertainty interval.
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
Input hashes now identify the exact byte snapshots parsed and measured, not a
second read after calculation. A source-file change during the calculation
causes the audit to stop before writing its output directory.

## Check the calculation

Run the independent synthetic checker in a new folder:

```sh
python -m research.verify_mask_resolution_audit --output output/my-mask-verification
```

The checker independently counts centred pixel-pair products and interpolates
the half-height crossing using exact rational arithmetic. It checks 18 small
synthetic fields across three reduction factors, two tie rules and three
pixel spacings: 324 measurements. Empty fields and missing directional
crossings remain unresolved. It uses no averaging, correlation or crossing
helper from the production audit. This is verification of the specified
discrete calculation, not validation of physical sizes or segmentation.

The current audit also recomputes binary pair counts exactly when FFT values
are within 1e-12 of the half-height level. That number selects a numerical
check; it is not measurement uncertainty. Tolerance decisions allow only
eight floating-point epsilons of roundoff at their inclusive boundary.
The frozen simulation analyses use their recorded historical sources.
See the [current validation and tool comparison](MASK_AUDIT_REVIEW_2026-10-13.md)
for the checks, limitations and the narrower claim about its purpose.

The [bounded value and baseline specification](AUDIT_VALUE_AND_BASELINE_2026-10-15.md)
separates a practical processing check from a new algorithm claim. The optional
`python -m research.check_mask_covariance_conventions --output output/new-convention-check`
companion checks the finite-field centring convention using separately counted
synthetic pairs. It is not a PoreSpy execution, a full published-method baseline,
or physical validation. Different centring/directional conventions must be
declared before comparing measurements from different packages.

For an exhaustive check of the smallest supported **4x4** measurement grid:

```sh
python -m research.verify_mask_resolution_audit --exhaustive-four-by-four \
  --output output/my-exhaustive-mask-check
```

This enumerates all 65,536 binary fields at that shape and compares with the
separate exact-rational reference. It does not exhaust larger fields, make a
4x4 field physically adequate, or test the correctness of a segmentation.

Before handing over an existing result, verify its four output hashes and,
when the original plan/masks are available locally, replay its numerical tables:

```sh
python -m research.verify_mask_audit_delivery output/my-audit \
  --input-plan path/to/the-original-plan.json --require-current-sources
```

Without `--input-plan`, only delivery integrity is checked; no numerical
reproduction is claimed. Without `--require-current-sources`, an old source
version is reported as different rather than silently certified as current.
Hashes are not authentication: someone could alter a table and rehash it.
Local replay detects a disagreement with the implementation and supplied
inputs, not physical truth or an independently written algorithm.

An allowlisted **local**, synthetic-only review copy can be prepared with
`python -m research.build_mask_pilot_bundle --output output/new-mask-pilot-copy`.
It includes a short README and the minimal dependencies, not private planning,
raw microscopy or simulation archives. Preparing this copy does not send,
publish or establish student approval of it.

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
