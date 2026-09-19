# Literature scope and an honest route to a contribution

**Subsequent correction:** the deeper search identified Ledesma-Alonso et al.
(2018), PRE 97, 023304, as particularly close prior art for image reduction,
correlation descriptors and fraction-versus-shape effects. Read the updated
[originality assessment and question](ORIGINALITY_AND_NEXT_QUESTION_2026-09-19.md)
before using the older candidate-contribution wording below. The new control
tests whether fraction matching is sufficient; static resolution sensitivity
alone is not a novel result.

## Status of this document

This is an AI-assisted **bounded scoping review**, searched on 19 September
2026. It is not a systematic review and cannot support the phrase “the first
ever.” No web search can establish that every paper, thesis, conference
proceeding or non-English source has been found. A specialist must check the
final novelty claim before submission. The purpose of this map is to prevent
obvious reinvention and turn the current project into a precise question that
an academic can assess.

Search routes included APS, publisher pages, Crossref/DOI and broad scholarly
web search. Query families combined: `Kawasaki`, `conserved Ising`, `coarsening`,
`effective exponent`, `finite size`, `composition`, `anisotropy`, `correlation
length`, `image resolution`, `block averaging`, `segmentation threshold`,
`phase fraction`, `microstructure`, `tomography`, and `coarsening exponent`.
The source-by-source comparison in
[`LITERATURE_COMPARISON_2026-09-17.md`](LITERATURE_COMPARISON_2026-09-17.md)
is part of this scope and contains the detailed Majumder-Das crosswalk.

## What is established already

