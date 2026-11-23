# Pixel check: does the 2× warning predict bias?

Data: the 16 held-out short-window trajectories in
`research/runs/growth_reliability_holdout_v1` (8 per composition, L=128,
0.65 Tc). Fit window 1,000–20,000 sweeps, 24 snapshots per fit. Images at
resolution k (1, 2, 4) are made with `research.imaging.observe(factor=k)`.

True bias at resolution k: n_k − n_1. Warning: n_2k − n_k, the change the
Pixel check reports when a user's images are coarsened a further 2×.

| k | Median smallest length (px) | True bias, median [range] | Warning, median |
|---|---:|---|---:|
| 1 | 1.61 | +0.000 | −0.008 |
| 2 | 0.90 | −0.008 [−0.018, −0.003] | −0.052 |
| 4 | 0.54 | −0.060 [−0.088, −0.045] | −0.142 |

With |warning| > 0.01 as the flag and |bias| > 0.01 as a real problem, over
48 cases: 22 biased, all 22 flagged (no misses); 26 not biased, 16 flagged.
Correlation between warning and bias for k > 1: 0.96. The warning is about
two to three times the real error.

Conclusion: a sensitive but unspecific screen. The tool's wording says so.
This is simulation evidence only; the threshold was not tuned on these data.
