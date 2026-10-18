# Pre-declared protocol: does the processing bias fade once structures are resolved?

Written 18 October 2026 by an AI assistant, BEFORE any coarse-grained
measurement of these archives was computed in this session. Django has not
yet written his own prediction; this protocol is not a student-authored
pre-registration. Its SHA-256 is recorded in the results folder.

Already known before writing (from the 18 October review and the earlier
fraction-matched benchmark, which used this campaign's 1k-174k window): the
fourfold lengths in the short fresh window are sub-pixel, and over 1k-174k
the fourfold integrated shift at 50:50 was about -0.024. Nothing is known yet
about the shift *as a function of resolution* at late times.

## Question

For the existing 0.65 Tc, L=128, one-million-sweep Model B trajectories, does
the local exponent difference between a processed image and the native image
move inside the project's declared tolerance once the native structure spans
several coarse pixels?

## Data (no new simulations)

`research/runs/main_065_multisize_v1/c{0,1}_L128_rep000-015.npz` at commit
1a405b3: 16 trajectories each for c=0.5 (c0) and c=0.15 (c1), all saved
checkpoints with t >= 1000 sweeps. Foreground = up spins.

## Measurements (unchanged project operators)

- Length: `research.imaging.image_length` (finite-window connected
  correlation, first 0.5 crossing, mean of x and y), in native site units.
- Factors 2 and 4. Stages: `integrated` (block mean, grey, no threshold),
  `fixed` (block mean >= 0.5), `matched` (`research.fraction_matching.match_fraction`
  to the native fraction, mean length over the five `TIE_SEEDS`).
- Resolution coordinate: n(t) = ensemble-mean native length / factor
  (native structure size in coarse pixels).

## Estimand

D(t) = ln( mean_i L_proc,i(t) / mean_i L_nat,i(t) ), ratio of ensemble means.
The local exponent difference in a bin is the OLS slope of D against ln t over
the checkpoints whose n(t) falls in that bin. This equals (processed exponent
- native exponent) in that window.

Bins in n (coarse pixels): [0,1), [1,2), [2,3), [3,5), [5,inf).
A bin is estimable only if it holds >= 5 checkpoints spanning at least a factor
of 2 in t; otherwise it is reported as "not estimable". Bins are fixed and
will not be merged or moved after results are seen.

Uncertainty: 2000 bootstrap resamples of whole trajectories (paired across
stages; bins re-assigned from each resample's own native mean), 95% percentile
interval, RNG seed 20261018. This covers trajectory sampling only.

Tolerance: |difference| <= 0.02, the project's previously declared benchmark
tolerance (`research/GROWTH_RELIABILITY_PROTOCOL_2026-09-19.md`).

## Decision rule (primary: matched stage; applied per composition and factor)

- **PRESERVED** in a bin: the whole 95% interval lies inside [-0.02, 0.02].
- **BIASED** in a bin: the whole interval lies outside that band.
- **UNDECIDED**: anything else.

Overall verdict per composition/factor:
- "Success regime found" if the largest estimable bin is PRESERVED and the
  [0,1) or [1,2) bin (whichever is estimable first) is BIASED.
- "No success regime in this data" if the largest estimable bin is BIASED.
- "Inconclusive" otherwise, including when only one bin is estimable.

The study-level conclusion is "success regime found" only if it holds for
both compositions at factor 4 (the case the brief is about). Factor 2,
`fixed` and `integrated` are secondary, reported in full, and cannot rescue a
failed primary verdict.

## Caveats declared in advance

- Late-time native lengths approach ~0.1 of the box. Finite-size effects act
  on native and processed images alike, but may still change both.
- The native length is itself only a few sites early on.
- Systematic choices (observable, tie rule, grid origin) were shown earlier to
  move shifts by more than the bootstrap interval. Only the grid origin at
  (0,0) is used here.
- 16 trajectories per composition; bootstrap percentile intervals may
  undercover somewhat.
