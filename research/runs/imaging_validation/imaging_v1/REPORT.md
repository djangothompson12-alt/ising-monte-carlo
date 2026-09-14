# Controlled observation results

fresh-seed repeat; 8 / 8 replicas.
Full-image covariance is a reference, not a true radius. No result is corrected toward 1/3.
Each comparison uses its own common resolved mask; compare actual times, not just nominal labels.
All crops within a replica are averaged only if every crop resolves. Bootstrap units are whole replicas.
These transforms model observation sensitivity, not a calibrated instrument. Independent repeat is only four replicas/composition.

## Primary window, L=128

| c | condition | alpha | delta vs full [95% paired interval] | retained points | actual times |
|---|---|---|---|---|---|
| 0.15 | full | 0.247 | 0.000 [0.000, 0.000] | 12 | 1224–20000 |
| 0.15 | bin2 | 0.237 | -0.010 [-0.014, -0.007] | 12 | 1224–20000 |
| 0.15 | bin4 | 0.174 | -0.073 [-0.088, -0.060] | 12 | 1224–20000 |
| 0.15 | blur1 | 0.241 | -0.006 [-0.013, -0.000] | 12 | 1224–20000 |
| 0.15 | blur2 | 0.244 | -0.003 [-0.027, 0.018] | 12 | 1224–20000 |
| 0.15 | blur1_threshold_minus02 | 0.230 | -0.017 [-0.023, -0.011] | 12 | 1224–20000 |
| 0.15 | blur1_threshold_plus02 | 0.254 | 0.007 [-0.000, 0.015] | 12 | 1224–20000 |
| 0.15 | crop96 | 0.251 | 0.004 [0.004, 0.006] | 12 | 1224–20000 |
| 0.15 | crop64 | 0.248 | 0.001 [-0.001, 0.005] | 12 | 1224–20000 |
| 0.15 | crop32 | 0.201 | -0.046 [-0.062, -0.034] | 12 | 1224–20000 |
| 0.15 | periodic_engine | 0.246 | -0.001 [-0.002, 0.001] | 12 | 1224–20000 |
| 0.5 | full | 0.243 | 0.000 [0.000, 0.000] | 12 | 1224–20000 |
| 0.5 | bin2 | 0.243 | 0.000 [-0.002, 0.002] | 12 | 1224–20000 |
| 0.5 | bin4 | 0.186 | -0.057 [-0.059, -0.056] | 12 | 1224–20000 |
| 0.5 | blur1 | 0.222 | -0.020 [-0.021, -0.019] | 12 | 1224–20000 |
| 0.5 | blur2 | 0.188 | -0.055 [-0.058, -0.052] | 12 | 1224–20000 |
| 0.5 | blur1_threshold_minus02 | 0.223 | -0.019 [-0.021, -0.018] | 12 | 1224–20000 |
| 0.5 | blur1_threshold_plus02 | 0.222 | -0.021 [-0.023, -0.019] | 12 | 1224–20000 |
| 0.5 | crop96 | 0.242 | -0.001 [-0.004, 0.003] | 12 | 1224–20000 |
| 0.5 | crop64 | 0.242 | -0.000 [-0.002, 0.003] | 12 | 1224–20000 |
| 0.5 | crop32 | 0.259 | 0.016 [-0.002, 0.038] | 12 | 1224–20000 |
| 0.5 | periodic_engine | 0.242 | -0.000 [-0.002, 0.002] | 12 | 1224–20000 |

All sizes/windows, missingness and ratios are in paired_fits.csv; raw individual crops are in observations.csv.
The box/window figure is descriptive: independently simulated sizes are not paired statistical controls.
Do not interpret agreement of estimators as proof of accuracy. No experimental images are included here.
