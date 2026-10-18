# Static length agreement and a fixed kinetic fit

AI-assisted exploratory extension, written 15 October before this extension's
calculation, after the underlying Kawasaki results were already known.
This is not preregistration, an unseen holdout or a replacement primary question.
No new Monte Carlo or experimental data will be generated.

## Purpose and estimand

The fixed question remains whether preserving species-site fraction after
resolution reduction preserves the native finite-window fitted exponent.
Here ask a supporting methods question: how small would a per-time relative
length difference have to be to bound the difference of the declared log-log
OLS slopes, without assumptions about the temporal pattern of that difference?

The elementary regression identity and interval bound are not claimed as new
mathematics. Static native-mask agreement is not physical accuracy. This
analysis does not automatically turn the mask tool into a kinetic validator.

## Calculation fixed before execution

Let x_i=log(t_i), w_i=(x_i-mean(x))/sum((x-mean(x))^2), and
q_i=mean(processed length)_i / mean(native length)_i on identical times.
Then delta_alpha=sum(w_i log(q_i)). If every q_i is in [a,b], the sharp
box bound is |delta_alpha| <= S log(b/a), S=sum(abs(w_i))/2.
Positive weights at b and negative weights at a attain the positive bound;
reverse them for the negative bound. This witness is an abstract length
sequence, not necessarily realisable by the image operator.

If every relative difference is at most epsilon<1, use a=1-epsilon and
b=1+epsilon. A sufficient common epsilon for an exponent budget B is
tanh(B/(2S)). Constant multiplicative bias cancels; hence this sufficient
criterion is not necessary. No claim of optimal experimental acquisition
or validated resolution selection follows.

## Known-data replay

Read the hash-checked fresh observation and fit tables. Keep compositions
separate. Use the half-height observable only, all factors (2,4,8), four
declared origins and integrated/fixed/fraction-matched treatments: 72 related
comparisons, not 72 independent samples. Keep all eight trajectories per
composition and the existing all-treatment/all-tie common time mask. Average
the five tie lengths inside each trajectory/time before ensemble averaging;
ties and saved times are not extra replications. Recompute the native and
processed slopes and check against all corresponding archived fit rows.
Retain unresolved cases, if present, rather than selecting by the budget.
Do not use secondary factor-eight positive-lobe values with their known
arithmetic discrepancy. Primary factor-four half-height data are unchanged.

Show illustrative static tolerances 2%, 5%, 10% and the historical numerical
exponent budget 0.02. These are not lab-owner requirements or materials
standards. Report point differences separately from the archived paired
bootstrap intervals. No threshold will be tuned to improve a pass rate, and
no independent-case accuracy estimate will be calculated.

## Checks and interpretation

Verify the formulas by independent least squares, every corner of a small
ratio box, constant/power-law ratios, unit changes, and attainment of both
sharp bounds. Recheck archived slope values, counts and source/table hashes.
Static tests verify one mask calculation; this extension assesses a different
time-series outcome. The proposed methods contribution needs an expert's
novelty judgement, a justified published baseline, and success/failure evidence
at adequate resolution. This known short-window stress test cannot supply all
of those requirements. Source and output manifests accompany all new results.
