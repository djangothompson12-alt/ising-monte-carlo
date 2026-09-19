# Review preparation: completed checks and open criticisms

## Numerical checks

A separately written direct-pair covariance calculation (no production FFT,
crossing or fit helper) remeasured the first, middle and final checkpoint in
all 32 L=128 trajectories used by the conservation-aware analysis. All 576
directional lengths agreed; the largest absolute difference was
3.5527e-15 lattice sites. Centred-dot-product regression and separately
written paired resampling reproduced all 12 original fit rows and intervals.
This is independence of implementation, not an independent investigator.

Five thousand resamples with a separate random seed retained the original
zero-crossing classifications. Leave-one-trajectory-out primary segmentation
shifts ranged from -0.05519 to -0.05410 at c=.50, and -0.04460 to -0.04293 at
c=.15. A resampling sensitivity check does not create more experimental or
simulation replicas. The original analysis and its 500-draw intervals remain
the primary record.

The volume checks now include analytic slab covariance, cuboid axis
permutation, mirror invariance and spherical symmetry. An initial analytic
slab test expectation was corrected: there are two interfaces, and each
mismatched pair changes its normalized product from +1 to -1. At short lag
r the covariance is (n-5r)/(n-r), not (n-3r)/(n-r). The production result
agreed with direct pair counting; no measurement formula was changed.

The standalone volume tool no longer imports plotting/scientific-stack
modules just to hash a file. Hashing streams the input instead of reading a
whole TIFF into memory. The new volume run preserves all 60 measurement rows
from the previous version. Eleven volume tests and the command-line example
passed from a minimal copied source tree under the separate Python 3.12
runtime. This is not a fresh-network installation or a full cross-platform
verification of the Monte Carlo environment.

## Most important open criticisms

1. **Sequential decomposition is not causal attribution.** The sum of the
   two stage differences equals the combined difference, but phase-fraction
   change is not isolated from geometry change. A mass-preserving binary
   comparison would be a separate experiment, with its own tie/spatial rule;
   it must not be improvised and then sold as confirmation.
2. **One factor and one threshold are narrow.** The primary audit fixes
   fourfold averaging and a zero threshold with +1 ties. Earlier sensitivity
   analyses provide context, not a systematically sampled parameter map.
3. **Intervals condition on measurement choices.** They do not cover the
   shared-mask rule, field selection, segmentation truth, or model validity.
4. **A real-image length is not a validated alloy prediction.** Sparse Al-Ge
   boxes, unestablished registration and partial-volume effects prohibit a
   kinetic validation claim. Ge volume fraction is not bulk composition.
5. **Novelty is open.** The ingredients have prior art; a specialist may find
   the exact stage decomposition already published or too narrow to matter.

## Additional bounded literature check

On 19 September, web queries combined `coarsening exponent threshold Zabler`,
`Ising coarsening block averaging segmentation`, `conserved coarsening exponent
image segmentation` and `Kawasaki pixel integration`. Unrelated results were
discarded. This search is not systematic and does not establish absence of
prior art.

- Zabler et al. (2007), [author-hosted manuscript](https://www.alexanderrack.eu/papers/zabler2007.pdf),
  Figure 8: fitted exponent versus threshold/solid fraction is already explicit.
- Eidel et al. (2021), [publisher full text](https://onlinelibrary.wiley.com/doi/full/10.1002/zamm.202000245):
  the image-coarsening variants include mixed/interphase pixels reflecting
  phase fractions, alongside segmentation. The general distinction is not new.
- [Chromatin mechanics dictates subdiffusion and coarsening dynamics of embedded
  condensates](https://www.nature.com/articles/s41567-020-01125-8) (2021) is adjacent
  primary literature: it checks threshold sensitivity and uses integrated
  intensity and volume-based measures to test conservation at coalescence.
  It is a different physical system, but it further rules out claiming that
  connecting image measurement to a conservation diagnostic is unprecedented.

The narrower simulation question remains a candidate contribution for
criticism, not a claim of first use, publishability or external endorsement.
