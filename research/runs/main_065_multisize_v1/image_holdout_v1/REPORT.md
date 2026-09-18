# Fixed image-operator holdout

Read the protocol and paired_fits.csv before interpreting this figure.
This was specified after an earlier observed effect; new seeds test directional repetition, not novelty or a physical growth law.
All 128 dynamics trajectories were complete before any extension image was measured here.
The bootstrap resamples whole paired trajectories. It does not include fitting-window or model uncertainty.

Primary point estimates are negative at both compositions: consistent in direction with the earlier selected effect, not blind confirmation.
This sign rule uses the two 1,000–20,000-sweep point estimates only. A percentile interval crossing zero is reported as such, and the secondary window cannot rescue a failed primary test.

| Composition | Nominal window | Actual window | Points | Native α | Binned α | Δα [95% interval] | Interval crosses zero? | Native +1 fraction | Binned +1 fraction | Fraction shift | Status |
|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---|
| 0.5 | 1000–20000 | 1091–17913 | 17 | 0.234 | 0.178 | -0.056 [-0.059, -0.053] | no | 0.5000 | 0.5214 | +0.0214 | fit resolved |
| 0.5 | 1000–200000 | 1091–173983 | 30 | 0.256 | 0.221 | -0.036 [-0.037, -0.035] | no | 0.5000 | 0.5171 | +0.0171 | fit resolved |
| 0.15 | 1000–20000 | 1091–17913 | 17 | 0.232 | 0.158 | -0.074 [-0.077, -0.069] | no | 0.1500 | 0.1290 | -0.0211 | fit resolved |
| 0.15 | 1000–200000 | 1091–173983 | 30 | 0.251 | 0.201 | -0.050 [-0.052, -0.048] | no | 0.1500 | 0.1356 | -0.0144 | fit resolved |

Unresolved directional length values across every saved checkpoint are retained in per_replica_checkpoint.csv; the counts in paired_fits.csv are over the full trajectory, not just one fit window. Fraction means above use each row's fixed shared-resolved time mask.
The tie-to-+1 threshold may change apparent composition; no physical phase fraction or microscope correction is inferred.
