# Controlled geometry check (exploratory)

This design was written after seeing the Kawasaki measurement results, before
executing this geometry experiment. It is not a new holdout or a physics model.
Do not alter the frozen 19 September validation protocol or its outputs.

Use 256 by 256, exactly half-filled checkerboards of square width
4, 8, 16, 32 and 64 native pixels. These tile the periodic domain exactly.
For integer displacements 0 <= r <= width, the periodic directional normalized
covariance is 1 - 2r/width. Its half-height length and positive-lobe integral
are both width/4. Verify this formula against direct pair products, not just FFTs.
Assign artificial scale coordinates t = width^3; the analytic length has an
exact exponent of 1/3 by construction. These coordinates are NOT Monte Carlo
sweeps or experimental ageing times. Finite-window lengths can differ from
the periodic analytic values, especially for large squares.

Cross factors 2, 4, 8 with translations (0,0), (1,1), (2,2), (3,3).
Report clean patterns and a deliberately perturbed variant in which 1% of
each phase's sites are flipped in paired equal counts (seed 20260920+width).
The latter preserves fraction exactly; it is NOT an equilibrium thermal-noise
model. Translate the already constructed pattern. Translations move both the
block grid and finite measurement boundary, not either effect in isolation.

Measure native, integrated, threshold-at-0.5 and rank-matched images. Use the
existing five coordinate-priority seeds, averaging their *lengths* for the
matched treatment. Report finite half-height and positive-lobe measures.
Keep unresolved observations. A fit needs all five widths and all five ties
where applicable; do not trim a window until a fit works. Report fitted
differences relative to the finite native baseline, separately from analytic
1/3. No statistical confidence intervals: these are designed images, not
independent stochastic coarsening trajectories.

Also show the factor-8, width-4 clean aliasing example. Its integrated field
is identically 0.5, so it contains no contrast; a forced half-filled binary
output cannot recover the original boundaries. This is a known information-
loss example, not a proposed novel theorem or a model of microscope noise.

Checks: exact fraction; independent direct finite-pair correlation against
FFT for every clean width at origin zero; periodic analytic formula for both
axes; factor-one identity; no mutation of input; unresolved-flat handling;
source/protocol/output hashes; reproducible output; refuse overwriting.

Decision: these controls can expose sampling and estimator behaviour. They
cannot uniquely explain the Kawasaki effect, establish publication novelty,
or validate a real-material kinetic exponent. All cases will be retained.
