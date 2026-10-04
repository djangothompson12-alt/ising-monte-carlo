# FeM public-mask resolution audit

**Status:** completed local public-data stress test on 22 September 2026.

**Source:** Gomes et al., FeM dataset version 1,
[DOI 10.5281/zenodo.5014700](https://doi.org/10.5281/zenodo.5014700).

## Why this dataset was selected

FeM provides 81 paired fields from a polished, epoxy-mounted itabiritic
iron-ore concentrate. The sample mainly contains hematite and quartz, with
minor magnetite and goethite. Each 999x756-pixel reflected-light image is
registered to an SEM image. The producer thresholded the SEM image to make a
binary reference in which ore is 0 and embedding resin is 255. The published
physical calibration is 1.05 micrometres per pixel.

This is a stronger software stress test than selecting one convenient field:
all 81 supplied masks were included. It is not an independent-specimen study,
because the fields come from one mounted sample. The masks are producer
references made by SEM thresholding, not direct physical truth.

The Zenodo record is publicly open and requests citation, but its licence field
does not display a licence identifier. The raw archive therefore remains local
and is not copied into this repository or embedded in the report.

## Frozen primary protocol

These choices were fixed before viewing the primary results:

- all 81 reference masks;
- ore value 0 as foreground and resin value 255 as background;
- the same near-centred ROI `[0, 756, 1, 997]` in every field;
- the ROI is the largest 756x996 field divisible by four without resampling;
- native, 2x and 4x digital mask representations;
- exact 50:50 blocks assigned to background;
- the published 1.05 micrometres-per-pixel calibration;
- no invented acceptable-error tolerance.

The downloaded archive matched the producer's published MD5,
`f1f2d29c449d12deb71b676f81b4ae78`. All 81 masks were single-plane, had the
published dimensions, contained only 0 and 255, and had a matching
reflected-light image.

## Primary results

Values below are medians across fields, with the interquartile range in
parentheses. They describe variation among fields from one specimen; they are
not confidence intervals for a material population.

| Representation | Median length, um | Median change from native | Median ore area fraction | Median fraction change | Median smaller directional length, pixels | Flagged fields |
|---|---:|---:|---:|---:|---:|---:|
| Native, 1.05 um/pixel | 19.3457 (18.4548–20.4771) | reference | 0.35693 | reference | 17.87 | 0/81 |
| 2x, 2.10 um/pixel | 19.1685 (18.2803–20.3680) | -0.898% (-1.089 to -0.581%) | 0.34848 | -0.857 percentage points | 8.89 | 0/81 |
| 4x, 4.20 um/pixel | 19.6639 (18.7644–20.7149) | +1.610% (+1.380 to +1.872%) | 0.35337 | -0.311 percentage points | 4.57 | 0/81 |

All 81 fields were resolved at every representation. With ties assigned to
background, all 81 2x lengths decreased, by 0.138% to 1.963%, while all 81 4x
lengths increased, by 0.722% to 2.808%. This non-monotonic result should not be
interpreted as a physical change: it is produced by re-representing the same
fixed masks.

Exact 50:50 blocks were not rare. Their median frequency was 1.755% at 2x and
0.812% at 4x. This motivated an explicitly post-hoc tie-rule sensitivity check.

## Post-hoc tie-rule sensitivity

The complete audit was repeated with only one change: exact 50:50 blocks were
assigned to ore instead of resin. This was run after viewing the primary result
and is therefore a sensitivity analysis, not a second preregistered result.

| Representation | Ties to background: median length change | Ties to ore: median length change | Ties to background: median fraction change | Ties to ore: median fraction change |
|---|---:|---:|---:|---:|
| 2x | -0.898% | +1.925% | -0.857 percentage points | +0.906 percentage points |
| 4x | +1.610% | +2.530% | -0.311 percentage points | +0.503 percentage points |

With ties assigned to ore, every field increased at both 2x and 4x. The sign of
the small 2x length bias therefore depends on the tie convention. This is the
main methodological result of the FeM test: when a majority filter is used,
the treatment of exactly balanced blocks must be fixed and reported. A stable
physical calibration alone does not remove this discrete operator choice.

## Independent numerical checks

The main estimator obtains finite, nonperiodic directional correlations by an
FFT calculation. For fields 001, 041 and 081 at all three resolutions, I
separately calculated each valid pixel-pair product directly in real space and
interpolated the first half-height crossing. All nine phase fractions and both
directional lengths matched the audit output to an absolute tolerance of
`1e-10`. This does not prove that correlation half-height is the best descriptor
for ore particles; it checks that the declared calculation was implemented
consistently.

The complete repository test suite passed 192 tests after adding the FeM replay
check.

## What this result does and does not show

It shows that the audit:

- processes a complete, physically calibrated public materials dataset;
- retains resolved measurements across all 81 fields at 4x reduction;
- exposes a small but consistent resolution-dependent length change;
- reveals that a tie convention can change the sign of that change;
- keeps phase-area fraction distinct from chemical composition.

It does not show that:

- digital downsampling reproduces a lower-resolution microscope acquisition;
- the SEM-thresholded masks are exact physical truth;
- 81 fields from one mounted sample are 81 independent material specimens;
- a 1–3% change is acceptable for a laboratory decision;
- the FeM result validates a Kawasaki growth exponent or an alloy prediction.

No pass/fail tolerance was supplied by a materials owner, so none was added
after seeing the result. The next validation step remains an owner-led pilot in
which the feature, descriptor, field and useful tolerance are agreed before the
audit is run.

## Reproducibility record

The checked replay is implemented in `research/replay_fem_mask_tool.py`.
Local, ignored outputs are in:

- `output/fem_mask_audit_2026-09-22_v2/` for the frozen primary protocol;
- `output/fem_mask_audit_2026-09-22_tie_foreground_sensitivity_v1/` for the
  explicitly post-hoc tie sensitivity.

The primary provenance file records the archive and source hashes, all input
mask hashes, exact ROI and labels, 243 field-level rows, aggregate quartiles and
the nine independent direct-correlation checks.
