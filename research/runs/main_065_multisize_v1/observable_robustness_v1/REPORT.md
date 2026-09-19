# Full-extension observable robustness audit

This is a post-result robustness audit under the frozen protocol, not a blind discovery test.
Every within-group fit uses one common checkpoint mask across all four observables and all 16 trajectories.
The estimators are different morphology proxies, not four calibrated measurements of one true radius.

## All paired fit rows

| c | L | estimator | nominal window | actual window | points | alpha [95%] | delta from half-height [95%] | unresolved values |
|---:|---:|---|---|---|---:|---|---|---:|
| 0.5 | 32 | threshold_05 | 1000–20000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 207 |
| 0.5 | 32 | positive_lobe | 1000–20000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 294 |
| 0.5 | 32 | spectral_moment | 1000–20000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | inverse_interface_proxy | 1000–20000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | threshold_05 | 1000–200000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 207 |
| 0.5 | 32 | positive_lobe | 1000–200000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 294 |
| 0.5 | 32 | spectral_moment | 1000–200000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | inverse_interface_proxy | 1000–200000 | 1091–2617 | 6 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | threshold_05 | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 207 |
| 0.5 | 32 | positive_lobe | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 294 |
| 0.5 | 32 | spectral_moment | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | inverse_interface_proxy | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | threshold_05 | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 207 |
| 0.5 | 32 | positive_lobe | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 294 |
| 0.5 | 32 | spectral_moment | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | inverse_interface_proxy | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | threshold_05 | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 207 |
| 0.5 | 32 | positive_lobe | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 294 |
| 0.5 | 32 | spectral_moment | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 32 | inverse_interface_proxy | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 64 | threshold_05 | 1000–20000 | 1091–10600 | 14 | 0.231 [0.220, 0.242] | 0.000 [0.000, 0.000] | 31 |
| 0.5 | 64 | positive_lobe | 1000–20000 | 1091–10600 | 14 | 0.227 [0.213, 0.245] | -0.003 [-0.009, 0.004] | 127 |
| 0.5 | 64 | spectral_moment | 1000–20000 | 1091–10600 | 14 | 0.147 [0.140, 0.154] | -0.084 [-0.089, -0.079] | 0 |
| 0.5 | 64 | inverse_interface_proxy | 1000–20000 | 1091–10600 | 14 | 0.188 [0.179, 0.198] | -0.042 [-0.048, -0.037] | 0 |
| 0.5 | 64 | threshold_05 | 1000–200000 | 1091–10600 | 14 | 0.231 [0.220, 0.242] | 0.000 [0.000, 0.000] | 31 |
| 0.5 | 64 | positive_lobe | 1000–200000 | 1091–10600 | 14 | 0.227 [0.213, 0.244] | -0.003 [-0.009, 0.004] | 127 |
| 0.5 | 64 | spectral_moment | 1000–200000 | 1091–10600 | 14 | 0.147 [0.140, 0.154] | -0.084 [-0.089, -0.079] | 0 |
| 0.5 | 64 | inverse_interface_proxy | 1000–200000 | 1091–10600 | 14 | 0.188 [0.178, 0.199] | -0.042 [-0.048, -0.037] | 0 |
| 0.5 | 64 | threshold_05 | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 31 |
| 0.5 | 64 | positive_lobe | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 127 |
| 0.5 | 64 | spectral_moment | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 64 | inverse_interface_proxy | 20000–200000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 64 | threshold_05 | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 31 |
| 0.5 | 64 | positive_lobe | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 127 |
| 0.5 | 64 | spectral_moment | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 64 | inverse_interface_proxy | 20000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 64 | threshold_05 | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 31 |
| 0.5 | 64 | positive_lobe | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 127 |
| 0.5 | 64 | spectral_moment | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 64 | inverse_interface_proxy | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 96 | threshold_05 | 1000–20000 | 1091–17913 | 17 | 0.234 [0.226, 0.242] | 0.000 [0.000, 0.000] | 1 |
| 0.5 | 96 | positive_lobe | 1000–20000 | 1091–17913 | 17 | 0.228 [0.220, 0.236] | -0.006 [-0.009, -0.003] | 30 |
| 0.5 | 96 | spectral_moment | 1000–20000 | 1091–17913 | 17 | 0.149 [0.144, 0.155] | -0.085 [-0.088, -0.082] | 0 |
| 0.5 | 96 | inverse_interface_proxy | 1000–20000 | 1091–17913 | 17 | 0.190 [0.183, 0.198] | -0.043 [-0.045, -0.042] | 0 |
| 0.5 | 96 | threshold_05 | 1000–200000 | 1091–173983 | 27 | 0.261 [0.253, 0.269] | 0.000 [0.000, 0.000] | 1 |
| 0.5 | 96 | positive_lobe | 1000–200000 | 1091–173983 | 27 | 0.254 [0.246, 0.264] | -0.006 [-0.009, -0.003] | 30 |
| 0.5 | 96 | spectral_moment | 1000–200000 | 1091–173983 | 27 | 0.168 [0.164, 0.173] | -0.093 [-0.097, -0.089] | 0 |
| 0.5 | 96 | inverse_interface_proxy | 1000–200000 | 1091–173983 | 27 | 0.206 [0.202, 0.211] | -0.054 [-0.058, -0.051] | 0 |
| 0.5 | 96 | threshold_05 | 20000–200000 | 21336–173983 | 10 | 0.297 [0.274, 0.319] | 0.000 [0.000, 0.000] | 1 |
| 0.5 | 96 | positive_lobe | 20000–200000 | 21336–173983 | 10 | 0.291 [0.264, 0.318] | -0.006 [-0.013, 0.004] | 30 |
| 0.5 | 96 | spectral_moment | 20000–200000 | 21336–173983 | 10 | 0.192 [0.177, 0.205] | -0.106 [-0.118, -0.095] | 0 |
| 0.5 | 96 | inverse_interface_proxy | 20000–200000 | 21336–173983 | 10 | 0.224 [0.207, 0.238] | -0.074 [-0.086, -0.063] | 0 |
| 0.5 | 96 | threshold_05 | 20000–1000000 | 21336–173983 | 10 | 0.297 [0.276, 0.319] | 0.000 [0.000, 0.000] | 1 |
| 0.5 | 96 | positive_lobe | 20000–1000000 | 21336–173983 | 10 | 0.291 [0.266, 0.317] | -0.006 [-0.013, 0.004] | 30 |
| 0.5 | 96 | spectral_moment | 20000–1000000 | 21336–173983 | 10 | 0.192 [0.178, 0.204] | -0.106 [-0.117, -0.095] | 0 |
| 0.5 | 96 | inverse_interface_proxy | 20000–1000000 | 21336–173983 | 10 | 0.224 [0.208, 0.238] | -0.074 [-0.085, -0.064] | 0 |
| 0.5 | 96 | threshold_05 | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 1 |
| 0.5 | 96 | positive_lobe | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 30 |
| 0.5 | 96 | spectral_moment | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 96 | inverse_interface_proxy | 200000–1000000 | unresolved | 0 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 128 | threshold_05 | 1000–20000 | 1091–17913 | 17 | 0.234 [0.229, 0.239] | 0.000 [0.000, 0.000] | 0 |
| 0.5 | 128 | positive_lobe | 1000–20000 | 1091–17913 | 17 | 0.225 [0.220, 0.230] | -0.009 [-0.010, -0.008] | 17 |
| 0.5 | 128 | spectral_moment | 1000–20000 | 1091–17913 | 17 | 0.150 [0.147, 0.153] | -0.084 [-0.086, -0.082] | 0 |
| 0.5 | 128 | inverse_interface_proxy | 1000–20000 | 1091–17913 | 17 | 0.191 [0.187, 0.195] | -0.043 [-0.045, -0.041] | 0 |
| 0.5 | 128 | threshold_05 | 1000–200000 | 1091–173983 | 30 | 0.256 [0.251, 0.262] | 0.000 [0.000, 0.000] | 0 |
| 0.5 | 128 | positive_lobe | 1000–200000 | 1091–173983 | 30 | 0.248 [0.243, 0.254] | -0.008 [-0.009, -0.007] | 17 |
| 0.5 | 128 | spectral_moment | 1000–200000 | 1091–173983 | 30 | 0.166 [0.163, 0.170] | -0.090 [-0.092, -0.088] | 0 |
| 0.5 | 128 | inverse_interface_proxy | 1000–200000 | 1091–173983 | 30 | 0.204 [0.201, 0.208] | -0.052 [-0.055, -0.050] | 0 |
| 0.5 | 128 | threshold_05 | 20000–200000 | 21336–173983 | 13 | 0.280 [0.262, 0.300] | 0.000 [0.000, 0.000] | 0 |
| 0.5 | 128 | positive_lobe | 20000–200000 | 21336–173983 | 13 | 0.276 [0.257, 0.297] | -0.005 [-0.008, -0.000] | 17 |
| 0.5 | 128 | spectral_moment | 20000–200000 | 21336–173983 | 13 | 0.183 [0.172, 0.196] | -0.097 [-0.106, -0.089] | 0 |
| 0.5 | 128 | inverse_interface_proxy | 20000–200000 | 21336–173983 | 13 | 0.214 [0.200, 0.228] | -0.067 [-0.074, -0.060] | 0 |
| 0.5 | 128 | threshold_05 | 20000–1000000 | 21336–246834 | 15 | 0.285 [0.270, 0.302] | 0.000 [0.000, 0.000] | 0 |
| 0.5 | 128 | positive_lobe | 20000–1000000 | 21336–246834 | 15 | 0.282 [0.265, 0.302] | -0.003 [-0.008, 0.003] | 17 |
| 0.5 | 128 | spectral_moment | 20000–1000000 | 21336–246834 | 15 | 0.187 [0.178, 0.196] | -0.099 [-0.108, -0.092] | 0 |
| 0.5 | 128 | inverse_interface_proxy | 20000–1000000 | 21336–246834 | 15 | 0.216 [0.206, 0.228] | -0.069 [-0.078, -0.064] | 0 |
| 0.5 | 128 | threshold_05 | 200000–1000000 | 207231–246834 | 2 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 128 | positive_lobe | 200000–1000000 | 207231–246834 | 2 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 17 |
| 0.5 | 128 | spectral_moment | 200000–1000000 | 207231–246834 | 2 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.5 | 128 | inverse_interface_proxy | 200000–1000000 | 207231–246834 | 2 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 32 | threshold_05 | 1000–20000 | 1548–4421 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 32 | positive_lobe | 1000–20000 | 1548–4421 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 32 |
| 0.15 | 32 | spectral_moment | 1000–20000 | 1548–4421 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 32 | inverse_interface_proxy | 1000–20000 | 1548–4421 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 32 | threshold_05 | 1000–200000 | 1548–173983 | 16 | 0.222 [0.214, 0.231] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 32 | positive_lobe | 1000–200000 | 1548–173983 | 16 | 0.203 [0.195, 0.212] | -0.019 [-0.024, -0.015] | 32 |
| 0.15 | 32 | spectral_moment | 1000–200000 | 1548–173983 | 16 | 0.134 [0.128, 0.140] | -0.088 [-0.092, -0.084] | 0 |
| 0.15 | 32 | inverse_interface_proxy | 1000–200000 | 1548–173983 | 16 | 0.166 [0.157, 0.175] | -0.056 [-0.061, -0.050] | 0 |
| 0.15 | 32 | threshold_05 | 20000–200000 | 21336–173983 | 11 | 0.122 [0.075, 0.174] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 32 | positive_lobe | 20000–200000 | 21336–173983 | 11 | 0.108 [0.063, 0.156] | -0.015 [-0.022, -0.007] | 32 |
| 0.15 | 32 | spectral_moment | 20000–200000 | 21336–173983 | 11 | 0.082 [0.051, 0.112] | -0.040 [-0.068, -0.013] | 0 |
| 0.15 | 32 | inverse_interface_proxy | 20000–200000 | 21336–173983 | 11 | 0.102 [0.059, 0.142] | -0.020 [-0.054, 0.014] | 0 |
| 0.15 | 32 | threshold_05 | 20000–1000000 | 21336–1000000 | 20 | 0.040 [0.022, 0.060] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 32 | positive_lobe | 20000–1000000 | 21336–1000000 | 20 | 0.037 [0.020, 0.056] | -0.003 [-0.007, 0.001] | 32 |
| 0.15 | 32 | spectral_moment | 20000–1000000 | 21336–1000000 | 20 | 0.025 [0.015, 0.035] | -0.016 [-0.026, -0.006] | 0 |
| 0.15 | 32 | inverse_interface_proxy | 20000–1000000 | 21336–1000000 | 20 | 0.030 [0.017, 0.043] | -0.010 [-0.021, 0.000] | 0 |
| 0.15 | 32 | threshold_05 | 200000–1000000 | 207231–1000000 | 9 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 32 | positive_lobe | 200000–1000000 | 207231–1000000 | 9 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 32 |
| 0.15 | 32 | spectral_moment | 200000–1000000 | 207231–1000000 | 9 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 32 | inverse_interface_proxy | 200000–1000000 | 207231–1000000 | 9 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 64 | threshold_05 | 1000–20000 | 1091–15039 | 16 | 0.237 [0.224, 0.249] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 64 | positive_lobe | 1000–20000 | 1091–15039 | 16 | 0.236 [0.222, 0.249] | -0.000 [-0.007, 0.007] | 37 |
| 0.15 | 64 | spectral_moment | 1000–20000 | 1091–15039 | 16 | 0.142 [0.135, 0.149] | -0.094 [-0.100, -0.088] | 0 |
| 0.15 | 64 | inverse_interface_proxy | 1000–20000 | 1091–15039 | 16 | 0.180 [0.170, 0.189] | -0.057 [-0.062, -0.052] | 0 |
| 0.15 | 64 | threshold_05 | 1000–200000 | 1091–86439 | 17 | 0.258 [0.248, 0.268] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 64 | positive_lobe | 1000–200000 | 1091–86439 | 17 | 0.252 [0.241, 0.263] | -0.006 [-0.010, -0.000] | 37 |
| 0.15 | 64 | spectral_moment | 1000–200000 | 1091–86439 | 17 | 0.155 [0.148, 0.161] | -0.103 [-0.107, -0.099] | 0 |
| 0.15 | 64 | inverse_interface_proxy | 1000–200000 | 1091–86439 | 17 | 0.191 [0.183, 0.200] | -0.067 [-0.070, -0.064] | 0 |
| 0.15 | 64 | threshold_05 | 20000–200000 | 86439–86439 | 1 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 64 | positive_lobe | 20000–200000 | 86439–86439 | 1 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 37 |
| 0.15 | 64 | spectral_moment | 20000–200000 | 86439–86439 | 1 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 64 | inverse_interface_proxy | 20000–200000 | 86439–86439 | 1 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 64 | threshold_05 | 20000–1000000 | 86439–1000000 | 6 | 0.258 [0.231, 0.287] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 64 | positive_lobe | 20000–1000000 | 86439–1000000 | 6 | 0.239 [0.210, 0.269] | -0.019 [-0.026, -0.011] | 37 |
| 0.15 | 64 | spectral_moment | 20000–1000000 | 86439–1000000 | 6 | 0.146 [0.130, 0.165] | -0.111 [-0.124, -0.100] | 0 |
| 0.15 | 64 | inverse_interface_proxy | 20000–1000000 | 86439–1000000 | 6 | 0.153 [0.133, 0.175] | -0.104 [-0.117, -0.093] | 0 |
| 0.15 | 64 | threshold_05 | 200000–1000000 | 496824–1000000 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 64 | positive_lobe | 200000–1000000 | 496824–1000000 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 37 |
| 0.15 | 64 | spectral_moment | 200000–1000000 | 496824–1000000 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 64 | inverse_interface_proxy | 200000–1000000 | 496824–1000000 | 5 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 96 | threshold_05 | 1000–20000 | 1091–17913 | 17 | 0.232 [0.221, 0.241] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 96 | positive_lobe | 1000–20000 | 1091–17913 | 17 | 0.224 [0.213, 0.233] | -0.008 [-0.010, -0.006] | 14 |
| 0.15 | 96 | spectral_moment | 1000–20000 | 1091–17913 | 17 | 0.139 [0.132, 0.145] | -0.092 [-0.096, -0.088] | 0 |
| 0.15 | 96 | inverse_interface_proxy | 1000–20000 | 1091–17913 | 17 | 0.176 [0.167, 0.183] | -0.056 [-0.059, -0.052] | 0 |
| 0.15 | 96 | threshold_05 | 1000–200000 | 1091–146069 | 27 | 0.251 [0.244, 0.259] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 96 | positive_lobe | 1000–200000 | 1091–146069 | 27 | 0.241 [0.234, 0.249] | -0.010 [-0.012, -0.008] | 14 |
| 0.15 | 96 | spectral_moment | 1000–200000 | 1091–146069 | 27 | 0.150 [0.146, 0.154] | -0.101 [-0.105, -0.098] | 0 |
| 0.15 | 96 | inverse_interface_proxy | 1000–200000 | 1091–146069 | 27 | 0.182 [0.178, 0.187] | -0.069 [-0.073, -0.065] | 0 |
| 0.15 | 96 | threshold_05 | 20000–200000 | 21336–146069 | 10 | 0.289 [0.270, 0.308] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 96 | positive_lobe | 20000–200000 | 21336–146069 | 10 | 0.276 [0.259, 0.294] | -0.013 [-0.017, -0.008] | 14 |
| 0.15 | 96 | spectral_moment | 20000–200000 | 21336–146069 | 10 | 0.168 [0.156, 0.182] | -0.121 [-0.129, -0.112] | 0 |
| 0.15 | 96 | inverse_interface_proxy | 20000–200000 | 21336–146069 | 10 | 0.192 [0.176, 0.211] | -0.097 [-0.107, -0.087] | 0 |
| 0.15 | 96 | threshold_05 | 20000–1000000 | 21336–350190 | 14 | 0.273 [0.256, 0.289] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 96 | positive_lobe | 20000–1000000 | 21336–350190 | 14 | 0.258 [0.240, 0.276] | -0.015 [-0.019, -0.011] | 14 |
| 0.15 | 96 | spectral_moment | 20000–1000000 | 21336–350190 | 14 | 0.161 [0.151, 0.170] | -0.112 [-0.120, -0.103] | 0 |
| 0.15 | 96 | inverse_interface_proxy | 20000–1000000 | 21336–350190 | 14 | 0.181 [0.171, 0.192] | -0.091 [-0.100, -0.082] | 0 |
| 0.15 | 96 | threshold_05 | 200000–1000000 | 207231–350190 | 4 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 96 | positive_lobe | 200000–1000000 | 207231–350190 | 4 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 14 |
| 0.15 | 96 | spectral_moment | 200000–1000000 | 207231–350190 | 4 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 96 | inverse_interface_proxy | 200000–1000000 | 207231–350190 | 4 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 128 | threshold_05 | 1000–20000 | 1091–17913 | 17 | 0.235 [0.227, 0.242] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 128 | positive_lobe | 1000–20000 | 1091–17913 | 17 | 0.227 [0.221, 0.234] | -0.007 [-0.009, -0.006] | 0 |
| 0.15 | 128 | spectral_moment | 1000–20000 | 1091–17913 | 17 | 0.141 [0.136, 0.146] | -0.094 [-0.097, -0.091] | 0 |
| 0.15 | 128 | inverse_interface_proxy | 1000–20000 | 1091–17913 | 17 | 0.178 [0.171, 0.184] | -0.057 [-0.059, -0.055] | 0 |
| 0.15 | 128 | threshold_05 | 1000–200000 | 1091–173983 | 30 | 0.252 [0.248, 0.256] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 128 | positive_lobe | 1000–200000 | 1091–173983 | 30 | 0.241 [0.237, 0.245] | -0.011 [-0.012, -0.010] | 0 |
| 0.15 | 128 | spectral_moment | 1000–200000 | 1091–173983 | 30 | 0.151 [0.148, 0.153] | -0.102 [-0.103, -0.100] | 0 |
| 0.15 | 128 | inverse_interface_proxy | 1000–200000 | 1091–173983 | 30 | 0.182 [0.179, 0.185] | -0.070 [-0.071, -0.069] | 0 |
| 0.15 | 128 | threshold_05 | 20000–200000 | 21336–173983 | 13 | 0.275 [0.259, 0.292] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 128 | positive_lobe | 20000–200000 | 21336–173983 | 13 | 0.262 [0.245, 0.279] | -0.013 [-0.016, -0.011] | 0 |
| 0.15 | 128 | spectral_moment | 20000–200000 | 21336–173983 | 13 | 0.164 [0.155, 0.173] | -0.112 [-0.119, -0.104] | 0 |
| 0.15 | 128 | inverse_interface_proxy | 20000–200000 | 21336–173983 | 13 | 0.188 [0.177, 0.198] | -0.088 [-0.096, -0.080] | 0 |
| 0.15 | 128 | threshold_05 | 20000–1000000 | 21336–1000000 | 23 | 0.281 [0.267, 0.294] | 0.000 [0.000, 0.000] | 0 |
| 0.15 | 128 | positive_lobe | 20000–1000000 | 21336–1000000 | 23 | 0.271 [0.256, 0.285] | -0.010 [-0.012, -0.009] | 0 |
| 0.15 | 128 | spectral_moment | 20000–1000000 | 21336–1000000 | 23 | 0.166 [0.159, 0.174] | -0.115 [-0.121, -0.108] | 0 |
| 0.15 | 128 | inverse_interface_proxy | 20000–1000000 | 21336–1000000 | 23 | 0.182 [0.175, 0.190] | -0.099 [-0.106, -0.092] | 0 |
| 0.15 | 128 | threshold_05 | 200000–1000000 | 207231–1000000 | 10 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 128 | positive_lobe | 200000–1000000 | 207231–1000000 | 10 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 128 | spectral_moment | 200000–1000000 | 207231–1000000 | 10 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |
| 0.15 | 128 | inverse_interface_proxy | 200000–1000000 | 207231–1000000 | 10 | unresolved [unresolved, unresolved] | unresolved [unresolved, unresolved] | 0 |

