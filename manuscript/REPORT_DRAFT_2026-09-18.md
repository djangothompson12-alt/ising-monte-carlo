# What changes a measured coarsening rate in a conserved 2D lattice?

*AI-assisted working-paper draft, updated 18 September 2026 after the
million-sweep extension completed. This is **not** Django's final submitted
prose or an accepted paper. Every numerical statement needs Django's own
source check and wording decisions. The older `main.tex` remains a separate
historical manuscript; its PDF is stale. The new extension outputs are local,
not yet in the public GitHub snapshot.*

## Provisional abstract — Django to rewrite after checking the results

Conserved phase separation is often summarised by a domain length growing
approximately as time to the one-third power. A fitted slope from a finite
simulation need not measure that late-time law. This study uses a
two-dimensional nearest-neighbour Kawasaki model to test how the slope changes
with lattice size, fitting window and the definition of domain length. At
`0.65 Tc`, 64 independent runs across four widths and two compositions were
followed to 200,000 Monte Carlo sweeps. For widths 64–128, fitting the
connected-correlation half-height length from about 1,000 sweeps gave slopes
near 0.26 at both compositions. At width 128 and 50:50 composition, including
the earliest times changed the fitted value from 0.258 to 0.197. Alternative
length measures and synthetic image-processing steps also changed fitted
values on the **same** saved configurations; a fourfold block-and-threshold
operation lowered the image-based slope by about 0.056–0.072 in the original
ensemble, with a similar shift in a small fresh-seed repeat. The completed
extension added 16 new trajectories per composition and lattice width, each
to one million sweeps. At width 128, the 20,000–1,000,000-sweep effective
slopes were 0.300 at 50:50 and 0.281 at 15:85, while the smallest 15:85
system visibly flattened. A fixed new-seed image-operator test repeated the
earlier negative shift in both compositions, but the operation also changed
apparent phase fraction. These results show finite-run time, size and
measurement sensitivity within this model, not a demonstrated asymptotic law
or an alloy-ageing prediction.

## 1. Question and materials context

Some binary alloys develop regions of different composition during heat
treatment. Their size, spacing and shape matter because microstructure can
affect later properties. The aim here is not to predict a named alloy from a
two-dimensional grid. It is to examine a simpler question first: if the
underlying simulated configurations are unchanged, how much can a reported
coarsening rate move when the measurement or fitting choice changes?

