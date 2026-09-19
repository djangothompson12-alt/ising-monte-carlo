# Resolution-method comparison: remaining reproduction boundary

Source: Ledesma-Alonso, Barbosa and Ortegón, *Physical Review E* 97,
023304 (2018), [author manuscript](https://arxiv.org/abs/1712.03183).
PDF pages 3, 8 and 11 were visually inspected; sections II and III were
also text-checked. This is a method comparison, not a full replication.

| Component | Published method | Our completed comparison |
|---|---|---|
| Descriptors | Two-point, line-path, pore-size; both phases | Directional covariance only |
| Aggregation | Ensemble descriptors, Eq.32 | Each retained snapshot must pass |
| Characteristic length | First near-zero approach; minimum across descriptors/phases | Minimum of two directional covariance lengths |
| Reduction limit | Floor/ceiling rule, Eq.34 | Rounding algebra tested |
| Reduction process | Sequential random, bilinear or bicubic steps | Direct block integration, thresholding and fraction matching |
| Outcome | Static statistical-information retention | Paired finite-window exponent change |

Pore-size density normalization uses interface density and phase fraction
(Eqs.11–12); a distance-transform histogram needs an explicit discretization
before being treated as equivalent. The paper delegates digitized descriptor
computation to earlier methods (section III.C). A faithful baseline therefore
needs those conventions checked, not just two extra arrays named after them.

## What we can conclude now

Our zero-acceptance result applies to our conservative adaptation, not to the
published method. It cannot establish that we have outperformed or refuted
that work. No full three-descriptor benchmark has been completed.

The new `sequential_binary` unit test independently illustrates another
non-equivalence: thresholding after each factor-two average can differ from
thresholding once after factor-four averaging. We do not silently treat the
two image operators as interchangeable. This is a test example, not the
authors' full implementation or validation against their figures.

## Decision before further method development

Send the bounded result for criticism now. Ask whether a kinetic paired-error
benchmark adds useful evidence beyond established static-image descriptors,
and which descriptor implementation would be a credible baseline. If a
reviewer agrees this comparison is worthwhile, specify digitization, boundary
conditions and acceptance criteria before testing another fresh dataset.
The already inspected fresh cohort cannot serve as untouched validation for
a subsequently tuned warning rule.

Do not spend another large simulation campaign trying to manufacture a
passing diagnostic. Keep the negative result and the all-case tables.
