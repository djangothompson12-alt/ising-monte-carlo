# Controlled observation results

exploratory existing trajectories; 64 / 64 replicas.
Full-image covariance is a reference, not a true radius. No result is corrected toward 1/3.
Each comparison uses its own common resolved mask; compare actual times, not just nominal labels.
All crops within a replica are averaged only if every crop resolves. Bootstrap units are whole replicas.
These transforms model observation sensitivity, not a calibrated instrument. Independent repeat is only four replicas/composition.

## Primary window, L=128

| c | condition | alpha | delta vs full [95% paired interval] | retained points | actual times |
|---|---|---|---|---|---|
| 0.15 | full | 0.231 | 0.000 [0.000, 0.000] | 16 | 1069–19557 |
| 0.15 | bin2 | 0.220 | -0.011 [-0.014, -0.007] | 16 | 1069–19557 |
| 0.15 | bin4 | 0.159 | -0.072 [-0.077, -0.068] | 16 | 1069–19557 |
| 0.15 | blur1 | 0.221 | -0.011 [-0.013, -0.008] | 16 | 1069–19557 |
| 0.15 | blur2 | 0.230 | -0.001 [-0.010, 0.007] | 16 | 1069–19557 |
| 0.15 | blur1_threshold_minus02 | 0.212 | -0.019 [-0.021, -0.017] | 16 | 1069–19557 |
| 0.15 | blur1_threshold_plus02 | 0.235 | 0.003 [-0.000, 0.007] | 16 | 1069–19557 |
| 0.15 | crop96 | 0.234 | 0.003 [-0.003, 0.009] | 16 | 1069–19557 |
| 0.15 | crop64 | 0.231 | -0.000 [-0.004, 0.004] | 16 | 1069–19557 |
| 0.15 | crop32 | 0.227 | -0.004 [-0.028, 0.019] | 16 | 1069–19557 |
| 0.15 | periodic_engine | 0.235 | 0.004 [0.001, 0.006] | 16 | 1069–19557 |
| 0.5 | full | 0.236 | 0.000 [0.000, 0.000] | 16 | 1069–19557 |
| 0.5 | bin2 | 0.231 | -0.004 [-0.007, -0.002] | 16 | 1069–19557 |
| 0.5 | bin4 | 0.180 | -0.056 [-0.060, -0.052] | 16 | 1069–19557 |
| 0.5 | blur1 | 0.216 | -0.020 [-0.020, -0.019] | 16 | 1069–19557 |
| 0.5 | blur2 | 0.179 | -0.057 [-0.059, -0.054] | 16 | 1069–19557 |
| 0.5 | blur1_threshold_minus02 | 0.216 | -0.020 [-0.021, -0.018] | 16 | 1069–19557 |
| 0.5 | blur1_threshold_plus02 | 0.216 | -0.020 [-0.021, -0.018] | 16 | 1069–19557 |
| 0.5 | crop96 | 0.240 | 0.005 [0.001, 0.009] | 16 | 1069–19557 |
| 0.5 | crop64 | 0.237 | 0.002 [0.000, 0.003] | 16 | 1069–19557 |
| 0.5 | crop32 | 0.234 | -0.002 [-0.018, 0.018] | 16 | 1069–19557 |
| 0.5 | periodic_engine | 0.236 | 0.001 [-0.001, 0.002] | 16 | 1069–19557 |

All sizes/windows, missingness and ratios are in paired_fits.csv; raw individual crops are in observations.csv.
The box/window figure is descriptive: independently simulated sizes are not paired statistical controls.
Do not interpret agreement of estimators as proof of accuracy. No experimental images are included here.
