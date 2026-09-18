# Matched-time size comparison for the queued 0.65 Tc extension

Supplementary analysis addendum, 17 September 2026, before the queued
million-sweep extension has begun. The original 13 September protocol and its
five fixed fitting windows are unchanged. This addendum specifies an extra
descriptive output, not a revised fit chosen after seeing longer-run data.

For each composition and each shared saved sweep count, compare the primary
connected-correlation mean length at L=32, 64 and 96 separately with L=128
at the **same** sweep count. Report both length difference in lattice sites
and the ratio `mean_length(L) / mean_length(128)`. Keep every planned time in
the output, marking a comparison unresolved unless both groups have all 16
replicas resolved in both directions. Never fill missing lengths, carry a
previous value forward or use an inconsistent subset of replicas.

For each comparison, bootstrap the 16 whole trajectories in each lattice
size **independently** 500 times and report descriptive 2.5/97.5 percentiles
for the ratio. Trajectories, not timepoints, are the resampling unit. Plot
the ratio against matched sweeps with its interval; draw ratio one only as a
reference. Record source and raw-data hashes. The intervals do not include
model, observable, common-mask or multiple-time-scan uncertainty.

An L=128 comparison is not an infinite-system reference: it too may develop
finite-size effects. A ratio below one may reflect different transient
behaviour, unresolved measurement or finite box limitations. Do **not** call
the first point with an interval excluding one a physical onset time, and do
not transfer the roughly 4.5-million-sweep number from Majumder–Das to this
different temperature and measurement. A defensible onset criterion would
need a justified tolerance, persistence requirement and robustness checks
across all sizes; this addendum does not predeclare one. Its purpose is to
make the size comparison visible and criticisable rather than relying on
plot overlap or a fixed `length/L` threshold alone.
