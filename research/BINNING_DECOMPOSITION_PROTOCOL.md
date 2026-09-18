# Post-hoc decomposition of the 4× observation operator

Working analysis declaration, 17 September 2026. This follow-up was motivated
by the completed binning-plus-threshold result and therefore is exploratory,
not a pre-data registered hypothesis or an independent confirmation. It does
not rerun or modify the Monte Carlo dynamics.

## Bounded question

How much of the already reported 4×-binning-plus-threshold effective-exponent
shift appears at the greyscale block-average stage, and how much appears only
after converting that coarse image back to a binary mask? Does the convention
for exact zero block averages matter?

Analyse only the archived L=128, c=0.50 and c=0.15 trajectories in the
completed 64-run campaign (eight replicas per composition) and the fresh-seed
20,000-sweep repeat (four per composition). Keep the two campaigns separate;
their checkpoint grids differ. For each unchanged saved snapshot measure:

1. Full binary finite-image correlation length, pixel spacing one site.
2. 4×4 block-averaged *continuous* greyscale field, pixel spacing four sites.
3. That block average thresholded to +1 for values **greater than or equal to**
   zero, as in the earlier `bin4` study.
4. The same block average thresholded to +1 only for values **strictly greater
   than** zero, assigning exact ties to −1.

Use the same finite-field, non-wrapping connected-correlation half-height
length for all four fields; track apparent phase fraction and the fraction of
zero-valued coarse pixels. The greyscale field is a different observable, not
"pure resolution" independent of contrast/normalisation.

The primary slope window is nominally 1,000–20,000 sweeps; on the original
campaign also show 1,000–200,000 as a secondary sensitivity window. For each
composition and campaign use one jointly resolved time mask across all four
conditions and every replica. Require at least four points spanning fivefold
in time. Fit log of the **replica-mean length** against log sweeps. Resample
whole trajectories in paired bootstrap draws, never pixels or timepoints.
Report the actual retained time range, n, and treatment-minus-reference
slopes. The same mask makes the arithmetic decomposition of the total change
into greyscale-block and threshold steps exact for point estimates, but not a
unique physical causal decomposition.

Before interpretation, verify that the freshly recomputed full and
zero-ties-to-+1 lengths reproduce the earlier `imaging_v1/observations.csv`
for the same file and checkpoint. Include failures and unresolved values; do
not tune thresholds or choose a preferred tie rule to move a slope toward 1/3.

The result can support a narrower account of *this numerical observation
pipeline*. It cannot calibrate a microscope, identify which coarse mask is
physically right, isolate the one-third asymptote, or validate real alloy
ageing. Composition and mask morphology can change the balance between steps.
