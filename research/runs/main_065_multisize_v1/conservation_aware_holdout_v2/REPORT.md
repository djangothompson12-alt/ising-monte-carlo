# Conservation-aware observation audit

This is a transparent new-seed mechanism audit designed after the broad image effect was known.
It separates mean-preserving pixel integration from composition-changing binary segmentation.
It is not a microscope calibration, an alloy validation, a new growth law or a blind novelty claim.

The segmentation-stage point estimate was negative at both compositions, consistent in direction with the earlier selected effect; this is not a blind discovery.

| c | Window | Comparison | Reference alpha | Treatment alpha | Delta alpha [95% interval] | Crosses zero? | Points | Actual range |
|---:|---|---|---:|---:|---|---|---:|---|
| 0.50 | 1000-20000 | integrated-minus-native | 0.234 | 0.232 | -0.001 [-0.003, 0.001] | yes | 17 | 1091-17913 |
| 0.50 | 1000-20000 | segmented-minus-integrated | 0.232 | 0.178 | -0.054 [-0.056, -0.052] | no | 17 | 1091-17913 |
| 0.50 | 1000-20000 | segmented-minus-native | 0.234 | 0.178 | -0.056 [-0.059, -0.053] | no | 17 | 1091-17913 |
| 0.50 | 1000-200000 | integrated-minus-native | 0.256 | 0.232 | -0.024 [-0.025, -0.023] | no | 30 | 1091-173983 |
| 0.50 | 1000-200000 | segmented-minus-integrated | 0.232 | 0.221 | -0.012 [-0.013, -0.011] | no | 30 | 1091-173983 |
| 0.50 | 1000-200000 | segmented-minus-native | 0.256 | 0.221 | -0.036 [-0.037, -0.035] | no | 30 | 1091-173983 |
| 0.15 | 1000-20000 | integrated-minus-native | 0.232 | 0.202 | -0.030 [-0.034, -0.026] | no | 17 | 1091-17913 |
| 0.15 | 1000-20000 | segmented-minus-integrated | 0.202 | 0.158 | -0.044 [-0.047, -0.041] | no | 17 | 1091-17913 |
| 0.15 | 1000-20000 | segmented-minus-native | 0.232 | 0.158 | -0.074 [-0.077, -0.069] | no | 17 | 1091-17913 |
| 0.15 | 1000-200000 | integrated-minus-native | 0.251 | 0.213 | -0.038 [-0.039, -0.036] | no | 30 | 1091-173983 |
| 0.15 | 1000-200000 | segmented-minus-integrated | 0.213 | 0.201 | -0.012 [-0.014, -0.010] | no | 30 | 1091-173983 |
| 0.15 | 1000-200000 | segmented-minus-native | 0.251 | 0.201 | -0.050 [-0.052, -0.048] | no | 30 | 1091-173983 |

## Apparent conservation check

The integrated partial-volume field preserved the native fraction at every checkpoint.
The binary segmentation did not have that guarantee:

| c | Mean native +1 fraction | Mean integrated equivalent | Mean segmented +1 fraction | Mean segmented shift | Mean exact-tie fraction |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.500000 | 0.500000 | 0.529453 | +0.029453 | 0.059120 |
| 0.15 | 0.150024 | 0.150024 | 0.095844 | -0.054181 | 0.016179 |

All uncertainty intervals resample complete paired trajectories. The common resolved-time mask
is stricter than a separate fit for each operator, so the alphas here need not match other tables.
The broad observation that image processing affects measured kinetics predates this project.
