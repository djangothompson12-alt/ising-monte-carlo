# Results: width-128 resolution re-analysis

18 October 2026. AI-run analysis of existing archives under the pre-declared
[PROTOCOL.md](PROTOCOL.md) (SHA-256 `ebcd809b…3464`, written before any coarse
measurement was computed). No simulations were run and nothing in the
repository was edited. Full numbers: [bin_slopes.csv](bin_slopes.csv),
[verdicts.json](verdicts.json). Re-run (about 10 s) from the repo root with
`python3 review/resolution_reanalysis_2026-10-18/l128_resolution_reanalysis/reanalyse.py`.

## Primary result (fraction-matched, factor 4)

Exponent difference (processed minus native) by how many coarse pixels the
native structure spans. Tolerance is ±0.02.

| Native size (coarse px) | 50:50 | 15:85 |
|---|---|---|
| below 1 | −0.051 [−0.053, −0.049] biased | −0.066 [−0.069, −0.063] biased |
| 1 to 2 | −0.012 [−0.015, −0.009] **inside tolerance** | −0.017 [−0.020, −0.013] undecided |
| 2 to 3 | not estimable as declared (one unresolved length) | too few checkpoints |
| 3 or more | not reached by 1M sweeps | not reached |

Pre-declared verdict: success regime found at 50:50, inconclusive at 15:85,
so the study-level primary verdict is **not established**.

Cross-check: the sub-pixel 50:50 value (−0.051) agrees with the separate
fresh 16-trajectory cohort (−0.0505).

## What the data say in plain terms

1. **The bias shrinks by about three-quarters once the structure spans one or
   two coarse pixels**, in both compositions, for both matched and fixed
   thresholds. This is the main new finding.
2. **At factor 2, matched fraction stays inside tolerance in every bin from
   one coarse pixel upward**, at both compositions (largest |shift| 0.009).
3. **The grey-image result from the review does not generalise.** Un-thresholded
   block means kept the 50:50 slope only while sub-pixel (−0.007). Once resolved
   they are biased (−0.046 at 1–2 px, factor 4; −0.037 to −0.018 at factor 2).
   So "binarisation drives the shift" is true in the sub-pixel window only;
   the earlier review's wording needs this limit.
4. **Matched and fixed thresholds are close at factor 4** (50:50, 1–2 px:
   −0.012 vs −0.014), again showing fraction error is not the main driver.

## Limits

- **Resolution and time are confounded.** Larger coarse-pixel sizes only occur
  later, and the native local exponent itself rises (50:50: 0.24 over 1k–30k,
  0.30 over 36k–300k, 0.33 over 350k–1M; 15:85: 0.24, 0.28, 0.29). A partial
  check: over the same 50:50 times (36k–294k), factor 2 (2–5 coarse px) gives
  about −0.004 while factor 4 (1–2 px) gives −0.012, so coarser images are
  more biased at the same time.
- The 50:50 factor-4 [2,3) bin is undefined because one trajectory
  (rep000, 839,558 sweeps) has no half-height crossing in the integrated and
  matched images. A **post-hoc** run dropping only that measurement
  ([posthoc_unresolved_sensitivity.txt](posthoc_unresolved_sensitivity.txt))
  gives −0.020 [−0.062, 0.000]: too noisy to decide. It is not a primary result.
- Late native lengths reach 9% (50:50) and 7% (15:85) of the box.
- Only grid origin (0,0) and one observable (half-height) were used; earlier
  work showed those choices can move shifts more than these intervals.
- 16 trajectories per composition; bootstrap covers trajectory sampling only.
- The bin rule cannot label a stage that is fine everywhere (for example factor 2
  matched) as "success", because it requires a biased small bin first. Those
  rows read "inconclusive" in verdicts.json even though every bin is inside
  tolerance.

## What this changes

A one-line rule now has some support in these data: **below about one coarse
pixel per structure the exponent shift is −0.05 to −0.07; at one to two pixels
it falls to about −0.01 to −0.02.** Whether it reaches zero by three pixels needs
longer or larger runs, which is the costly experiment and should only be
designed if a specialist thinks the question is worth it.