## All matched-size rows

| c | sweep | L/128 | estimator | ratio [95%] | status |
|---:|---:|---:|---|---|---|
| 0.5 | 207231 | 32/128 | threshold_05 | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 207231 | 32/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 207231 | 32/128 | spectral_moment | 0.852 [0.803, 0.899] | resolved |
| 0.5 | 207231 | 32/128 | inverse_interface_proxy | 0.853 [0.787, 0.918] | resolved |
| 0.5 | 1000000 | 32/128 | threshold_05 | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 1000000 | 32/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 1000000 | 32/128 | spectral_moment | 0.618 [0.589, 0.645] | resolved |
| 0.5 | 1000000 | 32/128 | inverse_interface_proxy | 0.591 [0.551, 0.628] | resolved |
| 0.5 | 207231 | 64/128 | threshold_05 | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 207231 | 64/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 207231 | 64/128 | spectral_moment | 1.016 [0.969, 1.067] | resolved |
| 0.5 | 207231 | 64/128 | inverse_interface_proxy | 1.021 [0.964, 1.084] | resolved |
| 0.5 | 1000000 | 64/128 | threshold_05 | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 1000000 | 64/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 1000000 | 64/128 | spectral_moment | 0.931 [0.879, 0.985] | resolved |
| 0.5 | 1000000 | 64/128 | inverse_interface_proxy | 0.921 [0.865, 0.981] | resolved |
| 0.5 | 207231 | 96/128 | threshold_05 | 1.033 [0.987, 1.084] | resolved |
| 0.5 | 207231 | 96/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 207231 | 96/128 | spectral_moment | 1.004 [0.975, 1.034] | resolved |
| 0.5 | 207231 | 96/128 | inverse_interface_proxy | 0.999 [0.965, 1.034] | resolved |
| 0.5 | 1000000 | 96/128 | threshold_05 | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 1000000 | 96/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.5 | 1000000 | 96/128 | spectral_moment | 1.008 [0.972, 1.047] | resolved |
| 0.5 | 1000000 | 96/128 | inverse_interface_proxy | 1.000 [0.957, 1.046] | resolved |
| 0.15 | 207231 | 32/128 | threshold_05 | 0.757 [0.723, 0.792] | resolved |
| 0.15 | 207231 | 32/128 | positive_lobe | 0.745 [0.716, 0.774] | resolved |
| 0.15 | 207231 | 32/128 | spectral_moment | 0.848 [0.816, 0.884] | resolved |
| 0.15 | 207231 | 32/128 | inverse_interface_proxy | 0.862 [0.809, 0.921] | resolved |
| 0.15 | 1000000 | 32/128 | threshold_05 | 0.475 [0.445, 0.504] | resolved |
| 0.15 | 1000000 | 32/128 | positive_lobe | 0.477 [0.451, 0.504] | resolved |
| 0.15 | 1000000 | 32/128 | spectral_moment | 0.648 [0.617, 0.674] | resolved |
| 0.15 | 1000000 | 32/128 | inverse_interface_proxy | 0.640 [0.598, 0.679] | resolved |
| 0.15 | 207231 | 64/128 | threshold_05 | 1.075 [0.963, 1.202] | resolved |
| 0.15 | 207231 | 64/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.15 | 207231 | 64/128 | spectral_moment | 1.043 [0.982, 1.108] | resolved |
| 0.15 | 207231 | 64/128 | inverse_interface_proxy | 1.052 [0.986, 1.128] | resolved |
| 0.15 | 1000000 | 64/128 | threshold_05 | 0.967 [0.905, 1.028] | resolved |
| 0.15 | 1000000 | 64/128 | positive_lobe | 0.947 [0.888, 1.006] | resolved |
| 0.15 | 1000000 | 64/128 | spectral_moment | 0.963 [0.925, 0.999] | resolved |
| 0.15 | 1000000 | 64/128 | inverse_interface_proxy | 0.953 [0.910, 0.995] | resolved |
| 0.15 | 207231 | 96/128 | threshold_05 | 0.985 [0.939, 1.033] | resolved |
| 0.15 | 207231 | 96/128 | positive_lobe | 0.987 [0.942, 1.034] | resolved |
| 0.15 | 207231 | 96/128 | spectral_moment | 0.987 [0.956, 1.022] | resolved |
| 0.15 | 207231 | 96/128 | inverse_interface_proxy | 0.985 [0.945, 1.029] | resolved |
| 0.15 | 1000000 | 96/128 | threshold_05 | 1.111 [1.016, 1.218] | resolved |
| 0.15 | 1000000 | 96/128 | positive_lobe | unresolved [unresolved, unresolved] | unresolved |
| 0.15 | 1000000 | 96/128 | spectral_moment | 1.049 [0.999, 1.101] | resolved |
| 0.15 | 1000000 | 96/128 | inverse_interface_proxy | 1.041 [0.988, 1.097] | resolved |

## Boundary

The tables report sensitivity of finite-window measurements. They do not select an asymptotic law, establish a unique finite-size onset, validate a real alloy or make any estimator a particle radius.