| Area | Representative primary literature | Consequence for this project |
|---|---|---|
| Dynamic universality | Hohenberg and Halperin, [Rev. Mod. Phys. 49, 435 (1977)](https://doi.org/10.1103/RevModPhys.49.435) | Model A and Model B are established classifications. Implementing Metropolis flips and Kawasaki exchanges is not a research contribution by itself. |
| Phase-ordering growth laws | Bray and Rutenberg, [Phys. Rev. E 49, R27 (1994)](https://doi.org/10.1103/PhysRevE.49.R27); Bray's 1994 review, cited in the comparison note | The one-half and one-third laws are theoretical late-time expectations under stated assumptions, not values that every finite straight-line fit must return. |
| Conserved phase-separation mechanisms | Binder, [Phys. Rev. B 15, 4425 (1977)](https://doi.org/10.1103/PhysRevB.15.4425) | Diffusion, cluster processes and crossovers have long been discussed. A low finite-window slope is not automatically a new mechanism. |
| Finite-time and metastable Kawasaki behaviour | Krzakala, [Phys. Rev. Lett. 94, 077204 (2005)](https://doi.org/10.1103/PhysRevLett.94.077204) | Very slow early growth and late recovery of one-third behaviour have prior art. The report should treat an early sub-one-third value as an effective exponent. |
| Finite size, initial offsets and multiple lengths | Majumder and Das 2010, 2011 and 2013, with links and exact method distinctions in the comparison note | Temperature, composition, filtered chord lengths, correlation lengths, structure-factor lengths and finite-size scaling were already studied. Our 50:50/15:85 sweep and estimator comparison are not individually novel. |
| Composition in another conserved model | König, Ronsin and Harting, [Phys. Chem. Chem. Phys. 23, 24823 (2021)](https://doi.org/10.1039/D1CP03229A) | A Cahn-Hilliard study already reports morphology- and observable-dependent fitted exponents. We cannot say every off-critical deviation is only finite size/time. |
| Anisotropic conserved coarsening | Ala-Nissila, Gunton and Kaski, [Phys. Rev. B 33, 7583 (1986)](https://doi.org/10.1103/PhysRevB.33.7583) | Strongly anisotropic structures, generalized anisotropic scaling and non-simple finite-time growth laws predate this project. `Jx != Jy` is a useful demonstration, not a novelty claim and not a model of elastic rafting. |
| Experimental threshold sensitivity | Zabler et al., [Acta Materialia 55, 5045 (2007)](https://doi.org/10.1016/j.actamat.2007.05.028) | They explicitly plotted a fitted coarsening exponent against binarization threshold/solid fraction in Al-Ge radiographs. “Thresholding changes the exponent” is therefore not new. |
| Instrument-time observation effects on Kawasaki data | Honerkamp-Smith, Machta and Keller, [Phys. Rev. Lett. 108, 265702 (2012)](https://doi.org/10.1103/PhysRevLett.108.265702), including time-averaged Kawasaki snapshots used to mimic camera acquisition | Using an observation operator to mimic camera limits in an Ising-type comparison also has precedent. Their critical-dynamics question is different, but our work must still be precise about what its operator and outcome add. |
| Mixed pixels and image coarsening | Eidel, Fischer and Gote, [ZAMM 101, e202000245 (2021)](https://doi.org/10.1002/zamm.202000245) | Their image-based mechanics study already distinguishes binary coarsening from a mixed/interphase-pixel representation. Mean-preserving partial-volume pixels are therefore not a new general idea; our possible addition is the paired stage decomposition of a fitted coarsening exponent in two conserved morphologies. |
| Quantitative EDS phase mapping | Beniwal et al., [Metallography, Microstructure, and Analysis 12, 924 (2023)](https://doi.org/10.1007/s13632-023-01020-7), and [Phase Fraction Estimation in Multicomponent Alloy from EDS Measurement Data (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11122778/) | Composition maps, phase segmentation and mixed-phase measurement regions already have dedicated methods. This project should not claim a new segmentation system, and it must distinguish phase area fraction from conserved elemental composition. |
| Materials imaging and metrology | Ezad et al. (2022), Tiwari and Tewari (2010), Eidel (2021), Chan et al. (2020), Stuckner et al. (2022), and Sun et al. (2017), linked in the comparison note | Resolution, segmentation and choice of size metric are established sources of measurement uncertainty in real microstructures. |

## Claims that the current work must not make

The evidence does **not** support claiming that this project discovered
Model B coarsening, composition-independent growth, anisotropic domain growth,
the effect of estimator choice, or the effect of segmentation on a coarsening
exponent. It also cannot claim that a 2D nearest-neighbour lattice predicts a
specific alloy's time, length, hardness or service behaviour. `Jx != Jy` does
not introduce coherency strain, elasticity, crystal orientation, dislocations
or a third dimension, so it is not a quantitative gamma-prime rafting model.

## The narrow contribution that remains plausible

The strongest current question is:

> In an exactly composition-conserving Kawasaki simulation, how much of a
> low-resolution effective-exponent shift appears during linear pixel
> integration, which preserves the field mean, and how much is added by binary
> segmentation, which can violate apparent conservation? Does that
> decomposition repeat across bicontinuous and droplet morphologies?

The repository now addresses this with paired snapshots from 16 new-seed
trajectories at each composition, a common resolved-time mask, whole-trajectory
bootstrap intervals, exact source hashes and a protocol that acknowledges the
earlier effect. The distinction is useful because it connects a physical law
(conserved composition) to a metrology check (whether the observed image still
appears conserved) instead of reporting a generic image-processing sensitivity.

This remains a **candidate methodological contribution**, not a publication
claim. The broad ingredients are all prior art. The exact combination was not
found in this bounded search, but absence from a search result is not evidence
that it has never been done.

The conservation language also needs a strict real-materials boundary. In the
simulation, binary-site fraction is composition. In a real alloy, a binary
phase-mask area fraction is generally **not** bulk chemical composition: each
phase may contain both elements, and phase fractions may evolve while total
solute remains conserved. The [external-pilot decision document](CONSERVATION_AWARE_EXTERNAL_PILOT_2026-09-19.md)
therefore separates a geometrical phase-mask audit from a calibrated
composition-map audit.

## Ranked questions for the technical report

1. **Primary, answerable now:** How do mean-preserving integration and
   composition-changing segmentation separately affect the fitted effective
   exponent in 50:50 and 15:85 Model B trajectories? This is the cleanest
   original-looking result because it has a conservation-based reason, paired
   controls and two morphologies.
2. **Primary physics context:** Why do the effective exponents depend on fit
   window and observable, and which evidence distinguishes finite-time drift
   from finite-size saturation? Compare with Majumder-Das without calling a
   method match that has not been verified.
3. **External-use test:** On an owner-approved real coarsening image series,
   does a processing audit materially change a reported growth conclusion or
   uncertainty? A binary phase mask can test geometrical area/length
   sensitivity; only a calibrated quantitative composition map can support a
   separate mass-balance question. The data owner must define the signal,
   calibration and decision. This would be genuine outside use; a synthetic
   demo alone is not.
4. **Secondary morphology question:** Is the observation bias larger or
   different in the off-critical droplet case than the bicontinuous case, and
   can that be explained by partial-volume pixels and threshold ties rather
   than a new physical growth law?
5. **Later, not a pre-deadline priority:** How do directional correlation
   lengths behave under controlled anisotropy? This needs a dedicated,
   literature-matched protocol. Existing anisotropic work means it is not an
   easy novelty route.

## What would make the contribution publishable rather than merely polished

A visually good app and a long report are not enough. Before journal language
is used, the project needs:

- an independent specialist to challenge the novelty search, observable and
  statistical unit;
- either an owner-approved real time series with known pixel/time calibration,
  or a broader predeclared synthetic parameter map showing when the audit does
  and does not matter;
- a clear baseline against Zabler et al.'s threshold-versus-exponent analysis
  and the Majumder-Das estimator literature;
- student-led explanation of every equation, design choice and limitation;
- a target journal checked for scope, pre-university authorship and AI policy;
- release of scripts, environment, checksums and all non-restricted data needed
  to regenerate the figures.

An academic endorsement is realistic only if it is phrased as what the expert
actually did—for example, “reviewed the protocol and the student responded to
three methodological criticisms”—not as borrowed authority or a guaranteed
statement that the result is original. A laboratory pilot is more valuable if
the lab supplies the question and can say whether the audit changed anything.

## Search boundary and next reviewer questions

The reviewer should specifically be asked:

1. Have you seen the conservation-aware integration/segmentation decomposition
   applied to a fitted coarsening exponent in conserved phase separation?
2. Is the connected-correlation half-height length defensible for both
   bicontinuous and droplet morphologies, or should a second primary observable
   be declared before any external-image pilot?
3. Is a common all-replica resolved-time mask too conservative, and if so what
   missing-data rule should be fixed without selecting by outcome?
4. Which experimental system has an accessible calibrated composition-map
   sequence, a registered field or defensible sampling design, and a relevant
   owner-defined decision? If only binary masks exist, is a geometrical audit
   still useful without calling phase fraction chemical composition?
5. What result would be useful enough to change a laboratory's analysis rather
   than simply illustrating a known warning?

Those questions turn outside contact into falsifiable technical review. They
are more credible than asking an academic to endorse a completed claim.
