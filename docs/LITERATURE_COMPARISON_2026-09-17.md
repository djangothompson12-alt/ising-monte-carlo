# What the Majumder–Das papers already did, and what this project tests

Source-checking note, 17 September 2026. This is an AI-assisted reading aid,
not a novelty verdict or text to submit as the student's own literature review.
The paper versions linked below were inspected directly; the student should
check the cited pages and ask a specialist about any claimed method match.

**18 September update:** For the completed 128-run `0.65Tc` extension and a
short expected-versus-observed table, read
[this result comparison](EXPECTED_VS_OBSERVED_2026-09-18.md). The older
eight-replica study mentioned below remains a separate historical dataset.

## The essential correction

**Temperature and composition dependence in a 2D Kawasaki Ising mixture was
already studied by Majumder and Das in 2013.** The present 50:50 versus 15:85
comparison is not, by itself, a new test of whether composition changes the
asymptotic growth exponent. Their work includes off-critical droplet morphology,
multiple length definitions and finite-size scaling. This project's possible
contribution is narrower: a reproducible, paired audit of how a finite-run
growth estimate changes with the length observable and with a declared image
observation pipeline, plus a candid test of whether available real images can
support the same measurement. Whether that is sufficiently original or useful
for a journal is a question for an independent reviewer.

## Bray's actual claim and the finite-run gap

