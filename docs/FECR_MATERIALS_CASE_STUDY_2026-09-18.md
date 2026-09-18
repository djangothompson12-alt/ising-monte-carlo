# Fe–Cr as a reality check for the materials argument

*AI-assisted source note, 18 September 2026. This is not a result of this repository, a model calibration, or student-authored paper prose. Verify the primary paper before citing any number in a submitted report.*

## Why this paper matters

[Küchler and co-authors, *Advanced Engineering Materials* 24, 2100909 (2022)](https://doi.org/10.1002/adem.202100909) studied **binary Fe–Cr alloys** aged at 500 °C. They measured Vickers hardness and Cr-rich α′ microstructure with STEM–EDS and atom-probe tomography. This is a concrete processing → microstructure → property example for the report. It is not a validation of our 2D Kawasaki engine: the simulation has no physical clock, 3D precipitate chemistry, dislocations or hardness model.

| Published observation | Why it is relevant here | Boundary |
|---|---|---|
| Their Fe–20 wt% Cr and Fe–40 wt% Cr alloys hardened substantially over 50–1008 h; the paper reports roughly 133→245 VHN and 215→448 VHN, respectively, by the long-time measurements. | Actual mechanical consequences make microstructure measurement an engineering question. | These are **measured** hardnesses from their specimens, not outputs or forecasts from this model. |
| At 1008 h, Fe–20 wt% Cr showed dispersed globular α′ regions; Fe–40 wt% Cr showed an interconnected, vein-like α/α′ structure. | Composition changes morphology, not just a fitted growth slope. | The paper discusses whether the globular case is nucleation/growth or spinodal; appearance alone does not settle mechanism. |
| For Fe–20 wt% Cr at 1008 h, Table 1 reports an α′ radius of 3.5 ± 0.6 nm from STEM–EDS, versus 2.6 ± 0.4 nm by one APT proxigram analysis, 1.2 ± 0.8 nm by APT cluster search, and 3.1 ± 0.8 nm by an APT 1D profile. | A real paper already shows why an apparently precise “domain size” needs a definition and measurement protocol. This supports the *importance* of our observation-pipeline audit. | These are different methods and potentially sampled volumes; the numerical spread is **not** a controlled estimate of pure algorithmic bias and must not be sold as this project's discovery. Their length measures are precipitate radii, not our correlation half-height length. |
| The authors report that both α′ feature size and phase composition change during ageing and develop a measured structure–hardness relation. | It explains why one coarsening exponent cannot by itself predict a material property. | Our spins have fixed binary labels and conserve global fraction; the engine does not resolve evolving solute concentration within α and α′, elastic strain or dislocation barriers. |

The compositions must be named correctly: the paper gives 20 and 40 **weight** percent Cr as 21.27 and 41.73 **atomic** percent Cr. A simulation setting `c=0.15` is a site/atom fraction of the `+1` state, not “Fe–15 wt% Cr”. Its `c=0.5` case is not the paper's 40 wt% alloy. Do not line up the curves merely because their mixture ratios look similar.

[Xu and co-authors (2016)](https://doi.org/10.1007/s11661-016-3800-4)
provide a second, more directly kinetic example. For their alloy labelled
35Cr, aged at 773 K, the inverse SANS peak position gave a decomposition
wavelength scaling as approximately $t^{0.16}$, while a Guinier-derived
particle radius in the same paper gave $R\propto t^{0.27}$. The latter
uses a spherical-particle approximation even for comparison across
different decomposition morphologies. The authors themselves
emphasise that the structural quantity and stage of decomposition matter
when interpreting these powers. This is **prior experimental evidence**
that a quoted effective exponent needs an observable attached to it; the
gap between those two numbers is not a controlled estimate of image-processing
bias, and neither is a target value for our lattice fit. The paper's 35Cr
composition is given in weight percent, unlike the model's site fraction.

Two other **distinct published Fe–Cr specimens** make the time/measurement
issue more concrete. [Westraadt et al. (2015)](https://doi.org/10.1016/j.matchar.2015.10.001)
used analytical STEM on Fe–36 wt% Cr aged at 500 °C and reported a
decomposition wavelength of about **2, 3 and 6 nm** after **1, 10 and
100 hours**, respectively. They found the wavelength less sensitive to
specimen thickness than the compositional amplitude. Those are published
experimental wavelength estimates, **not** three points to fit against
our correlation length or Monte Carlo time. A separate
[Fe–32 at% Cr study](https://www.jstage.jst.go.jp/article/matertrans/50/7/50_M2009029/_article/-char/en)
combined TEM, hardness and a linear Cahn–Hilliard calculation; it reports
slow early decomposition and faster later growth with changing morphology.
Neither study supplies raw registered time-series images here or a
Kawasaki-to-Fe–Cr calibration. They show why time window, measurement
modality and the exact microstructural quantity matter in a real system.

## What this sharpens in our research question

The physical target is not “get α=1/3, therefore predict an alloy.” A stronger, narrower question is whether a reported **length or effective exponent remains stable under a declared observation method**, with the underlying simulated evolution held fixed. In a real alloy, different microscopy methods and segmentation choices also change the apparent size, while different phases, concentrations and mechanical mechanisms affect hardness. Our synthetic study isolates one part of that chain; it cannot close the whole chain.

The same paper notes that the Fe–Cr spinodal transition line is not firmly established and treats the 20 wt% mechanism cautiously. This is a useful warning against reading the repository's Bragg–Williams spinodal as a measured Fe–Cr phase boundary. The toy diagram can teach the thermodynamic distinction between instability and coexistence, but it does not classify their specimens.

Its data-availability statement says supporting data may be obtained from
the corresponding author **upon reasonable request**; raw registered
composition maps are not an openly downloaded dataset in this project.
Seeking them would require a specific analysis plan, the author's permission,
and the student's own outreach. Published figure panels alone are not an
adequate substitute for raw measurement input.

## Responsible use in the student report

- Cite this paper in the motivation/discussion as a **real engineering example** and as prior art for measurement dependence. Distinguish its published results from this project's own simulations.
- Use one small comparison table of *definitions*, not a plot forcing physical time and Monte Carlo sweeps onto the same axis.
- Ask a reviewer: “Would a controlled observation-pipeline sensitivity test add anything useful beside existing Fe–Cr STEM–EDS/APT comparisons? If so, what specific uncertainty should I quantify next?”
- Do **not** digitise the published micrograph panels and claim a fresh ageing exponent from them. Raw registered composition maps, scale and sampling details would be needed for that analysis.

Primary source details to recheck: [experimental protocol and hardness (Sections 2–3)](https://doi.org/10.1002/adem.202100909), [Table 1 and the method comparison](https://doi.org/10.1002/adem.202100909), and the discussion of the uncertain spinodal transition line. No data or images from the paper are redistributed in this repository.
