# A focused check before reducing a microstructure mask

Internal AI-assisted development record, 13 October 2026. Django still needs
to review the method and explanation. No outside pilot, endorsement or
laboratory adoption is recorded here.

## The specific job

An imaging researcher supplies a checked, two-label 2D mask, a physical pixel
spacing, a fixed field and the length measurement they want to compare.
The audit answers: how much does direct 2x or 4x block reduction change this
finite-field correlation half-height length, and does that exceed a tolerance
the owner specified beforehand?

This is a check of digital mask processing. The input is already segmented;
the output is compared with its native measurement. Physical pixel size is
assumed equal on both axes. The correlation length is an operational
descriptor, not a measured particle radius. Phase area fraction is recorded
as geometry and is not equated with chemical composition. No experimental
growth exponent is fitted. The main Kawasaki fraction-matching question and
its archived results retain their own study protocol.

## Changes made

The declared tie rule remains primary. For every image at both coarse
resolutions, the opposite exact 50:50 block-tie convention is also measured
on the same field. The report exposes a decision that depends on this choice;
it does not select the rule that gives the closest native length.

An owner can require agreement in the mean or in both directions separately.
The template now suggests both directions; older plans without that setting
retain the mean-only convention. This matters because opposite x/y changes
can cancel in a mean. Resolution warnings remain visible even if the chosen
tolerance is met. There is no automatic acceptance without an owner tolerance.

The report opens with a compact result and next-action table. Method, material
context and the complete primary table remain accessible in disclosure panels.
The two extra CSVs retain the complete comparison. Input and calculation
source hashes include the crossing code, and the output hashes cover all
four delivered files.

The binary-mask kernel checks FFT values near half height by recomputing
binary pair counts with integer arithmetic. It uses the existing first
descending bracket from >=0.5 to <0.5, with linear interpolation. The
1e-12 trigger is numerical, not a physical uncertainty. A separate correction
makes an exactly-on-boundary tolerance inclusive: e.g. 11 versus 10 is within
a declared 10% tolerance. Only eight float64 epsilons are allowed for numerical
roundoff. This does not account for segmentation or calibration uncertainty.

## Verification completed

The independent checker uses explicit centred pixel-pair products, exact
rational covariance values, its own block counts and rational interpolation.
It shares no averaging, covariance or crossing helper with the production
calculation. Hand-calculated checkerboards anchor the reference. The 18
synthetic fields include absent phases, one-direction-only structures,
anisotropic patterns, isolated pixels, circles and seeded random fields.
Three reduction factors, two tie rules and three scales give **324 numerical
comparisons**. The maximum absolute disagreement was
**2.6645352591003757e-15** in the tested arbitrary/scaled units. Missing
crossings remained missing. Tests also check label complement, transposition,
scale changes, the half-height arithmetic and tolerance decisions.

The restored FeM archive matched its published MD5 before extraction. The
new tool processed all **81 supplied fields**, producing 243 primary rows,
324 tie-sensitivity rows and 162 summary rows. Its native/declared-rule mean
lengths agreed with the earlier table to at most **1.7763568394002505e-14 um**.
The replay also passed the nine separately implemented direct-pair checks
for fields 001, 041 and 081. These are different calculations, not independent
human review. The original data remain in temporary storage.

| Reduction | Median mean-length change, ties to background | Median mean-length change, ties to foreground |
|---|---:|---:|
| 2x | -0.8984% | +1.9245% |
| 4x | +1.6096% | +2.5296% |

These reproduce the earlier tie sensitivity. The important use is making
that dependency visible automatically. No tolerance was supplied, so all
162 summary rows remain unclassified against an owner criterion. None
triggered the existing three-pixel warning. The 81 fields belong to one
mounted sample; they are not independent specimens. See the
[FeM source record](https://zenodo.org/records/5014700) and
[earlier full record](FEM_PUBLIC_MASK_AUDIT_2026-09-22.md).

The cached Al-Ge plane was also replayed with its fixed field and calibration.
Its under-resolution warnings remain visible at both coarse factors. This
is a replay of the existing single-plane example, not a new specimen or
validation of the microscope acquisition.

The repository suite passed **240 tests** after the numerical and decision
changes; the report was then simplified and its focused tests rerun.

## What existing tools already provide

The following primary documentation was checked on 13 October 2026. This is
a bounded comparison of relevant capabilities, not an exhaustive search of
all software or proof that no identical workflow exists.

| Existing work | Relevant capability | Consequence for this tool |
|---|---|---|
| [PoreSpy two-point correlation](https://porespy.org/autoapi/porespy/metrics/two_point_correlation.html) and [chord distributions](https://porespy.org/autoapi/porespy/metrics/chord_length_distribution.html) | Calibrated correlation and chord measurements; current correlation documentation describes nonperiodic pair normalisation and radial averaging. | Correlation measurement and finite-pair handling are established. Its radial phase probabilities are not numerically interchangeable with our globally centred directional covariance. |
| [ImageJ/Fiji MorphoLibJ](https://imagej.net/plugins/morpholibj) | Binary/label image geometry in 2D and 3D, with spatial calibration and many region descriptors. | Segmentation and particle measurement are already well served. Our small audit should complement an existing mask workflow. |
| [scikit-image measure](https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.euler_number) | Geometric measurements; its Euler-number documentation suggests a connectivity comparison as a resolution diagnostic. | Automated resolution warnings are not a new general idea. Our three-pixel heuristic is not a substitute for topology checks or a certified accuracy criterion. |
| [Ledesma-Alonso et al. (2018)](https://arxiv.org/abs/1712.03183) | Image decimation effects on statistical microstructure descriptors and an information-loss criterion. | Resolution dependence is prior art. We have not implemented or outperformed the full published descriptor criterion. |

The practical distinction is a ready-to-run, traceable comparison of a
specified mask reduction: primary and opposite tie conventions, directional
changes, a predeclared owner criterion and unresolved results in one report.
An experienced user could build that workflow using existing packages.
Its usefulness has to be established through saved effort or a better
measurement decision, rather than claiming a new correlation algorithm.

## The next outside test

Ask one materials-imaging practitioner whether this particular descriptor
and processing check support a decision they make. Before analysing their
permitted mask, record the phase definition, calibration, ROI, tie rule,
directional scope and useful tolerance. Send them every planned result and
ask whether the report changed a decision, confirmed an existing check,
added no value, or was misleading. Record the criticism and response.

Numerical verification is now stronger. Calibration accuracy, segmentation
accuracy, useful resolution limits, performance on actual lower-resolution
acquisitions, and value to a laboratory are still open. A specialist's request
for a different descriptor would justify the next change. Additional generic
features before that response are unlikely to improve this focused tool.

## Reproduce

```sh
python -m research.verify_mask_resolution_audit --output output/new-mask-verification
python -m research.make_mask_resolution_demo --output output/new-mask-demo
```

For permitted masks, follow [the tool instructions](MASK_RESOLUTION_AUDIT.md).
The latest local development outputs are under
`output/mask_audit_verification_2026-10-13_v3/`,
`output/mask_audit_demo_2026-10-13_v4/`,
`output/fem_mask_audit_2026-10-13_v3/` and
`output/alge_mask_audit_2026-10-13_v3/`.