The project began with Metropolis single-spin flips, which do not conserve the
number of +1 sites, and moved to nearest-neighbour Kawasaki exchanges, which
do. That conservation makes the second model a minimal analogy for a binary
mixture with fixed overall composition. The distinction is more useful than
calling either update a literal atomistic ageing process. The expected
late-time exponent for ideal diffusion-controlled conserved coarsening is
one-third under its usual assumptions; see [Bray 1994](https://doi.org/10.1080/00018739400101505).
The scaling argument is physical rather than a rule imposed by the code:
for a typical domain length `ℓ`, interface curvature creates a chemical-
potential difference of order `γ/ℓ`; spreading that difference over a
distance `ℓ` makes a diffusive current, and hence a boundary speed, scale
roughly as `dℓ/dt ∝ 1/ℓ²`. Integrating gives `ℓ³ ∝ t`. This assumes a
late-stage, single-length scaling regime and suitable transport; it says
nothing about which finite interval of Monte Carlo sweeps first satisfies
those assumptions. Bray sets out this argument in section 2.5 of the
review, not as a fit to this particular simulation.
Bray also distinguishes the predicted late-stage growth law, which does
not change with phase volume fraction under that scaling picture, from
the scaling functions and morphology, which do. Comparing our two
finite-window slopes therefore does not by itself test the full
asymptotic statement.
Earlier two-dimensional Kawasaki work has already studied finite size,
composition, thermal noise and length definitions—particularly
[Majumder and Das 2010](https://doi.org/10.1103/PhysRevE.81.050102),
[2011](https://doi.org/10.1103/PhysRevE.84.021110) and
[2013](https://doi.org/10.1039/C3CP50612F). The question here is therefore
**not** whether off-centre mixtures or below-one-third finite-window slopes
exist for the first time. It is whether a controlled, paired measurement audit
on reproducible trajectories makes a useful distinction between changing
dynamics and changing what the observer reports. Independent review is needed
to judge that contribution against prior work.

There is also direct materials-characterisation precedent for the practical
warning: [Ezad et al. (2022)](https://doi.org/10.2138/am-2021-7797)
found that manual versus automated measurement could change the kinetic
interpretation of experimental grain-growth data. Their material, length
definition and growth-law fit differ from ours, but the broader point that
image analysis can alter a fitted kinetic result is not new. A fuller
[prior-art comparison](../docs/LITERATURE_COMPARISON_2026-09-17.md)
sets out this limit.

The square-lattice interaction can also be translated into an approximate
regular-solution free energy. The [checked mean-field binodal and spinodal](../docs/REGULAR_SOLUTION_BINODAL_2026-09-18.md)
help place the quenches in a materials phase-diagram vocabulary, while the
[exact infinite-2D coexistence boundary](../docs/EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md)
shows that the approximate critical temperature is not the exact lattice
critical temperature. Neither curve is a phase diagram for Fe–Cr or another
real alloy. A [published Fe–Cr microscopy/hardness study](../docs/FECR_MATERIALS_CASE_STUDY_2026-09-18.md)
is relevant context for why domain measurements matter, not a calibration of
this model to hardness or ageing hours.

## 2. Model and measurement methods

The Model B lattice is `L × L` with periodic boundaries and spins `s=±1`.
Horizontal and vertical nearest-neighbour couplings can differ, although
the controlled campaign fixed both at `Jx=Jy=1`. An attempted move chooses a
nearest-neighbour pair and exchanges its spins with the Metropolis probability
`min(1, exp(-ΔE/T))` in reduced units (`k_B=1`). A sweep consists of `L²`
**attempted** exchanges. Equal-spin exchanges do nothing; acceptance is not
guaranteed. Because a swap preserves the sum of the two spins, total
magnetisation and both species counts remain exactly fixed. Numerical checks
compare local energy changes with a full Hamiltonian and test a tiny
fixed-composition transition matrix against its Boltzmann distribution. These
verify defined parts of the code; they do not validate its use as a real
alloy.

More explicitly, each horizontal and vertical bond is counted once in

`H = −Jx Σ_(horizontal bonds) s_i s_j − Jy Σ_(vertical bonds) s_i s_j`.

The exact critical temperature of the **isotropic 2D square-lattice Ising
equilibrium model**, in these units, is `Tc = 2J/ln(1+√2) ≈ 2.269` for
`J=1`. Thus `0.65 Tc` is about `1.475` model temperature units, not a
particular number of kelvin for an alloy. Kawasaki and single-flip updates
share this equilibrium interaction but have different transport dynamics.

The main campaign quenched from approximately `3 Tc` to `0.65 Tc` after 200
high-temperature sweeps. It used widths `32, 64, 96, 128`, nominal +1
fractions `0.50` and `0.15`, and eight fresh seeds per condition: 64
trajectories in total, each reaching 200,000 sweeps. The actual +1 fraction
was fixed to an integer count on each lattice and saved with its seed and
configuration. Sixty unique integer checkpoint times were retained from the
64 requested logarithmic samples. The manifest records the frozen source
hashes and numerical-library versions. The independent statistical unit is a
whole trajectory, not a checkpoint, pixel or crop. See the
[data dictionary](../research/DATA_DICTIONARY.md) and
[prospective protocol](../research/PROTOCOL.md).

At each checkpoint the engine computes periodic directional spin correlations.
For Model B at off-centre composition, it subtracts the constant
magnetisation background and divides by the spin variance, giving a
normalised connected correlation with value one at zero distance. The primary
length is the first interpolated distance where each direction falls below
0.5; the two directional values are averaged. If either crossing is absent,
the result is unresolved, not set to zero. **This is deliberately not the
established Model A raw-correlation observable.** Model A's magnetisation
changes during ordering, so replacing its earlier raw statistic would alter
the analysis rather than make a neutral correction.

For either lattice direction, the saved Model B statistic is
`C(r) = [⟨s_i s_(i+r)⟩ − m²]/[1 − m²]`, where the average uses every site
with periodic wrapping and `m = L^(−2) Σ_i s_i`. The mean magnetisation is
constant along a Kawasaki trajectory. I take the first crossing of
`C(r)=0.5`, interpolate between adjacent integer separations, and average
the horizontal and vertical crossing distances. This is an operational
domain *length*, not the radius of a particular precipitate.

The effective exponent is a straight-line slope of `log(ensemble mean
length)` against `log(sweep count)` inside a stated window. It is not the mean
of per-run slopes. Complete trajectories are resampled for 500 bootstrap
draws. Those intervals describe replica variation conditional on the chosen
observable and fit mask; they do not include uncertainty about the model or
about which window to choose. The original protocol compared windows
beginning at 2, 100 and 1,000 sweeps. A heuristic `length/L < 0.15` filter
was applied; later results show it cannot guarantee the absence of finite-size
effects.

Four other saved-state measurements were compared on the same configurations.
In a separate **finite-image** study, the saved ±1 images were cropped,
blurred, binned or thresholded without advancing the simulation. This image
method counts only within-frame pixel pairs, estimates the observed image
mean and never joins opposite image edges. Its half-height length is therefore
not numerically identical to the periodic engine length. The original
image study used eight L=128 runs per composition; an independent four-run
repeat per composition used new seeds and a shorter 20,000-sweep duration.
The two time grids differ, so comparisons are paired **within**, not across,
ensembles. The full observation protocol and source are
[here](../research/IMAGING_PROTOCOL.md).

A separately planned extension kept the same isotropic coupling,
compositions and four widths, but used 16 **new** seeds per group and ran to
one million sweeps, producing 128 trajectories and 75 distinct saved
checkpoints per trajectory. Its five nominal fitting windows, requirement of
at least four jointly resolved checkpoints spanning a factor of five, and
whole-trajectory bootstrap were fixed before the run. Primary fits do not
filter by `ℓ/L`; the old `ℓ/L < 0.15` rule is a sensitivity analysis only.
Lengths at different sizes were also compared at identical sweep counts,
requiring every replica in both groups to resolve. See the [extension
protocol](../research/MAIN_EXTENSION_PROTOCOL.md) and
[matched-size addendum](../research/MAIN_EXTENSION_MATCHED_SIZE_ADDENDUM_2026-09-17.md).
An independently coded check rebuilt every declared fit, ensemble and
matched-size table row from the raw snapshots. A separate archive audit
recomputed all 19,200 directional lengths. One strict half-height decision
at the maximum available separation changed between two FFT calculations
because values on opposite sides of exactly 0.5 differed by about
`2 × 10⁻¹⁶`; the saved length agrees with the saved correlation. This
rounding ambiguity is recorded rather than silently counted as a physical
measurement disagreement.

After the earlier image effect had been seen, a fixed new-seed test was
specified on the extension's 32 width-128 trajectories. It compared full
native images with the same fourfold block-average-and-threshold operation,
using common resolved checkpoints and paired whole-trajectory resampling.
The primary window was 1,000–20,000 sweeps; 1,000–200,000 was a secondary
sensitivity check. The protocol was written before these new-seed image
measurements were opened, but **after** the earlier effect was found, so this
is a directional repeat rather than a blind first test. It retained the
apparent phase fraction before and after processing. See the [fixed holdout
protocol](../research/PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md).

## 3. Results from completed runs

### What the domains look like

The [fixed-selection microstructure panels](../figures/fig_archived_morphology_v1.png)
show the first archived `L=128` replica at each of the two compositions,
at exactly 1,069 and 200,000 sweeps. The 50:50 case forms broad,
interwoven regions; at 15:85 the minority phase appears mainly as
separated patches. Both visibly coarsen, but these panels are examples,
not ensemble evidence or images of a real alloy. The selection was set by
replica number and saved time, not by which picture looked most persuasive;
the [figure provenance](../figures/fig_archived_morphology_v1.json) records
the raw-file hashes and seeds. The length and slope comparisons below use
independent trajectories rather than reading numbers from these four panels.

### Window and size

For widths 64, 96 and 128, the nominal 1,000–200,000-sweep fit returned
effective exponents between 0.257 and 0.263 for each studied composition.
Every one of those rows used eight independent trajectories and 28 jointly
retained checkpoints, actually spanning 1,069–200,000 sweeps. The result is
not a one-third plateau. At `L=128,c=0.50`, the value was 0.197 when fitted
from sweep 2, 0.233 from sweep 100 and 0.258 from sweep 1,000, all ending
nominally at sweep 200,000. These overlapping fits show why a single slope
cannot be quoted without its time window. The [checked growth figures and
table](../docs/OVERNIGHT_RESULTS.md) contain the intervals and every size.
The [compact window figure](../figures/fig_core_window_sensitivity_v1.png)
redraws the two L=128 composition groups from that table; its bars are 95%
whole-replica bootstrap percentiles, not independent-window errors.
Because those windows share the same eight runs, a separate
[paired post-result audit](../docs/PAIRED_WINDOW_AUDIT_2026-09-18.md)
resampled complete trajectories with the same replica indices in both fits.
At `L=128`, moving the fit start from sweep 2 to 1,000 increased the fitted
exponent by 0.061 [0.057, 0.065] at 50:50 and 0.064 [0.057, 0.071] at
15:85, with 95% conditional paired-bootstrap intervals. This is evidence of
a stable window effect *in these archived runs*, not an estimate of when the
asymptotic regime begins.

The smallest width behaves differently at late time. For `c=0.15,L=32`, the
mean threshold length flattens near four sites and ends around 4.18 sites,
whereas the 96- and 128-site systems end around 5.57 and 5.69 sites.
For `c=0.50,L=32`, 35 saved directional lengths are unresolved, and its
nominal late fit actually stops at sweep 34,974. It must not be set beside a
200,000-sweep large-lattice fit as though they covered the same time. A
candidate `z=3` rescaling also fails to collapse all curves over the full
plotted range. The evidence supports a smaller-box problem **and** a shared
time-window drift; it does not show that finite size alone explains the
below-one-third values. The completed extension tests those possibilities
with more runs and matched-time size comparisons.

### The completed million-sweep extension

The 128 new trajectories passed the saved-file, seed, source-hash, fixed-
composition and energy-accounting checks. The first archived heat interval
was also replayed for every file from its seeded pre-quench state. These are
internal implementation checks, not experimental validation. All 80 declared
fit rows and 450 matched-size rows were independently recalculated; the
[complete local appendix](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md)
shows every window, including unresolved ones. Its underlying large raw
archive and analysis have **not** yet been published to GitHub.

For `L=128`, the primary unfiltered connected-correlation fits were:

| +1 fraction | Nominal sweeps | Actual sweeps | Effective α | 95% whole-replica interval |
|---:|---:|---:|---:|---:|
| 0.50 | 1,000–20,000 | 1,091–17,913 | 0.234 | 0.229–0.239 |
| 0.50 | 1,000–200,000 | 1,091–173,983 | 0.256 | 0.251–0.262 |
| 0.50 | 20,000–1,000,000 | 21,336–1,000,000 | 0.300 | 0.291–0.309 |
| 0.15 | 1,000–20,000 | 1,091–17,913 | 0.235 | 0.228–0.241 |
| 0.15 | 1,000–200,000 | 1,091–173,983 | 0.252 | 0.248–0.256 |
| 0.15 | 20,000–1,000,000 | 21,336–1,000,000 | 0.281 | 0.268–0.293 |

These overlapping-window fits show a later-window increase at both
compositions. They do **not** demonstrate convergence to one-third, and the
bootstrap intervals do not include uncertainty from selecting an observable
or window. All eight `200,000–1,000,000` primary size/composition fits were
unresolved under the *predeclared* factor-of-five time-span rule: the first
saved point was 207,231 sweeps, so the retained time ratio was only 4.83.
It would be misleading to quote a late-window slope by quietly relaxing that
rule. The broader 20,000–1,000,000 window remains a finite-time average,
not a late-time asymptotic measurement.

At 15:85, the `L=32` mean length flattened near 4.1 sites while `L=128`
reached 8.64 at one million sweeps; their matched-time length ratio was
0.475 [0.448, 0.505] at that last checkpoint. This is a clear small-box
departure *in this observable and campaign*. At 50:50, the smaller systems
instead developed missing half-height crossings: all 16 trajectories were
jointly resolved at only 56 of 75 checkpoints for `L=32`, 65 for `L=64`,
and 74 for `L=96`, against 75 for `L=128`. Their late fits cannot be
compared as though they all reached one million sweeps. The
[matched-time plots](../research/runs/main_065_multisize_v1/analysis_declared_v1/matched_size_ratios_c1.png)
show a departure, but do not specify the first physical onset of finite-size
effects; `L=128` is not an infinite-size reference.

### Length definition and observation

On the same `c=0.50,L=128` trajectories and nominal 1,000–200,000 window,
the connected-correlation half-height, positive-lobe, full-spectrum moment
and inverse-interface measurements gave 0.258, 0.251, 0.167 and 0.204,
respectively. They weight structure differently and should not be treated as
four estimates of a known particle radius. A [separate arithmetic audit](../docs/ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md)
recomputed the saved observables from archived states; agreement checks the
calculation, not the physical suitability of one length definition.

In the shorter image study's primary 1,000–20,000-sweep window, fourfold
block averaging **followed by binary thresholding** shifted the fitted
image-length exponent by −0.056 at `c=0.50` and −0.072 at `c=0.15` in the
original ensemble. The fresh-seed repeat gave −0.057 and −0.073. Those are
changes in a fitted *measurement* on unchanged dynamics. They are not a
universal microscope correction: the fresh study had only four replicas per
composition, the exact retained time grids differ, and the treatment changes
apparent phase fraction as well as resolution. Cropping showed less stable
behaviour. See [all treatments and uncertainty intervals](../docs/MEASUREMENT_STUDY_RESULTS.md).
The [compact paired-shift figure](../figures/fig_core_observation_shift_v1.png)
keeps the original eight-run and fresh four-run ensembles separate. Its
horizontal intervals are 95% whole-replica bootstrap percentiles of the
treatment-minus-reference slope. They do not cover observation-method or
fit-window selection uncertainty, and its absolute image exponent is not
the periodic-engine exponent plotted in the window figure.

Two later checks sharpen, rather than inflate, that conclusion. A
[post-result decomposition](../docs/BINNING_DECOMPOSITION_RESULTS_2026-09-17.md)
found that the relative contribution of block integration and thresholding
depends on composition and fit window. A deliberately simple
[known-growth control](../docs/SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md)
gave the image estimator a geometric `t^(1/3)` pattern. Its finite-image
fitted value at a 384-site field was 0.355, moving toward 0.333 as the field
grew. Downsampling barely shifted **that** aligned square pattern. This
does not explain the Kawasaki low slopes: the control is not Kawasaki
dynamics, uses a different estimator, and its finite-window bias has the
opposite sign. It shows why a measurement pipeline should be checked against
known inputs and why one observed operator effect should not be made
universal.

The fixed **new-seed** width-128 holdout repeated the sign of the earlier
selected fourfold block-average-and-threshold effect in both compositions.
In its primary 1,000–20,000-sweep window, the bin-minus-native fitted shifts
were `−0.056` [−0.059, −0.053] at 50:50 and `−0.074` [−0.077, −0.069]
at 15:85; these are paired whole-trajectory bootstrap intervals from 16
new runs per composition. The original eight-run values were `−0.056` and
`−0.072`, and the first four-run fresh-seed values were `−0.057` and
`−0.073`. These three different ensembles agree in direction, but their
different saved time grids must not be pooled as one trial. The holdout's
secondary 1,000–200,000-sweep shifts were smaller in magnitude, `−0.036`
and `−0.050`. Crucially, processing changed the mean apparent +1 fraction
over the primary common-fit checkpoints from 0.5000 to 0.5214 at 50:50,
and from 0.1500 to 0.1290 at 15:85. Resolution and apparent composition
therefore changed together in this binary observation step. The [full local
holdout report](../research/runs/main_065_multisize_v1/image_holdout_v1/REPORT.md)
keeps the uncertainty, actual windows and unresolved counts visible. This
is stronger repeatability evidence *within the simulation* than the earlier
four-run repeat, but it remains neither a blind discovery nor a claim about
a particular microscope or alloy.

## 4. Real-image feasibility and engineering relevance

The transfer question is whether a declared measurement-sensitivity check
could help an imaging researcher decide whether a reported microstructure
length is stable enough to use. It is not whether a 2D Kawasaki lattice can
predict a particular alloy's strength or ageing hours. Five published
Al–Ge tomography slices were inspected as a feasibility case. Their
background, dimensions and recovered scale metadata were not sufficiently
comparable to justify an experimental growth exponent. No such exponent is
reported. On a separate set of 42 published **static** steel annotations,
reducing the resolution of the producer masks changed the measured
correlation length; a fourfold reduction gave a median coarse/native ratio
of 1.050 under the declared tie rule. Those images may share specimens and
have no calibrated physical length in this analysis. Neither case validates
the Ising kinetics or represents outside lab use. Their value is to expose
the practical metadata, segmentation and sampling decisions that a real
pilot must settle first.

The distinction has a real materials example. Published Fe–Cr ageing
studies report changing Cr-rich morphology, decomposition wavelength and
hardness, while different microscopy methods can return different feature
sizes. The [source-checked Fe–Cr case note](../docs/FECR_MATERIALS_CASE_STUDY_2026-09-18.md)
keeps their measured nanometres, hours and hardness separate from our
dimensionless lattice sites and sweeps. It gives a reason to care whether
one length definition is stable, not a route to calibrate the model by
matching one fitted slope.

The steel-mask comparison also changed the practical direction of the work.
The simple thresholded photographs did not recover the producer masks'
correlation length reliably, so a proposed local
[mask-resolution audit](../docs/MASK_RESOLUTION_AUDIT.md) now starts from a
declared binary phase mask and physical pixel size rather than claiming to
segment a new material correctly. It reports the same field at native, 2×
and 4× resolution, including unresolved measurements and the chosen tie rule.
This is a tested workflow prototype, not a result from a partner laboratory;
whether it answers a real measurement decision remains an open question.

A separate [Fe–Cr methods paper by Xu et al. (2016)](https://doi.org/10.1007/s11661-016-3800-4)
reported an effective $t^{0.16}$ for the inverse SANS-peak wavelength and
$t^{0.27}$ for a Guinier-derived particle radius in its 35Cr alloy at
773 K. These are different structural quantities, and the particle-radius
conversion assumes spherical particles; the numerical difference is not a
clean image-processing experiment or a validation target for this simulation.
It is further reason to state the observable whenever I quote an exponent.

A further [bounded check on public segmented Al–Ge tomography](../docs/ALGE_REAL_IMAGE_AUDIT_2026-09-18.md)
tested the exact 4× observation step on real solid-state-aged alloy images.
It is an exploratory transfer of the *measurement question*, not a kinetics
comparison: all four stages are from one specimen, their fields shift, and
the source authors already analysed 3D feature evolution. Seven of eleven
fixed interior planes at 15 minutes contained no Ge, so the correlation
length was undefined; a 105-minute plane also became unresolved after
binning. The two later stages yielded descriptive static length ratios,
not a growth exponent. The failure cases make ROI selection and the
physical meaning of the measured feature specific questions for an external
microscopist rather than details to hide.
The [all-plane display](../figures/fig_alge_fixed_plane_audit.png) leaves
those failures visible alongside the resolved static ratios.

There is a more basic materials distinction too. The source authors
separated Ge lamellae from later Ge precipitates before analysing their
three-dimensional morphology, and identified an additional Fe/Ni-bearing
phase. They associated the hardness history with competing recovery,
lamellar coarsening and precipitation processes, using a separately prepared
sample for hardness. Our all-Ge, two-dimensional
correlation length combines rather than isolates those features. It cannot
be relabelled as a precipitate radius or used to infer strength; a reviewer
needs to say whether a *population-specific* resolution audit would help.
The cast eutectic starting structure is also unlike our random high-temperature
lattice quench.

## 5. Discussion and pending decisions

The completed result is strongest where the same saved microstructures are
measured in more than one declared way. It establishes a reproducible
finite-run *sensitivity*, not the cause of the physical transient or the
late-time exponent. The model is 2D, binary, nearest-neighbour and
vacancy-free, with no strain field, real diffusion coefficient or calibrated
time/length mapping. The experimental-image checks do not bridge that gap.
Published work has already analysed coarsening, multiple length definitions
and image-processing bias; a specialist needs to judge whether this narrower
paired growth-fit study is useful enough for a paper or best presented as a
technical report.

The 40 completed `0.6 Tc,L=128` trajectories are **not** called a reproduction
of Majumder and Das: a student-checked measurement-method declaration is
still outstanding, and one width cannot reproduce their size study. The
separate 0.65 Tc extension is now complete and reported above under its
[frozen protocol](../research/MAIN_EXTENSION_PROTOCOL.md) and
[matched-size addendum](../research/MAIN_EXTENSION_MATCHED_SIZE_ADDENDUM_2026-09-17.md).
It supports a finite-time rise of the fitted slope at larger sizes and an
additional small-box problem, most clearly at 15:85 and `L=32`. It does not
establish a universal one-third plateau or a numerical onset time. Indeed,
the narrowest nominal late window failed the predeclared time-span criterion
in every group.
An additional [fixed image-operator holdout protocol](../research/PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md)
was written while the extension was incomplete. Its post-completion test
repeated the earlier effect's direction on new seeds, but its phase-fraction
changes limit any claim about resolution alone. The selected effect was
already observed before this protocol, so this is not a blind first discovery.

## Data, assistance and review status

The code, plans, tests and selected completed main-study trajectories are in
the repository; see [the data guide](../research/DATA_README.md). The new
reference and extension data are local and not yet in a reviewed public
release. This draft, its checks and much of the code were developed with
generative-AI assistance, recorded in
[AI use and contributions](../AI_USE_AND_CONTRIBUTIONS.md). Before sharing or
submitting a paper, Django needs to verify the sources, rerun the results he
uses, choose the claims, write or substantially revise the prose himself,
and check the destination's AI policy. No academic or industry partner has
endorsed, adopted or independently validated the work.

## Questions to answer before this becomes a paper

1. Which single figure carries the main result, and could you explain its
   length definition, independent-run count and missing-value rule aloud?
2. Does the longer extension separate a shared time drift from a size-specific
   departure at matched sweeps? If not, say so.
3. Which result survives a change of observable or observation pipeline, and
   which does not? Why is that difference worth a materials reader's time?
4. After reading the primary prior work, what is genuinely added here?
5. What specific microstructure decision would an imaging researcher test
   with the bounded audit, and what negative result would stop the pilot?
