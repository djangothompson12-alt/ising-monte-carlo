# Validation record for the phase-mask resolution audit

**Status:** internal numerical and workflow checks completed on 22 September
2026. This is not independent laboratory validation.

## Intended materials-science use

The tool answers one bounded question: when the same checked binary phase mask
is represented at native, 2x and 4x pixel spacing, how much do its declared
correlation half-height length and phase area fraction change?

A real pilot must now declare:

- material system;
- processing or ageing condition;
- imaging method;
- section or acquisition geometry;
- spatial-calibration source;
- intended microstructural measurement;
- mask authority, phase definition and fixed field;
- any owner-defined tolerance, with its reason fixed before analysis.

The report does not equate phase area fraction with bulk chemical composition.
It reports an X/Y geometry ratio but does not call it mechanical anisotropy or
crystallographic texture.

## Numerical checks completed

The checked calculation uses a finite, nonperiodic covariance: opposite image
edges are not joined. The implementation has been tested against an explicit
pair-by-pair calculation. Additional controls check:

- invariance to exchanging foreground and background labels;
- correct scaling when physical pixel spacing changes;
- exchange of horizontal and vertical results when an image is transposed;
- constant and one-direction-only fields remaining unresolved;
- exact rejection of undeclared labels, antialiased masks and silently cropped
  fields;
- explicit 50:50 block-tie handling;
- preservation of the source mask;
- consistency with the earlier public-mask measurement kernel;
- input, source and output hashes;
- refusal to overwrite an earlier audit;
- escaping of user-supplied report text;
- rejection of incomplete materials context and unexplained decision
  tolerances.

The complete repository suite passed **192 tests** on 22 September 2026. Test
success shows that the software performs the declared calculation consistently;
it does not establish that the calculation is the correct physical descriptor
for a particular material.

## Synthetic workflow check

The deterministic two-circle demonstration produced resolved native, 2x and
4x measurements. Its empty field remained unresolved at every factor. Because
the demonstration contains no material, the report explicitly marks its
materials context as undeclared and refuses to classify the changes without an
owner tolerance.

Local output: `output/mask_resolution_demo_2026-09-22_v3/`.

## Published Al-Ge workflow replay

One previously selected 315-minute plane from the published segmented Al-Ge
tomography was replayed using the same fixed 300x300 field and 0.06 micrometre
voxel spacing. Input and reference hashes were checked. The updated workflow
reproduced the earlier values:

| Representation | Mean half-height length | Relative to native | Ge area fraction |
|---|---:|---:|---:|
| Native | 0.134556 micrometres | 1.000000 | 0.004744 |
| 2x | 0.144511 micrometres | 1.073983 | 0.005467 |
| 4x | 0.160644 micrometres | 1.193881 | 0.004267 |

The improved screen also exposes why this is not a comfortable physical
validation. The smaller directional length spans only about 2.15 pixels at
native resolution, 1.20 pixels at 2x and 0.63 pixels at 4x. All three rows are
flagged. The selected phase is sparse, every image comes from one specimen and
the same estimator produced both the original and replayed values.

Local output: `output/alge_mask_tool_replay_2026-09-22_v6/`.

## Independent MicroAl public-sample test

I next screened public materials-image datasets for a binary phase mask, an
explicit physical pixel scale, a clear feature definition and terms that allow
an academic test. The public GitHub sample from
[MicroAl-Dataset](https://github.com/neulmc/MicroAl-Dataset) met those minimum
conditions. Its heat-treated optical-metallography example supplies a
256x256-pixel Si-particle mask and states a scale of 0.1 micrometres per pixel.
The source permits academic research but prohibits unauthorised redistribution
and commercial use. Therefore the downloaded pixels remain outside this
repository; the local report stores only declared metadata, hashes and derived
measurements.

Before inspecting the output I fixed the whole field, black Si-particle pixels
as foreground, white matrix pixels as background, 2x and 4x reductions, and
ties to background. I did not invent a decision tolerance. The input hash was
locked to `31e3bb1127792cc70d92e377dde280b0311dbae84d0f032f06d59394d1139cba`.

| Representation | Mean half-height length | Relative to native | Si area fraction | Smaller directional length in coarse pixels | Screen |
|---|---:|---:|---:|---:|---|
| Native, 0.1 um/pixel | 0.832499 um | 1.000000 | 0.298538 | 7.97 | no flag |
| 2x, 0.2 um/pixel | 0.832193 um | 0.999634 | 0.287415 | 3.97 | no flag |
| 4x, 0.4 um/pixel | 0.851150 um | 1.022404 | 0.287842 | 1.94 | flagged |

This is an informative pass rather than proof of accuracy. The mean length is
nearly unchanged at 2x and is 2.24% higher at 4x. However, the 4x result spans
fewer than two pixels in its weaker direction, so the report warns against
treating its small percentage change as well-resolved microstructure. The
apparent Si area fraction falls by about 1.11 percentage points at 2x. Exact
50:50 blocks account for 2.26% of the 2x blocks, showing that the predeclared
tie rule has a visible geometrical consequence even where the mean length is
stable.

The public sample does not give the alloy designation, heat-treatment time or
temperature, section orientation, specimen sampling plan, or the quality class
of this particular annotation. It is one field, not an independent-specimen
study. It therefore tests the audit's behaviour on a second real materials mask
and exposes a resolution warning; it does not validate the supplied
segmentation, a kinetic law or a predictive alloy model.

Local output: `output/microal_mask_audit_2026-09-22_v1/`.

## Complete 81-field FeM test

The [FeM iron-ore dataset](https://doi.org/10.5281/zenodo.5014700) provided a
larger and better-resolved test: 81 registered reflected-light fields with
producer SEM-thresholded ore/resin reference masks and a published calibration
of 1.05 micrometres per pixel. The archive matched its published MD5 and every
mask/image pair, dimension and binary label was checked before analysis.

All 81 masks were included using one fixed 756x996 field. With exact block ties
assigned to background, the median length change was -0.898% at 2x and +1.610%
at 4x. No field was unresolved or triggered the three-pixel warning. However,
an explicitly post-hoc opposite-tie sensitivity changed the 2x median to
+1.925% and the 4x median to +2.530%. The sign of the small 2x bias therefore
depends on the declared handling of exactly balanced blocks.

Three predeclared fields at all three resolutions were recomputed directly in
real space; all nine checks matched the FFT calculation to `1e-10`. The full
method, quartiles, limitations and hashes are recorded in
[the FeM audit](FEM_PUBLIC_MASK_AUDIT_2026-09-22.md). The fields come from one
mounted sample and are not independent specimens. The Zenodo record is open
but displays no licence identifier, so raw pixels remain local.

Local primary output: `output/fem_mask_audit_2026-09-22_v2/`.

## What remains unvalidated

- The producer segmentation is treated as a reference, not physical truth.
- Numerical downsampling is not the same as re-imaging a specimen with a
  different microscope or acquisition setting.
- No independent specimens quantify sampling variability.
- No materials researcher has yet declared a decision tolerance or confirmed
  that this correlation length is useful for their work.
- No paired real images at independently measured resolutions have been tested.
- The tool does not fit an experimental ageing exponent or validate the 2D
  Kawasaki model as a predictive alloy model.

## Appropriate reviewer question

> For one microstructural feature you measure in practice, would this bounded
> native/2x/4x sensitivity report reveal a useful failure mode? If so, what
> phase definition, field, descriptor and tolerance should be fixed before a
> small owner-led pilot?
