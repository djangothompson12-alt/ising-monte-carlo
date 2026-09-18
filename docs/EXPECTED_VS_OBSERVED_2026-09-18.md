# Expected growth, measured growth, and the literature comparison

*AI-assisted comparison prepared 18 September 2026. This is a source-checked
research note, not a student-authored paper section or an independent review.
The student should verify the paper's methods and every interpretation before
using it in a report.*

## The question

For a conserved binary mixture undergoing diffusion-controlled late-stage
coarsening, the standard expectation is a characteristic length growing
approximately as `length ~ time^(1/3)`. That is an **asymptotic, conditional
expectation**, not a promise that every finite straight-line fit will equal
`1/3`. At different compositions, the domain shapes and growth amplitudes can
change even if the limiting exponent does not. See
[Bray's review, sections 2.5 and 7.3.3](https://www.thp.uni-koeln.de/krug/teaching-Dateien/WS2006/Bray.pdf).

[Majumder and Das (2010)](https://arxiv.org/pdf/1001.3985) report
`alpha = 0.334 +/- 0.004` for a **50:50**, two-dimensional, nearest-neighbour
Kawasaki Ising system at `0.6 Tc`. They argue that one-third behaviour is
visible early when an initial length is accounted for, and that finite-size
effects become prominent only when the measured domain length approaches a
substantial fraction of its eventual box-limited value. Their principal length
is a first moment of horizontal and vertical interface-to-interface chord
lengths after a local majority-spin filter; their multi-size scaling analysis
is not a direct fit of our raw correlation half-height length. Their `L=128`
example used **40** independent initial configurations and reached 4.5 million
Monte Carlo sweeps. That onset time is specific to their analysis, not a
threshold we can transfer to ours.

The later [Majumder and Das (2013)](https://arxiv.org/pdf/1305.2556) paper
already studies *composition* and temperature variation in two-dimensional
Kawasaki mixtures, including off-critical droplets. So our asymmetric
composition is not a new physical discovery by itself.

## What our controlled extension actually measured

Our completed main extension uses isotropic `Jx=Jy=1`, `0.65 Tc`, two fixed
`+1` fractions (`0.50` and `0.15`), four widths (`32, 64, 96, 128`), and
**16 independent seeded trajectories per condition**. Each of the 128
trajectories reaches one million attempted-exchange sweeps. The primary
length is the half-height crossing of a *connected* equal-time correlation,
averaged across directions, with no majority-spin filter. Each slope below is
a direct log–log fit of the ensemble-mean length over a declared finite
window; the intervals resample complete trajectories, not checkpoints.

| `+1` fraction, width | Nominal sweep window | Effective slope | 95% trajectory-bootstrap interval |
|---|---:|---:|---:|
| 0.50, 128 | 1,000–20,000 | 0.234 | 0.229–0.239 |
| 0.50, 128 | 1,000–200,000 | 0.256 | 0.251–0.262 |
| 0.50, 128 | 20,000–1,000,000 | 0.300 | 0.291–0.309 |
| 0.15, 128 | 1,000–20,000 | 0.235 | 0.228–0.241 |
| 0.15, 128 | 1,000–200,000 | 0.252 | 0.248–0.256 |
| 0.15, 128 | 20,000–1,000,000 | 0.281 | 0.268–0.293 |
| 0.15, 32 | 20,000–1,000,000 | 0.042 | 0.021–0.067 |

The [complete, unselected result table](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md)
also shows every size, all five fixed windows, actual sampled endpoints,
unresolved fits and the separately labelled `length/L < 0.15` sensitivity.
The nominal `200,000–1,000,000` window has only a 4.83-fold *actual*
time span and fails the study's declared fivefold minimum, so **none** of
those eight slopes is reported as resolved. The 32-wide, 50:50 length
becomes unmeasurable by this half-height rule at later times; we did not
replace missing lengths with zero.

## Did the result match the expectation?

**Partly, but not as a direct numerical replication.** The symmetric
128-wide slope rises from 0.234 in the early window to 0.300 in the broad
later window, moving toward one-third. The asymmetric 128-wide slope also
rises, but ends at 0.281. Both broad-window intervals remain below the
2010 paper's point estimate. Because the temperatures, length definitions,
filtering, time spans and fit forms differ, this numerical difference is
**not evidence against** their one-third finding. Conversely, our movement
toward one-third does **not prove** our asymptotic exponent is one-third.
The much flatter 32-wide asymmetric curve is consistent with size sensitivity,
but this study did not predeclare or establish an exact finite-size onset.

Several explanations may contribute; the data do not identify one unique
cause:

1. **Fitting and initial length.** A direct `log(length)` versus `log(time)`
   slope includes early-time offsets and transients. The 2010 scaling analysis
   treats a bare initial length explicitly. Shifting our fit start already
   changes the answer on the *same trajectories*.
2. **Different observables.** Our unfiltered connected-correlation 0.5
   crossing is not their filtered mean chord. On our 128-wide 50:50
   trajectories in the 1,000–200,000 window, alternative length definitions
   return different finite slopes (see the
   [working report](../manuscript/REPORT_DRAFT_2026-09-18.md)). That
   establishes method sensitivity here, not which definition is universally
   correct.
3. **Different physical settings.** `0.65 Tc` versus `0.6 Tc` changes the
   thermal interface noise and mobility. An off-critical 15:85 mixture has
   droplet-like rather than approximately bicontinuous morphology and a
   different box-limited length. Neither difference by itself predicts a
   precise slope correction.
4. **Time and box size.** Our million-sweep series ends before the 4.5-million
   point shown in the 2010 paper's 128-wide example, and our 32-wide
   off-critical system flattens while larger boxes continue to grow. Their
   finite-size threshold cannot simply be copied to our estimator or
   composition. More time alone would also eventually increase box effects;
   it is not an automatic cure.
5. **Statistical precision is not model equivalence.** Sixteen full
   trajectories per condition and trajectory-bootstrap intervals reduce
   sampling uncertainty. The 2010 paper used 40 at width 128. Our narrow
   intervals do not account for uncertainty in the model, observable, fit
   window or correspondence to an alloy.

The separately completed **40-run, 128-wide, `0.6 Tc`, 50:50 reference
campaign** matches more of the 2010 simulation settings, but no
student-approved, paper-method-matched chord analysis or multi-size collapse
has been released. Its existence must not be described as reproducing
`0.334` or the 4.5-million-sweep onset. See the
[source-to-code crosswalk](MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md).

## The defensible contribution and next test

The present result is a **reproducible measurement audit**: on conserved
trajectories, inferred growth depends materially on the chosen time window,
length observable and image observation operation. A new-seed, predeclared
image-operation check repeated the direction of an earlier block-and-threshold
effect, but the operation also changed apparent phase fraction; it is not a
microscope correction or validation against alloy ageing. Source code,
analysis rules, raw trajectories and declared tables are supplied in this
repository. All calculations remain subject to independent scientific review.

A focused reviewer question is: *Which length observable and treatment of
the initial length would make a fair, limited comparison to the 2010 paper,
without tuning after seeing the exponent?* A separate materials-imaging
question is whether the bounded resolution audit measures a feature an
engineer actually cares about on an approved dataset. Neither question is
settled by this note.
