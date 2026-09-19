# What is already known, and the small question worth testing

## Verdict

The broad question is **not original**: image resolution, segmentation and
choice of observable can change measured microstructure statistics and fitted
coarsening behaviour. The previous novelty map missed a particularly close
2018 paper. That omission has now been corrected. No search can certify that
the narrower experiment has never been done; novelty is still a question
for a specialist, not a guaranteed outcome of this project.

There is nevertheless a defensible small empirical question:

> For conserved Kawasaki trajectories, is matching the native species-site
> fraction during low-resolution binary segmentation sufficient to recover
> the native finite-window coarsening exponent? How do the residual bias and
> tie sensitivity vary with resolution and composition?

A linked external question is deliberately smaller: do the same controls
recover static correlation lengths in real, supplied 3D alloy phase masks?
The two questions do not assert that a 2D simulation predicts real kinetics.

## Three search passes and closest prior art

The search covered (1) coarsening measurements and exponents, (2) resolution,
correlation functions and microstructure descriptors, and (3) fraction/volume
constraints in thresholding. Sources below are primary papers or author/
institution-hosted versions. Search queries included quoted combinations of
`coarsening exponent`, `segmentation`, `Kawasaki`, `block averaging`,
`image resolution`, `volume fraction`, `preserving`, `thresholding`,
`decimation`, and the titles of the closest retrieved papers. Exact keyword
queries also returned unrelated computational coarsening and Kawasaki-company
results, which were excluded. This is a bounded scoping search, not a
systematic review or a reliable proof of absence.

| Primary work checked | Overlap that restricts our claim | Remaining distinction to assess |
|---|---|---|
| Zabler et al. (2007), [Acta Materialia](https://doi.org/10.1016/j.actamat.2007.05.028), [author manuscript](https://www.alexanderrack.eu/papers/zabler2007.pdf), Fig. 8 | Coarsening exponent versus threshold/solid fraction was already plotted for experimental Al-Ge. | Our paired known-fraction control on conserved trajectories is a different experimental design; generic threshold bias is not new. |
| Majumder and Das (2010/2011/2013), [2010 preprint](https://arxiv.org/abs/1001.3985), [2013 paper](https://doi.org/10.1039/C3CP50612F) | Finite-size, temperature, composition, filtering and multiple length measures in conserved Ising coarsening are established. | Do not claim that asymmetric mixtures, slow fitted slopes or multiple observables are original. The observation control is the proposed extension. |
| Ledesma-Alonso, Barbosa and Ortegón (2018), [PRE 97, 023304](https://doi.org/10.1103/PhysRevE.97.023304), [open manuscript](https://arxiv.org/abs/1712.03183), sections III, IV and VII | Progressive image reduction alters normalized correlation descriptors; they distinguish fraction-related changes from descriptor-shape changes and relate acceptable reduction to correlation length. They also include a real microstructure example. | This is close prior art for the static tool. The proposed addition is a time-dependent fitted-exponent benchmark with an explicit fraction-matched binary control, not discovery of static resolution error. |
| Eidel, Fischer and Gote (2021), [ZAMM](https://onlinelibrary.wiley.com/doi/full/10.1002/zamm.202000245) | Mixed/interphase pixels and binary coarsening, including phase-fraction effects, already appear in image-based mechanics. | Keeping block means is not a new method; our target quantity is a finite-window growth exponent. |
| Sun et al. (2017), [institutional record](https://laro.lanl.gov/esploro/outputs/journalArticle/Analytics-on-large-microstructure-datasets-using/9916370682503761) | Two-point correlations already quantify and interpret tomography-measured coarsening; variants are compared. | Applying correlations to real alloy images is not original or a validation by itself. |
| Laux and Swartz (2017), [Convergence of thresholding schemes incorporating bulk effects](https://arxiv.org/abs/1601.02467) | Volume-preserving threshold dynamics already exist. This is an adjacent dynamics literature, not the same post-processing experiment. | Selecting a threshold/rank to enforce a volume constraint must not be claimed as a new algorithm. |
| Fell et al. (2023), [institutional full text](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/67141d92-229c-4890-9d39-2fa277b70a49/content), section 3.5 | The dataset authors separate Ge lamellae and precipitations and apply dedicated filtering before object measurements. | Our all-Ge correlation length cannot be compared numerically with their population-specific particle length as if it were the same observable. |

The exact combination of fraction-matched post-processing, paired Kawasaki
growth-exponent differences, multiple resolutions and fixed tie sensitivity
was not identified in this search. That is a **candidate empirical gap**, not
an established literature gap. A knowledgeable reviewer may identify prior
work or judge the contribution too incremental for their journal.

## What could honestly be contributed

An openly reproducible quantitative benchmark, including failure cases, for
one specific way of checking whether an apparent coarsening result survives
image reduction. The interesting output is the residual exponent bias after
fraction matching, not a claim that equal fractions imply equal geometry.
That latter point is already fundamental to microstructure statistics.

An external tool can make the benchmark useful by answering an owner's
specific imaging question. Public-data reuse demonstrates feasibility, not
adoption. The contribution must be presented with the actual AI assistance
and the student's own decisions, understanding and response to criticism.
Admissions relevance is not a scientific selection criterion or proof of novelty.

## How to answer it with the existing data

1. Keep the 32 L=128 trajectories immutable: 16 per composition, c=.50 and
   .15, T=.65 Tc. The original decomposition is background evidence.
2. Compare native, block-averaged, fixed-threshold and fraction-matched
   images at factors 2, 4 and 8. The matching control knows the reference
   fraction and is therefore an oracle diagnostic, not a deployment claim.
3. Keep five fixed coordinate tie orderings. They are algorithmic sensitivity,
   not five new simulation runs. Round foreground counts to the nearest
   attainable integer and record the residual fraction error.
4. Use factor 4 and 1,000-20,000 sweeps as the primary comparison. Keep the
   same all-operator resolved mask, fit definition and paired trajectory
   bootstrap. Secondary factors and the longer window cannot replace it.
5. Report residual bias and missing measurements whether the control works
   or fails. Do not tune the answer to 1/3. The target is the native fit, which
   is itself a finite-window estimate, not known physical truth.
6. Apply the same operators separately to the four fixed Al-Ge volumes. Show
   static length ratios and phase-volume errors; fit no experimental exponent.
7. Ask a specialist whether this is a useful incremental benchmark and what
   closest method it should be compared with. Only after that choose a journal
   or expand to an owner-led experimental test.

The [protocol](../research/FRACTION_MATCHED_PROTOCOL_2026-09-19.md) was written
before computing the new control, but after the earlier effect was known.
The [new results](FRACTION_MATCHED_RESULTS_2026-09-19.md) answer that protocol.
