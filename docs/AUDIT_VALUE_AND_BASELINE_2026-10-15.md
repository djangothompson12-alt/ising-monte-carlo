# What useful check does the mask audit add?

15 October 2026. AI-assisted working specification, not student-approved
prose, a novelty certificate or evidence of outside use.

## One job, without changing the research question

On a supplied, already approved 2D binary phase mask: does direct 2x or 4x
digital reduction change the declared directional correlation half-height
measurement beyond a tolerance the image owner chose beforehand?

The static tool supports the fixed Kawasaki question about fraction matching
and a finite-window exponent; it does not itself fit experimental kinetics.
It does not recover boundaries, certify segmentation, or simulate a microscope.
Phase area fraction is not generally chemical composition. A numerical pass
must never suppress an unresolved result or a resolution warning.

## Comparison and contribution boundary

| Established capability | Source | What the proposed audit must add to be useful |
|---|---|---|
| Correlation measurements with calibrated spacing | [PoreSpy](https://porespy.org/autoapi/porespy/metrics/two_point_correlation.html) | A convenient paired processing check, not a claim to invent correlations. Its radial phase probability is not our directional, globally centred covariance. |
| Feature dimensions, distributions and phase fractions | [AQUAMI](https://github.com/JStuckner/aquami) | A useful check around an existing measurement workflow, not another general measurement suite. |
| Binary and labelled-region geometry | [MorphoLibJ](https://imagej.net/plugins/morpholibj) | Clearly justified processing comparisons; more descriptors alone are not a contribution. |
| Phase-fraction representativity | [ImageRep](https://doi.org/10.1002/advs.202414149) | Same-field processing sensitivity is a different question from sampling representativity. Neither establishes physical truth. |
| Descriptor preservation during image reduction | [Ledesma-Alonso et al.](https://arxiv.org/abs/1712.03183) | A justified comparison and a downstream kinetic question, not renaming a partial adaptation as the full method. |

An experienced user could construct these comparisons with existing packages.
Therefore convenience, traceability and failure reporting are candidate
practical advantages, not demonstrated scientific novelty. No competing
package has been executed for a head-to-head performance result here.

## First bounded calculation: match the measurement conventions

Specification written before this calculation, after the existing audit,
synthetic fields and literature were known. This is an internal verification
exercise, not preregistration, an unseen validation set or independent review.

For each lag on the finite field, independently count foreground pairs and
the foreground fractions of the left and right members. With global fraction
p, pair probability S2 and those two marginal fractions a and b, our covariance
is (S2 - p(a+b) + p^2)/(p(1-p)). The common homogeneous-ensemble expression
(S2 - p^2)/(p(1-p)) differs by p(2p-a-b)/(p(1-p)) on a finite field.
This elementary identity is not new mathematics and does not show that either
convention is universally better. Radial versus directional averaging is a
further difference; this check is directional only.

Use all 18 existing deterministic synthetic fields, direct factors 1, 2, 4,
both exact block-tie rules and both phase labels. Retain constant fields and
missing half-height crossings. Compare the independently counted centred
covariance with the existing FFT kernel, including its exact-half-height
refinement, at every retained lag. Report both conventions and all cases;
do not select fields for a dramatic difference or alter the production kernel.
The synthetic checker is AI-assisted and separately implemented, not an
independent person's verification. It does not execute PoreSpy or reproduce
the full published multi-descriptor method.

### Completed check

The run retained all 18 fields: 216 paired mask/convention comparisons,
or 432 directional curve checks. Maximum absolute disagreement with the
production covariance was 4.44e-16; the finite-marginal identity residual was
1.11e-16. Missing crossings and constant fields were retained. These figures
verify the declared discrete arithmetic on known fixtures, not materials
accuracy or a predictive resolution criterion. The local result is
`output/mask_conventions_2026-10-15_v2/`; all cases, source hashes and a
readable report are retained. No production numerical definition was changed.
The repository suite passed 268 tests; the final brief/navigation/convention
subset passed 14 tests after the presentation edits. These are developer
checks, not student hours, human independent verification or a novelty score.

## The smallest meaningful practical comparison next

Before analysing any new permitted mask, record:

1. The owner's intended measurement and actual processing decision. If this
   correlation descriptor is irrelevant to that decision, stop or obtain
   approval for a different measurement; do not relabel it a particle radius.
2. The phase definition, square-pixel calibration, fixed ROI, primary tie rule,
   and whether the tolerance applies to the mean or both directions.
3. The tolerance and its reason, or an explicit statement that none is known.
   An illustrative developer tolerance is not an owner requirement.
4. Native, 2x and 4x outputs with opposite-tie sensitivity, retained warnings
   and failed measurements. No post-result tuning or silent exclusions.
5. A minimal existing/manual workflow using the same operator, field, units,
   centring, lag support and crossing rule. A different metric is a sensitivity
   comparison, not an arithmetic truth benchmark.
6. What the owner concludes: changed decision, confirmed existing check,
   duplicated an easy check, no useful information, or misleading result.
   Any report-preparation time comparison needs actual timed observations;
   do not infer saved time from feature counts.

One bounded pilot is evidence about that use, not broad laboratory adoption.
An unused or unhelpful tool is an acceptable finding. Approval is required
before sharing images, identifying a participant or sending any request.

## Publication-facing gate, unchanged

The possible contribution is a reproducible paired kinetic benchmark with
resolved success and failure cases plus a useful processing check. The general
facts that image reduction changes geometry or fraction does not fix geometry
are prior art. Current severe-resolution effects alone do not establish
ordinary microscopy relevance. The known 5%-agreement examples do not supply
an observed large exponent failure within that criterion.

Keep the adequately resolved comparison, justified published baseline and
specialist criticism as open tasks. Do not delay an honest initial criticism
request until those paper-level tasks are finished. No additional large
simulation campaign or new general-purpose app is authorised by this plan.
