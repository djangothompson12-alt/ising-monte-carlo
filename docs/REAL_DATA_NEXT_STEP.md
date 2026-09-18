# A real microstructure comparison that can actually be reviewed

Working intake brief, updated 18 September 2026. No company data have been
received or analysed. The original five Al–Ge tomography slices were an
image-quality feasibility case only. A later fixed-plane test used four public
Al–Ge tomography stacks (15, 105, 195 and 315 minutes) with the same 44 slice
indices at each time. It found that the proposed image measurement can fail on
some planes and can change between times, but it still does not establish a
coarsening law: these are correlated slices of one specimen, the segmented Ge
phase includes distinct lamellar and precipitate features, and the initial
cast structure and reconstruction/registration choices matter. See
`docs/ALGE_REAL_IMAGE_AUDIT_2026-09-18.md` and
`research/ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md` for the exact result
and limits.

## The narrow contribution to propose

For an approved binary or two-phase ageing image series, test whether the
reported characteristic domain length and any fitted finite-window growth
slope are stable across a **predeclared** range of reasonable phase-segmentation
choices. The comparison with 2D Kawasaki snapshots concerns observation and
morphology measurements. It does not turn Monte Carlo sweeps into hours or
validate an alloy-strength prediction.

## Minimum intake questions for a data owner or microscopy specialist

1. May these images and derived measurements be used, discussed and, if
   applicable, redistributed? Record written permission or a public licence.
2. What material, composition convention and ageing temperatures are involved?
3. Which phase is foreground, and how is that identity known (contrast,
   chemistry map, expert annotation or another measurement)?
4. Are there at least three ageing times, with time and pixel/voxel calibration
   for **every** image? Are times measured from the same processing step?
5. Are the images registered views of the same specimen/volume, or independent
   specimens? How many independent specimens exist at each time?
6. Did microscope settings, staining/contrast, reconstruction or spatial
   resolution change? Supply the instrument/reconstruction record for each.
7. What specimen-interior region is suitable, and how should edges, pores and
   background be excluded? An expert should approve this ROI rule before fits.
8. Which segmentation thresholds or phase masks are technically plausible,
   and why? Preserve all declared candidates, including failed ones.

The companion machine-readable form is
`research/real_data_intake.template.json`. After a specialist fills it, use
`research/segmentation_sensitivity.py` on the approved image manifest. That
script retains every supplied threshold and phase fraction; it deliberately
does not fit an experimental exponent automatically. A slope is considered
only if the same observable, specimen design and time units are defensible at
all stages, with uncertainty assessed across **independent specimens**, not
adjacent slices or arbitrary image crops.

## Decision before any kinetics claim

- **Suitable for a measured ageing trend:** consistent scale, contrast and
  phase identification; explicit time and sampling design; defensible ROIs;
  relevant independent specimens or a registered longitudinal design.
- **Suitable only for a feasibility/audit note:** useful original images but
  unresolved registration, metadata or phase-labelling questions. This is the
  current status of the Al–Ge work, including the later four-stack test.
- **Do not measure:** uncertain permission, missing ageing times or physical
  scales, or an unidentifiable foreground phase.

An engineer or academic can make a meaningful contribution by checking the
phase definition and ROI, identifying known imaging artefacts, and explaining
whether the reported sensitivity would affect their actual research decision.
Record their comments and every resulting revision. A conversation alone is
not an endorsement or deployment.

### A concise request the student may adapt (not sent)

“I have been testing how much a measured coarsening rate changes when the same
two-phase microstructure is segmented or observed at different resolutions.
Would you know of a non-confidential ageing image series with scale and time
metadata where this would be a useful measurement check? I would first ask
someone who understands the images to review my phase and region choices. My
Ising model is a simplified reference for the analysis, not a prediction of
your material.”
