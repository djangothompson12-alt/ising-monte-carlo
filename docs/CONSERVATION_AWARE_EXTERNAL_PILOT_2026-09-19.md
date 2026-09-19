# External pilot: what can and cannot be tested with real materials images

*AI-assisted decision document, 19 September 2026. No laboratory or company
has agreed to this pilot, supplied data, used the code or endorsed the work.*

## Why this distinction matters

In the Kawasaki simulation, every lattice site is either species A or species
B. The mean of that binary field is therefore the model composition, and the
exchange rule conserves it exactly. A real micrograph is different. A binary
phase mask labels regions as phases, not individual atoms. Each phase can
contain both alloying elements, and the amount of each phase can change while
the specimen's total elemental composition remains fixed.

This means that **phase area fraction is not normally the same number as bulk
chemical composition**. Treating it as the same would turn a useful simulation
control into a false materials claim. The first outside pilot must follow one
of the two routes below and use the language belonging to that route.

## Route A: an approved binary phase mask

**Question:** How sensitive is one declared geometrical length and apparent
phase area fraction to reducing the resolution of the *same* checked mask?

The existing [`mask_resolution_audit.py`](../research/mask_resolution_audit.py)
is suitable for this route. It reports native, 2× and 4× measurements while
retaining unresolved correlation crossings. It does not segment a raw image,
fit a coarsening exponent or estimate chemical mass balance.

Minimum information from the data owner:

- phase or feature represented by each label, and who checked the mask;
- specimen identity, imaging method, physical pixel size and length unit;
- a fixed rectangular region and the reason for choosing it;
- whether images are repeat measurements of one field, different fields from
  one specimen, or genuinely independent specimens;
- the owner's normal measurement and the size of a change that would matter;
- permission boundaries for data, derived tables, names and quotations.

What may be concluded: the chosen mask-derived length was or was not sensitive
to this artificial coarsening operation in this field. What may not be
concluded: total composition was violated, the instrument has the same bias,
the simulation predicts the alloy, or the laboratory adopted the tool.

## Route B: a calibrated quantitative composition map

**Question:** Does spatial integration preserve the mean measured elemental
composition over a fixed registered field, and how does a later classification
or segmentation step change the reported quantity?

This is closer to the simulation's conservation-aware decomposition, but the
current binary-mask tool is **not** sufficient. The owner would need to supply
calibrated per-pixel composition values or another quantitatively interpretable
signal, rather than colour-rendered elemental-map images whose channels may
have been independently scaled. EDS-PhaSe, for example, explicitly requires
the measured overall composition of the scanned region and the units of the
EDS maps; published work on EDS phase-fraction estimation also treats boundary
pixels as possible mixtures of phases rather than automatically assigning a
pure binary label.

Before any code is run, record:

- element, units (`at.%`, `wt.%`, counts or another calibrated quantity),
  calibration and uncertainty;
- whether missing, saturated, background-corrected or below-detection pixels
  exist and how they are represented;
- pixel spacing in both directions, beam interaction-volume limitations and
  any smoothing already applied by the instrument software;
- one fixed field, its registration across times and whether material enters
  or leaves that field;
- reference composition for the same region, if one exists;
- the exact integration and classification rules, fixed before inspecting the
  result;
- the independent experimental unit and the number of specimens.

Even for this route, the mean of a small two-dimensional field need not remain
constant if the field is not registered or if material crosses its boundary.
Different destructive sections at different ageing times cannot be treated as
one conserved field. A segmented phase fraction remains distinct from mean
elemental composition after the classification step.

## Time-series decision tree

1. **Only one time point?** Run a static resolution-sensitivity audit; do not
   fit a growth law.
2. **Several times from one registered field?** Treat times as paired within
   one specimen. Check field conservation and unresolved measurements before
   considering a slope.
3. **Destructive sections or different fields?** Do not claim exact field-wise
   conservation. Estimate between-field and between-specimen variation first.
4. **Only a binary phase mask?** Discuss phase area fraction, never chemical
   composition conservation.
5. **Quantitative composition maps with calibration?** A separate analysis can
   compare mean-preserving integration with later classification, but only
   after the owner approves the calibration and physical question.
6. **No owner-defined decision?** Stop. A convenient dataset is not evidence
   of practical relevance.

## A smallest useful outside test

The researcher supplies two to five approved masks from one clearly described
measurement problem. Before seeing the output, they state which feature length
they normally use and what change would affect their interpretation. The audit
returns the complete native/2×/4× table, including failures. The researcher is
then asked three factual questions:

1. Did this reveal a sensitivity that your current workflow does not already
   check?
2. Is the correlation half-height length meaningful for this morphology?
3. What would have to change before this could be useful in your work?

A negative answer is still a valid documented pilot result. Genuine external
validation would be the owner's recorded technical criticism, a resulting
revision, and—only if true—their confirmation that the revised audit answered
a real measurement question. Access to a company, a placement or a polite
conversation is not itself validation.

## Deliberate stop rules

- The phase, scale, calibration, field, specimen or data rights are unclear.
- The owner cannot identify a measurement decision the audit could affect.
- A raw image needs an unvalidated segmentation before the proposed test.
- The chosen length remains unresolved for most fields.
- Slices or fields are being counted as independent specimens.
- The proposed comparison requires mapping Monte Carlo sweeps directly to
  hours or lattice sites directly to nanometres without a separate physical
  calibration.
- The equivalent analysis is already a routine check for the owner and adds no
  useful diagnostic.

## Position relative to existing work

Image coarsening, mixed pixels, phase segmentation and quantitative EDS phase
mapping all have substantial prior art. Eidel *et al.* explicitly distinguish
standard binary coarsening from mixed/interphase-pixel representations that
preserve phase fraction in image-based mechanics. EDS-PhaSe already converts
EDS elemental-map images into estimated composition maps and phase masks.
Recent EDS phase-fraction work also models measurement regions containing more
than one phase. Therefore this project's defensible contribution is not a new
segmentation system. The narrower candidate is a paired audit that connects an
exactly conserved simulation field to the separate effects of integration and
binary classification, then asks whether that distinction is useful in an
owner-defined measurement problem.

Primary references:

- B. Eidel, A. Fischer and A. Gote, “From image data towards microstructure
  information,” *ZAMM* 101 (2021),
  [doi:10.1002/zamm.202000245](https://doi.org/10.1002/zamm.202000245).
- D. Beniwal *et al.*, “EDS-PhaSe,” *Metallography, Microstructure, and
  Analysis* 12 (2023),
  [doi:10.1007/s13632-023-01020-7](https://doi.org/10.1007/s13632-023-01020-7).
- “Phase Fraction Estimation in Multicomponent Alloy from EDS Measurement
  Data,” *Materials* 17, 2322 (2024),
  [open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC11122778/).

These references bound the claim; they do not validate this repository's
method or establish novelty.
