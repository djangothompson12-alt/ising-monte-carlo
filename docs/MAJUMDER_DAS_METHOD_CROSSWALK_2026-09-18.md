# What the long L=128 run can and cannot compare with Majumder–Das

*AI-assisted source-to-code crosswalk, 18 September 2026. This is a reading
aid for the student, not his completed method declaration or a claim of
replication. The exact comparison remains gated by
`research/reference_benchmark.template.json`.*

Primary reference: [S. Majumder and S. K. Das, *Physical Review E* **81**,
050102(R) (2010)](https://doi.org/10.1103/PhysRevE.81.050102),
[open four-page preprint](https://arxiv.org/pdf/1001.3985). The paragraph
around Fig. 1 and Fig. 2 on preprint pp. 1–2 states most of the measurable
choices below. It does **not** fully specify every implementation detail.

| Dimension | What the paper establishes | What our separate completed campaign does | Residual mismatch/unknown |
|---|---|---|---|
| Dynamics | Conserved nearest-neighbour Kawasaki exchanges in a 2D square Ising lattice with periodic boundaries (p. 1). | Same class of proposed local moves, periodic 2D grid, `Jx=Jy=1`. | The short paper does not give a fully reproducible acceptance/RNG implementation. Our Metropolis acceptance and random proposal stream should be declared, not described as identical. |
| Composition and start | Symmetric 50:50 random start, direct quench to `0.6Tc` (p. 1). | Exactly fixed 50:50 random initial assignment; `equilibration=0`; target `0.6Tc`. | Our plan contains a nominal high initial temperature field but performs no high-temperature equilibration. Call it random, not equilibrated at that temperature. |
| Clock | One MCS contains `L²` attempted pair exchanges (p. 1). | One sweep contains `L²` attempted local exchanges. | Equal attempt counts are not physical seconds, nor proof of identical stochastic trajectories. |
| L=128 sample | Fig. 2 averages 40 independent initial configurations; Fig. 1 marks 4.5 million MCS as finite-size onset in their analysis (p. 2). | Forty independently seeded L=128 trajectories, each to 4.5 million sweeps; raw files passed the [integrity audit](REFERENCE_RUN_INTEGRITY_2026-09-17.md). | Their onset time is **their** measurement and model implementation, not a stopping rule or an onset finding for ours. Our run ends at that time and cannot show behaviour beyond it. |
| Noise removal | A local five-spin (site plus four nearest neighbours) majority replacement is described before physical-quantity measurement (p. 2). | `research/reference_measurements.py` performs **one simultaneous** periodic five-site pass on saved images only. | Paper does not unambiguously state pass count, simultaneous vs sequential update or whether every observable shares exactly the same filtered state. These choices can change the measured length. |
| Main length | First moment of a domain-length distribution where a length runs between successive x/y interfaces (Fig. 2 paragraph, p. 2). | `periodic_chord_lengths` pools all finite same-spin chords along both axes after one filter pass, then averages them. Tests check seams and the `L/2` stripe limit. | The paper does not specify uniform-line handling, pooling weights, histogram details or subpixel conventions. A plausible analogue is **not** an exact reconstruction. |
| Correlation | Fig. 2 inset shows a scaling comparison of `C(r,t)` divided in distance by measured `ℓ(t)` (p. 2). | Code also offers a raw periodic axis correlation after filtering. | Their directional/radial averaging and normalisation are not fully specified here; our off-critical primary analysis instead uses a **connected** half-height length. These must not be conflated. |
| Finite-size claim | Their Figs. 2–4 use several sizes and an adjustable initial bare length in the scaling analysis (pp. 2–3). | This reference campaign has **only L=128**. The separate completed 0.65Tc multi-size extension differs in temperature and observable. | One L cannot reproduce a multi-size collapse or establish their onset ratio. Their fitted `α=0.334±0.004` is not a value to impose on our data. |

## Why this matters for the report

The paper itself warns that fits can be sensitive to initial length and
oscillations in local exponent (preprint pp. 2–3). A matched comparison must
therefore specify what *our* measured quantity is before looking at a fitted
exponent. If the one-pass pooled-chord analysis differs from the paper's
unpublished implementation details, call it **paper-inspired measurement**.
This is still useful: the same saved trajectories can be analysed under the
primary connected-correlation method and a declared paper-inspired chord
method, quantifying observation dependence without pretending either is the
unique domain radius.

The paper's `ℓ_max≈L/2` belongs to its chord convention. On a synthetic
equal-width periodic stripe, our chord code also returns `L/2`; that tests an
important limit but cannot establish full method equivalence. Uniform scan
lines have no finite interface-to-interface chord and are omitted; a separate
first-zero correlation can remain unresolved on that stripe. These behaviours
are checked in `tests/test_reference_measurements_contract.py`.

## Student decision before the gated remeasurement

Read pp. 1–3 yourself, inspect one saved lattice and decide whether a
**one-pass simultaneous, pooled x/y chord** is an honest comparison target.
Record its unresolved ambiguities in the declaration. If yes, approve the
declaration with `student_verified=true` and keep `reviewer_status` as
`not_yet_reviewed` unless a real specialist has commented. If no, document
why and revise the analysis *before* calculating or inspecting the 40-run
chord fit. Either choice is defensible; a fabricated exact match is not.
