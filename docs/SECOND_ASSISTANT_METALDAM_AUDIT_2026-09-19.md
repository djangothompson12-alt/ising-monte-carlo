# Second-assistant adversarial audit of the MetalDAM pilot

**Status:** AI cross-check completed 19 September 2026. This is not external
peer review, a source-author response, a laboratory validation or an academic
endorsement. The second assistant was asked to look for defects rather than to
polish the project.

## Result

No confirmed code or arithmetic error was found in the declared MetalDAM
pilot. The six headline medians were independently recomputed from the local
hashed release as `0.824792`, `0.555652`, `0.734807`, `+0.178871`, `5.253489`
pixels and `0.425947`. The annotation-optimised Dice and length-ratio medians
were `0.834358` and `0.426527`; the bright-polarity Dice median was `0.057955`.
All 26 images with Dice at least `0.8` had a length ratio outside the displayed
`0.8–1.2` band. That band remains descriptive, not an engineering tolerance.

The assistant independently checked image–label pairs 0, 15, 19 and 26 in the
private local source archive. The structures aligned visually; images 15 and
19 had 66-row information bands and the other two had 65-row bands, matching
the recorded cropping logic. The three channels of label 26 agreed. Searching
translations within three pixels produced no meaningful alignment improvement.
Independent Otsu thresholds and explicit-mask Dice calculations matched the
implementation for all four samples. The local ZIP and source hashes matched
the recorded manifest.

## Source-data inconsistency found

The raw label pixels give overall matrix and austenite fractions of `34.6325%`
and `55.4855%`, whereas the producer README reports `31.86%` and `58.26%`.
Classes 2–4 agree to rounding. The release's separate metadata also contains
two inconsistent records: image 8's class counts sum to `1,145,600` while its
recorded total is `719,872`, and image 27's recorded class-count array differs
from the raw label counts. The pilot measures the label pixels themselves, so
these summary inconsistencies do not change its reported medians. They do make
the public source an imperfect reference and must remain disclosed.

The producer README identifies code 1 as austenite, and the sampled coloured
labels were consistent with the use of codes 0 and 1. The metadata discrepancy
does not establish that the class semantics are wrong.

## Sensitivity found

On micrograph 19, a private exploratory 3×3 median filter changed the
Otsu-dark correlation length from `1.035` to `2.152` pixels while Dice changed
only from `0.7355` to `0.7361`. This was not predeclared and is not a correction.
It shows that the half-height correlation length can respond strongly to fine
mask texture even when pixel overlap barely moves. The pilot must therefore
not relabel this observable as grain diameter, particle size or a physical
phase-boundary measurement.

## What survived the audit

The narrow result remains a reproducible stress test: on these images, a
reasonably high overlap score did not guarantee agreement in this particular
image-derived length. It remains descriptive across images from a public
release with unclear independence and no verified physical pixel scale. It is
not evidence about Kawasaki kinetics, a real ageing exponent, or industrial
deployment. The source repository did not clearly grant redistribution
rights, so withholding its images from the review archive remains appropriate.

The next meaningful audit must come from a materials-image owner who defines
the feature, physical scale, independent experimental unit and decision before
the result is computed. Another AI check cannot supply external validation.