In [Bray's 1994 review, section 2.5, printed pp. 370–371](https://www.thp.uni-koeln.de/krug/teaching-Dateien/WS2006/Bray.pdf),
the conserved-field one-third law follows from a *late-stage single-length*
argument: curvature sets a chemical-potential scale, and diffusive current
sets the interface speed. Bray also notes that simulations commonly need
extrapolation to reach this scaling regime. Later, in section 7.3.3
(printed pp. 442–443), the review says the conserved off-critical growth
law is independent of phase volume fractions **while the scaling functions
are not**, conditional on late-time scaling. This is the precise theoretical
context for the composition sweep—not a promise that a 2–200,000-sweep
straight-line fit must equal one-third. The review's dilute LSW droplet
derivation is not a licence to treat its three-dimensional radius
distribution as an exact benchmark for connected components in this 2D
lattice.

## Source-by-source comparison

| Work | What was actually done | Relation to this project |
|---|---|---|
| [Majumder & Das 2010](https://doi.org/10.1103/PhysRevE.81.050102), [open preprint](https://arxiv.org/pdf/1001.3985) | Two-dimensional, symmetric 50:50 conserved Ising study, T=0.6 Tc, periodic boundaries and Kawasaki exchange. L=32, 64, 128 growth curves used 2,000, 1,000 and **40** independent initial configurations, respectively. Their main length was the first moment of distances between successive x/y interfaces after a majority-spin noise filter. They fitted an initial bare length in a finite-size scaling analysis and report a 1/3-compatible exponent and weak size effects. | The completed L=128, 40-run, 0.6 Tc campaign matches several stated settings, but the RNG, exact filtering and chord weighting have not been established as identical; see the [method crosswalk](MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md). Its initial assignment is random and fixed-composition, not equilibrated at a high temperature. One size cannot reproduce their multi-size collapse or onset criterion. Our completed 0.65 Tc, eight-replica per group study has different temperature, observable, run length and ensembles. See [preprint pp. 1–3](https://arxiv.org/pdf/1001.3985#page=2). |
| [Majumder & Das 2011](https://doi.org/10.1103/PhysRevE.84.021110), [open preprint](https://arxiv.org/pdf/1101.4524) | Extends the early-time/finite-size analysis to 2D and 3D. Uses Metropolis-accepted nearest-neighbour exchanges, periodic boundaries and a majority-spin post-filter. Explicitly compares chord distribution, correlation and spectrum lengths; discusses thermal noise, initial-length subtraction and misleading direct log–log slopes. For its 2D T=0.6 Tc size plot, L=32 and 64 use 1,000 starts each and L=128 uses 40. | This is substantial prior art for **observable choice and noise handling**; merely comparing several definitions cannot be sold as unprecedented. Our current primary length is a connected-correlation **0.5 crossing**, whereas their main length is a filtered chord mean and their correlation diagnostic uses a first **zero** crossing. The paired original/fresh image-operator study asks a different, narrower question. See [methods pp. 2–3](https://arxiv.org/pdf/1101.4524#page=3) and [Fig. 6 discussion](https://arxiv.org/pdf/1101.4524#page=6). |
| [Majumder & Das 2013](https://doi.org/10.1039/C3CP50612F), [open preprint](https://arxiv.org/pdf/1305.2556) | Studies temperature and **composition** variation in 2D conserved Ising simulations, including 10:90 droplets at T=0.53 Tc. Uses a majority-spin filter and compares first-zero connected correlation, spectrum and chord lengths; reports similar scaling-law behaviour at moderate temperatures and lower early-time growth at sufficiently low temperature. | This directly removes any claim that exploring an asymmetric mixture or finding a low early slope is new. Our c=.15 and T=.65 Tc settings are not a direct replication of their c=.10 and T=.53 Tc examples. Their paper provides a much better prior-art comparator for the composition section. See [methods pp. 2–3](https://arxiv.org/pdf/1305.2556#page=3) and [composition results pp. 6–8](https://arxiv.org/pdf/1305.2556#page=7). |
| [König, Ronsin & Harting 2021](https://doi.org/10.1039/D1CP03229A), [open preprint](https://arxiv.org/pdf/2107.07234) | Uses a **different conserved model**, a two-dimensional Cahn–Hilliard phase field with symmetric Flory–Huggins thermodynamics and constant mobility. Across compositions, the authors report approximately 1/3 at 50:50, 0.30 at 25:75 and 0.26 at 40:60 using a structure-factor length with explicit initial time/length treatment. Their interfacial-energy estimate gives exponents about 0.02 higher than their structure-factor estimate. | This is strong prior art for both composition/morphology claims and observable-dependent fitted exponents. It cannot be used to assign our 0.26 to the same mechanism: our Kawasaki moves, 15:85 composition, correlation half-height and direct finite-window log slope differ. It also warns against assuming that *every* off-critical sub-1/3 fit must disappear with longer runs. See [introduction and methods](https://arxiv.org/pdf/2107.07234#page=2) and [results pp. 6–7](https://arxiv.org/pdf/2107.07234#page=6). |

## Method choices that must not be conflated

1. **Simulation versus observation.** A majority filter changes a snapshot for
   measurement, not the conserved Kawasaki dynamics. This repository's
   `research/reference_measurements.py` makes one simultaneous periodic
   five-site pass only on saved states. The papers specify the local rule, but
   the exact pass schedule and all weighting conventions need specialist review.
2. **A length is not a unique physical radius.** The literature's filtered
   chord first moment, first-zero correlation and structure-factor measures
   are not the same as `model_b/kawasaki_engine.py`'s connected-correlation
   half-height crossing. Different amplitudes and finite-window slopes do not
   establish a contradiction without comparing the full measurement methods.
3. **The two onset times are not interchangeable.** The 2010 preprint marks a
   T=.6 Tc, L=128 finite-size-effect example around 4.5 million sweeps; the
   broader 2011 paper shows a different 2D example around 350,000 sweeps.
   Neither number is a universal cutoff for this code, another observable, or
   the c=.15 case. Report each with its paper and estimator context.
4. **An initial-length offset matters.** Their collapse treats a bare length
   and microscopic time explicitly. Our present log–log window fits do not
   thereby disprove early 1/3 scaling. A matched comparison must show a
   declared, non-tuned initial-length sensitivity and explain its assumptions.
5. **Composition was studied before.** The honest novelty question is whether
   our paired observation-pipeline test and reproducible uncertainty accounting
   reveal a useful *methodological* risk not already quantified in these works.
   The answer is not established by this note or by a small bootstrap interval.
6. **The literature is not unanimous across model classes.** The 2021
   Cahn–Hilliard study reports a composition-dependent late-stage exponent in
   its own model and shows a smaller but real observable dependence. That
   neither disproves Bray's scaling argument nor validates our finite-window
   slopes. It makes "finite time/size must be the whole explanation" too
   strong. A reviewer should help decide which model assumptions and length
   definitions are actually comparable.

## Image-analysis prior art is substantial too

[Ezad et al. (2022)](https://doi.org/10.2138/am-2021-7797) are an especially
important comparison, not merely a generic segmentation citation. In
experimental spinel–orthopyroxene grain-growth data they compared manual
and automated grain identification, fitted growth kinetics and found that
the fitted kinetic parameter and plausible mechanism could change with the
measurement method (see their discussion around the two approaches and
longest-duration specimen). This is **not** conserved Ising phase separation,
and their fit uses `G^n−G0^n=kt`, not our finite-window log slope. But it
removes any broad claim that this project first showed that image analysis
can change an inferred coarsening mechanism. The narrower possible
contribution is a paired, controlled numerical audit on conserved
trajectories, with the observation operator and the effective exponent
specified exactly.

[Tiwari and Tewari (2010)](https://doi.org/10.1016/j.matchar.2010.02.005)
quantified resolution-dependent error in simple 2D bitmap feature
measurements. [Eidel (2021)](https://doi.org/10.1002/zamm.202000245)
separates image-resolution effects from later numerical-discretisation
error and explicitly compares pixel averaging with a phase-preserving
majority rule. These are additional reasons to keep *block averaging* and
*binary thresholding* separate in our discussion. Neither paper reports
this project's particular Kawasaki growth-fit shift, but their concepts
and much of the motivation are prior art.

[Chan et al. (2020)](https://doi.org/10.1038/s41524-019-0267-z) explicitly
study how voxel size, noise and thresholding affect downstream 3D
microstructure/grain-size measurements. [Stuckner et al. (2022)](https://doi.org/10.1038/s41524-022-00878-5)
compare segmentation quality with precipitate-size and area measurements.
[Sun et al. (2017)](https://doi.org/10.1016/j.actamat.2017.04.054)
already use two-point spatial correlations on time-resolved Al–Cu tomography
and compare extracted characteristic dendrite lengths with direct
measurements. The [related segmentation paper](https://doi.org/10.1186/2193-9772-3-6)
details registration and boundary-accuracy problems on that 4D material.
None of these papers tests this repository's **same-trajectory fitted coarsening
exponent**, but they make clear that processing-induced measurement bias is
not a new general concept. The possible contribution here is a narrow,
reproducible *growth-fit* sensitivity case, not "discovering" that resolution
or segmentation affects materials images. A reviewer should decide whether
that case is useful enough to develop further.

The wording above needs care: **none of these papers is being claimed to
test the repository's specific paired synthetic trajectory**, but Sun et al.
directly undermine any claim that bringing correlations to experimental
coarsening images is novel. See the [dataset feasibility note](EXTERNAL_DATASET_SCOUT_2026-09-17.md)
before proposing a real-image extension.

For the **materials property** motivation, [Küchler et al. (2022)](https://doi.org/10.1002/adem.202100909)
already connect Fe–Cr α′ size, fraction and composition with measured hardness,
and critically compare STEM–EDS and APT size determinations. The
[source note](FECR_MATERIALS_CASE_STUDY_2026-09-18.md) records what can be
borrowed as context and what the 2D lattice cannot predict. Neither a
structure–property link nor the general fact that measurement methods
disagree is novel to this project.

## What the student can read without reading every page now

- **2010:** abstract, the paragraph defining filtered chord length on p. 2,
  and the finite-size scaling/initial-length analysis on pp. 2–3.
- **2011:** methods on pp. 2–3, the multiple-observable comparison on pp. 3–4,
  and 2D finite-size discussion around Fig. 6 on pp. 5–7.
- **2013:** abstract and introduction's motivation, methods on pp. 2–3, and
  the composition section on pp. 6–8. Focus on what was *already* tested.
- **2021 Cahn–Hilliard:** abstract, Table I on p. 2, length definition on
  p. 5, and Fig. 6–7 discussion on pp. 6–7. Note the different dynamics and
  initial-length/time fit before comparing numbers.

Before citing a quantitative value, recheck it in the actual paper and state
which version and observable it belongs to. No pending benchmark exponent is
inserted here; the student's method declaration remains unverified.
