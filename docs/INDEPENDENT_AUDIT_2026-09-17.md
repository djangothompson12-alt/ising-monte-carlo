# Independent AI technical audit of the MetalDAM pilot

**17 September 2026.** A separate Codex agent received a fresh task brief
(`docs/SECOND_ASSISTANT_AUDIT_TASK.md`) and inspected the source, producer
release, local archive and generated measurements. This is a second AI check,
**not** an academic's review, endorsement, materials-lab validation, or
evidence of student-independent authorship. The main agent checked the
reported defects against the source files before updating the pilot note.

## Verdict

No confirmed code, arithmetic, or image-pairing defect was found in the
declared pilot. The headline result remains a **descriptive static-image
stress test**: good pixel overlap did not imply agreement in this particular
half-height correlation-length observable. It must not be presented as a new
general principle, an alloy-kinetics result, or a deployed tool.

## Checks completed

- The labelled-release ZIP hash matches the input manifest. The auditor
  independently recalculated the six headline *per-image medians* from the
  CSV: Dice 0.824792; reference fraction 0.555652; Otsu-dark fraction
  0.734807; median paired fraction difference +0.178871; reference length
  5.253489 px; median Otsu-dark/reference length ratio 0.425947.
- The in-sample, annotation-optimised medians are Dice 0.834358 and length
  ratio 0.426527. Bright-polarity Dice median is 0.057955. All 26 images
  with Dice at least 0.8 have length ratio outside the descriptive 0.8–1.2
  band; the full ratio range is 0.166026–0.638559.
- Raw image–label pairs 0, 15, 19 and 26 were inspected privately. Visible
  structures align, including the two 66-row bands and label 26's identical
  RGB channels. A ±3-pixel registration check found no meaningful shift
  improvement. Independent direct-mask Dice and brute Otsu checks on these
  pairs matched the implementation.
- The auditor checked that cited materials-imaging work had already examined
  downstream [precipitate-size and oxide-thickness
  errors](https://www.nature.com/articles/s41524-022-00878-5) and
  [grain-diameter errors](https://www.nature.com/articles/s41524-025-01801-4).
  Therefore this generic measurement warning is not claimed as first or new.

## Finding 1 — source-data inconsistency (moderate)

The [producer README](https://github.com/ari-dasci/OD-MetalDAM) lists matrix
and austenite fractions of 31.86% and 58.26%. Counting raw release labels
instead gives 34.6325% and 55.4855% across 32,786,944 pixels. Fractions of
classes 2–4 agree with the README to rounding. The separately downloaded
producer metadata asset, SHA-256
`936a8c0fbd66e2ededd2ffce0856555481e38bff6f38423f9d8931aa8e966ca4`,
is a SQLite database despite its `.sql` filename. Its row 8 records a total
of 719,872 although its own class counts sum to 1,145,600; row 27 records
class counts `[261838,66382,0,0,0]` where the raw label contains
`[261838,391652,66382,0,0]`. The README discrepancy is not fully explained
by these two rows alone. The code measures raw label pixels, so the reported
mask comparisons are unaffected. A source caveat was added to the pilot note.

## Finding 2 — fine-texture sensitivity (low, interpretive)

In a post-hoc private check on image 19, a 3×3 median filter changed the
Otsu-dark correlation length from 1.035 to 2.152 px while Dice moved only
from 0.7355 to 0.7361. The filter was **not** in the declared analysis and
must not be advertised as a better phase mask. This reinforces that the
specific observable is sensitive to isolated or fine-scale pixels; it is not
a direct grain diameter or physical radius. The pilot note now says so.

## Unresolved before any external claim

The dataset producer does not clearly state image redistribution rights in
its public repository/release. Raw images remain in ignored local storage;
do not publish overlays or bundle them into an application. Pixel size was
not calibrated in the pilot, so only pixel units are reported. Images may
share specimens and acquisition conditions, so 42 images are not asserted to
be 42 independent material samples. A materials expert has not yet judged
whether austenite correlation length matters in their workflow. The audit
cannot substitute for that judgement or for independent academic review of
the Ising paper.
