# Bounded observation/observable sensitivity appendix

AI-assisted exploratory reanalysis planned on 26 September 2026. The same
fresh-cohort data and its original fraction-matching effect are already known.
This is NOT a new holdout, external preregistration, new dynamics experiment,
or a reproduction of Majumder and Das. Do not replace the existing primary
question or choose methods because they give large differences.

## Fixed scope

Use all 16 L=128 archives in `research/runs/growth_reliability_holdout_v1`:
eight per nominal +1 fraction c=.50/.15, Jx=Jy=1, T=.65 Tc. Reuse every saved
snapshot in [1000,20000] post-quench sweeps: 24 available times, 1119–20000.
No new dynamics or new seeds. Check original input hashes before and after.

Three binary observation operators:

1. Native 0/1 image converted from the saved -1/+1 lattice.
2. Origin-zero disjoint 4x4 means, then nearest-count fraction matching with
   the original tie priorities 110,211,312,413,514. Retain all outcomes and
   average their measured lengths within each trajectory/time.
3. Exactly ONE simultaneous majority pass at native resolution. Each site's
   output is the majority of itself and its four nearest neighbours. Reuse
   periodic neighbours because the underlying simulation is periodic. This
   is observation only and can change the observed species fraction. Never
   feed its result into the engine. Never recommend wrapped real-image filtering.

Two measurements on each operator's result:

- The existing normalized finite-image directional covariance half-height,
  averaged over axes. The field's own mean and variance are used. Measurement
  never joins opposite edges. Spacing is 1 site natively and after majority,
  and 4 sites on the matched 32x32 grid.
- The number-weighted mean complete +1-species chord, pooled over horizontal
  and vertical lines. A chord must be bounded by 0 pixels at both ends within
  its line. Discard but count every foreground run touching an image border;
  a uniform foreground line counts as ONE censored run. Require at least one
  complete foreground chord on EACH axis, otherwise mark the pooled value
  unresolved. Record directional means, counts and censoring fractions.

This phase-specific chord is not a droplet radius, unbiased size estimator,
or exact observable replica from the paper. Removing boundary-touching runs
favours shorter chords; its bias can change with time. At c=.15 the measured
species is the minority; at c=.5 its label is arbitrary. The pooled all-phase
periodic chord would largely duplicate the inverse-interface proxy already
studied, so it is not being added as another supposedly independent measure.

## Inference and reporting

For each composition use ONE common time mask resolved and positive in
both measurements, every operator, every trajectory and every matched tie.
Record attrition; require >=4 points spanning >=5-fold time. No fallback time
window or post-result parameter change. Original primary estimates remain
archived even if this stricter mask shortens the new comparison.

Fit log ensemble-mean length against log sweeps by ordinary least squares.
Bootstrap 1000 draws of complete trajectories, seed 912; use the same draw
indices for all operators and observables. Average tie lengths within a
trajectory, not trajectories across operators and not as extra replicates.

Retain all nine planned contrasts for EACH composition:

1. Matched-minus-native and majority-minus-native within each of the two
   measurements (four contrasts).
2. Chord-minus-half-height fitted exponent under each operator (three).
3. For each processed operator, its shift in the chord exponent minus its
   shift in the half-height exponent (two interactions).

Report point estimates and paired percentile 95% intervals, all failures and
composition/censoring histories. These are descriptive, correlated sensitivity
contrasts; intervals are not adjusted for multiple comparisons and are not
universal error bars. They quantify run resampling, not systematic image bias.
No arbitrary threshold will be selected to make the differences look large.

The original factor-four half-height values/intervals must be recovered on
their original common time mask. Check this separately from the new global
mask. Test chord counting, units, boundary handling, immutability, simultaneous
majority and known power-law slope differences on synthetic data before run.
Record script/dependency/protocol hashes before measurement and after.

Keep the current two-page reviewer brief and evidence pack unchanged. This is
a supporting exploratory appendix. Results showing agreement or a smaller
effect are useful and must receive the same visibility as large differences.

## Context, not a novelty claim

- Majumder and Das (2010), https://arxiv.org/abs/1001.3985, describe a local
  majority-spin rule and a first moment of interface-to-interface distances.
  Exact pass count and our finite foreground-only censoring are not claimed
  to reproduce their method.
- Ledesma-Alonso et al. (2018), https://arxiv.org/abs/1712.03183, establish
  resolution sensitivity of microstructure descriptors. This appendix tests
  a specific existing finite-window inference, not new resolution physics.
