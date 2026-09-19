# Prospective follow-up: does fraction matching recover a growth measurement?

Declared after inspection of the earlier averaging/segmentation result and
the public 3D crop audit, but before calculating the new fraction-matched
control. This is exploratory secondary analysis, not a blind discovery or
an independently registered protocol. Original results remain unchanged.

## Bounded question

For the available 2D Kawasaki trajectories, how much finite-window growth
exponent bias remains after low-resolution binary segmentation is constrained
to match the native species-site fraction to the nearest attainable coarse
pixel count? How does this depend on resolution, composition and tie handling?
Do the same operators preserve static correlation lengths in supplied 3D
alloy phase masks? The latter is a measurement comparison, not kinetic validation.

## Frozen simulation inputs and controls

Use all 32 L=128 extension trajectories: 16 each at nominal c=.50 and .15,
Jx=Jy=1, T=.65 Tc. Use every saved snapshot. Never evolve processed states.
Convert native spins to a 0/1 phase indicator. At factors 2, 4 and 8 compare:

1. Native indicator, finite-image connected half-height length.
2. Disjoint block means (partial-volume indicator).
3. Fixed threshold >= .5 (ties to foreground), the previous convention.
4. Fraction-matched binary mask: choose the K highest block averages, where
   K=floor(Ncoarse * native_fraction + .5). This is an oracle control because
   the reference fraction is known. It is not a new segmentation algorithm.

At the boundary rank, equal averages are resolved by a seeded random ordering
of coordinates. Fix that ordering through time for each shape and seed.
Use seeds 110, 211, 312, 413 and 514; report all five, never select the best.
Only boundary ties use randomness. Nearest-integer matching permits an
absolute fraction error up to 0.5/Ncoarse; record the actual residual. A claim
of exact conservation is prohibited when that residual is nonzero.

## Fitting and uncertainty

Primary comparison: factor 4, nominal 1,000-20,000 sweeps, matched minus native
alpha at each composition. Secondary factors 2 and 8 and the longer
1,000-200,000 window are sensitivity checks, not rescue analyses.
Within each factor and window use checkpoints where all directions resolve
for every operator, every tie seed and all 16 trajectories. Retain missing
values and report the retained range/count. If fewer than four points or less
than a fivefold time span survive, leave the fit unresolved.

Average the five tie-specific lengths within each trajectory before forming
its ensemble mean. Ties are not independent physical replicas. Fit log of
ensemble mean length against log time. Use 500 paired complete-trajectory
bootstrap resamples, seed 912, for stage-minus-native differences. Also fit
each tie choice on the same mask and report their range as algorithmic
sensitivity, not a confidence interval. Report both |delta_matched| and
|delta_fixed|; improvement in closeness is not exact recovery or causality.

## Real-data external companion

Reuse the four exact 256-cube Al-Ge boxes from the existing v3 volume audit.
Do not relocate or select a more favourable region. Apply the same factors
and controls in 3D, with 0.06 micrometre native spacing. Match each box's
native Ge volume fraction separately; do not force constancy between scans.
Retain unresolved/empty phases. Each processed length is compared with its
own native box. Report length ratio and absolute phase-fraction error side
by side; pool neither dimensions nor scans into a kinetic fit or confidence
interval. The original mask is the reference, not independently known truth.

## Contribution and stop rules

Equal phase fractions do not determine geometry; that is established, not
the proposed discovery. The possible small contribution is a reproducible
dynamic benchmark quantifying when a fraction-matched observation control
does and does not recover a finite-window growth estimate, alongside a
bounded real-mask failure test. If matching recovers the measured exponent,
report that; if it does not, quantify the residual and tie dependence.
Never tune operators to 1/3 or fit an experimental alloy exponent from these
sparse, unregistered boxes. Novelty remains subject to expert review.
