# Controlled observation study v1

Specified 10 September 2026 before observing the new imaging-test outputs or
fresh-seed results. Existing pilot and overnight physics/estimator results have
already been inspected; analyses of those trajectories remain exploratory.
This local timestamped protocol is not an externally registered preregistration.

## Question and scope

Separate actual finite simulation size from finite observation window, and
quantify changes in measured growth caused by image resolution and segmentation.
Neither a new coarsening law nor experimental validation is assumed.

Existing data: overnight, c=.50/.15, L=32/64/96/128, eight replicas/group.
Independent repeat: imaging_validation.json, c=.50/.15, L=128, four NEW replicas
per composition, 20,000 sweeps, 40 requested checkpoints, seed 20260913.
The shorter repeat checks observation sensitivity over shared windows; it does
not confirm late-time behaviour out to 200,000 sweeps. Four replicas are modest.
Freeze these observation definitions before analysing the fresh data. No
selection of a preferred estimator or learned reliability classifier is planned.

## Observations

Primary image observable: the directional mean first 0.5 crossing of
pair-count-normalised, finite-window covariance divided by image variance.
Subtract the observed image mean. Sum only pairs inside the image; do not wrap
its edges. This is a separate image-analysis convention, NOT a change to either
engine's correlation or physical dynamics. Include the periodic full-image
engine threshold separately to expose the boundary/convention difference.
Local composition estimation is part of the crop effect, not pure geometry.

For L=128: full field; crop widths 96,64,32 at four fixed corner origins
(0,0),(0,L-w),(L-w,0),(L-w,L-w); these overlapping crops are NOT independent
replicas. Follow each fixed crop location through time. Average the four only
if every crop has resolved both directional lengths; retain NaNs otherwise.
Reference for crops: full L=128 finite-window observable at the same times.

For every full image: 2x and 4x block averaging with original-site pixel spacing
tracked, followed by threshold at 0; Gaussian blur sigma=1 and 2 original sites,
reflecting image-edge handling, followed by threshold at 0; segmentation
threshold sensitivity -0.2/+0.2 after sigma=1 blur. Input spins use -1/+1.
These are explicitly synthetic observation operators, NOT calibrated models
of a microscope or thermal fluctuations. Record changed apparent phase fraction.

Primary window: 1,000–20,000 sweeps. Secondary windows: 100–20,000 and,
for the overnight data only, 1,000–200,000. Use identical resolved checkpoints
for each paired comparison, requiring >=4 points spanning >=5x in time.
Record actual retained times and unresolved fractions. Resample entire replicas
500 times using identical indices for a treatment and its reference. Do not
resample crops or timepoints independently. A common mask fixed before
resampling does not include mask-selection uncertainty.

Report treatment-minus-reference effective slope, interval, and final available
matched length ratio. No 1/3 target, no post hoc removal of runs, no corrective
smoothing of engine trajectories. Compare true smaller-system full images
with crops only on explicitly matched time windows; different systems use
independent ensembles, so do not invent paired seeds across lattice sizes.

## Verification and claim boundaries

Check finite-window FFT correlation against brute-force pair products, no edge
wrapping, constant-image failure, sign/axis symmetry, block averaging and pixel
scale, invalid inputs, analytic sine wavelength, and exact paired no-effect
controls. Tests of image estimators establish defined numerical behaviour, not
their correspondence to a unique physical particle radius.

Known relevant prior art: Majumder & Das, Phys. Rev. E 84, 021110 (2011),
https://arxiv.org/abs/1101.4524. They already study early time, size, noise,
different length definitions and finite initial length. This study is NOT a
claim to discover those issues. Its intended output is a reproducible controlled
observation benchmark; originality and utility still need expert assessment.

Experimental application is separately gated on accessible licensed images,
physical scale/time metadata, phase identity and instrument consistency.
No image series is counted as experimental validation by this protocol.
