# Technical-report backbone: Model B coarsening and measurement

Working research scaffold, updated 18 September 2026. This is **not** a finished paper
or student-authored prose. Use it to check equations, source figures and claim
boundaries while writing the report in your own words. Do not paste sections
into an application without understanding and approving them. The older
`manuscript/main.tex` is useful history, but does not integrate the newer
replicated and observation studies; its tracked PDF is stale.

## A bounded central question

When a finite 2D Kawasaki simulation yields an effective domain-growth
exponent below the late-time one-third expectation, how much does the value
depend on fit window, system size and definition/observation of domain length?
The completed evidence addresses **measurement sensitivity** and some size/time
comparisons. It does not prove the asymptotic exponent, identify a unique
cause of the shortfall, or predict ageing in a named alloy.

The materials-engineering reason for asking is that domain and precipitate
measurements enter processing–microstructure–property arguments. The current
simulation stops at microstructure; it does not calculate strength. Model A
supplies a non-conserved contrast. Model B's fixed species counts are the
minimal binary-mixture analogy, not an atomistically faithful alloy model.
A [published Fe–Cr case study](FECR_MATERIALS_CASE_STUDY_2026-09-18.md)
shows real ageing, microstructure measurement and hardness in one binary
system, including disagreement between feature-size methods. It is context
and prior art, **not** a fitted calibration of the lattice to Fe–Cr.

## Report structure and what goes in each section

| Section | Material already available | Student decision still needed |
|---|---|---|
| Short abstract | One question, completed 64-run design, the window/estimator/observation results, bounded conclusion | Which one result is the clearest answer to your question? Write this last. |
| Motivation and prior work | Your existing introductory draft; [Bray 1994](https://doi.org/10.1080/00018739400101505), [Majumder & Das 2010](https://doi.org/10.1103/PhysRevE.81.050102), [2011 follow-up](https://doi.org/10.1103/PhysRevE.84.021110), [2013 temperature/composition study](https://doi.org/10.1039/C3CP50612F), [König et al. 2021](https://doi.org/10.1039/D1CP03229A), and the [Fe–Cr structure–hardness example](FECR_MATERIALS_CASE_STUDY_2026-09-18.md); [source comparison](LITERATURE_COMPARISON_2026-09-17.md) | Explain how your paired observation-pipeline comparison differs from prior size/time, noise, composition and continuum-model analyses. Do not call off-critical coarsening or low slopes a discovery. |
| Model and thermodynamics | Hamiltonian, conserved move, Metropolis rule, mean-field spinodal and [common-tangent binodal](REGULAR_SOLUTION_BINODAL_2026-09-18.md), plus the [exact 2D coexistence check](EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md); `phase_diagram.py` | Explain why the orange/blue curves are approximate, the green boundary is exact only for the infinite toy 2D lattice, and none is an Fe–Cr diagram. |
| Simulation and length methods | `research/plans/overnight.json`, `research/PROTOCOL.md`, `research/imaging.py`, estimator definitions | State which observable was primary before comparisons and why Model A uses raw correlation while off-critical Model B uses connected correlation. |
| Verified results | `docs/OVERNIGHT_RESULTS.md`, `docs/MEASUREMENT_STUDY_RESULTS.md`, raw tables and figure map below | Inspect each selected figure, explain actual retained times, independent-run unit, uncertainty type and missing values. |
| Long-run comparisons | The 40-run L=128 reference campaign is complete and has an [integrity audit](REFERENCE_RUN_INTEGRITY_2026-09-17.md) and [paper-method crosswalk](MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md); the separate 128-run 0.65 Tc extension is complete and internally audited (see the [claim ledger](CLAIM_AUDIT_2026-09-17.md)). | The reference-method declaration and any benchmark interpretation remain gated. Explain why the broader late fit does not establish one-third growth, and why the narrowest late window is unresolved under its fixed time-span rule. |
| Applied measurement case | `research/image_audit_report.py`, `docs/APPLIED_IMAGE_AUDIT.md`, the negative steel pilot, the [expert-mask resolution audit](METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md), the [fixed Al–Ge image test](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md), and the [unanalysed Al–Cu candidate](EXTERNAL_DATASET_SCOUT_2026-09-17.md) | Keep static resolution results separate from ageing kinetics. The source Al–Ge paper separates Ge lamellae and precipitates; our all-Ge 2D length does not. Before a physical-units or industry claim, establish a population, specimen independence, registration and a real decision threshold. Public-data analysis is not external adoption. |
| Discussion and limitations | `docs/CLAIM_AUDIT_2026-09-17.md` | Separate evidence from inference: 2D, finite time/size, small ensembles, observable choice, synthetic imaging, no physical time/strength calibration. |
| Reproducibility and assistance | manifests, hashes, tests, `AI_USE_AND_CONTRIBUTIONS.md` | Specify what you designed, checked, wrote and understood, and what AI assisted with. |

The new all-row extension appendix is a presentation aid only: after the
campaign and independent table audit finished, it listed all 80 declared fits
and unresolved coverage rather than selecting the best-looking window.
The supplied-mask tool is a possible bounded imaging-workflow pilot, not
evidence of adoption or material-property prediction. Both additions were
AI-authored while the long campaign remained incomplete.

## Equations to understand and verify

Use reduced units `k_B=1` in code; show `k_B` when explaining physical
dimensions. These equations come from the implemented model or elementary
algebra, not newly inferred material properties.

1. **Energy and composition.** For nearest-neighbour bonds counted once,
   `H = -Jx Σ_(horizontal) s_i s_j - Jy Σ_(vertical) s_i s_j`, with
   `s_i∈{-1,+1}` and periodic boundaries. `m=(1/N)Σ_i s_i` and
   `c=(1+m)/2` for the +1 species. An exchange replaces `(s_i,s_j)` by
   `(s_j,s_i)`, so `s_i+s_j` and therefore total magnetisation and both
   species counts are unchanged exactly. A flip has no such constraint.
2. **Metropolis move.** For a proposed exchange or flip,
   `p_accept=min(1,exp(-ΔE/(k_B T)))`, with `ΔE=H_after-H_before`.
   For symmetric proposals, detailed balance follows from the ratio of
   forward and reverse acceptance probabilities. If `ΔE<0`, the forward
   probability is 1 and the reverse probability is `exp(βΔE)<1`, so
   `W_forward/W_reverse=exp(-βΔE)`. Detailed balance alone is not a
   simulation of physical seconds; one sweep is `L²` **attempted** moves.
   The code tests a local energy change against a whole-lattice Hamiltonian.
   A separate exact 3×3 fixed-composition test checks the one-attempt
   transition matrix against canonical Boltzmann weights in all 126 states;
   an actual sampler diagnostic also agrees with the exact mean energy within
   its batch-estimated uncertainty. [Both small-system checks](SMALL_LATTICE_EQUILIBRIUM_CHECK_2026-09-17.md)
   are verification, not late-time coarsening evidence.
   See [Metropolis et al. 1953](https://doi.org/10.1063/1.1699114) and
   [Kawasaki 1966](https://doi.org/10.1103/PhysRev.145.224).
3. **Mean-field materials map.** The mean-field probability of unlike
   neighbours is `2c(1-c)`. Each unlike bond costs `2J_d` relative to a
   like one, and a square lattice has one horizontal and one vertical
   bond per site. The mixing-energy contribution is thus
   `Ωc(1-c)`, where `Ω=4(Jx+Jy)`. Adding ideal configurational entropy gives
   `f(c,T)=k_B T[c ln c+(1-c)ln(1-c)]+Ωc(1-c)`.
   Differentiating twice gives
   `f''=k_B T/[c(1-c)]-2Ω`; its zero gives
   `k_B T_s(c)=2Ωc(1-c)`. At `Jx=Jy=1`, `T_s=16c(1-c)` in reduced units
   and peaks at 4. This Bragg–Williams maximum is **not** the exact 2D
   Ising `T_c=2/ln(1+√2)≈2.269` for `J=1` ([Onsager 1944](https://doi.org/10.1103/PhysRev.65.117)). The mapping is checked
   numerically by `tests/test_physics_invariants.py`; it does not turn
   sweeps into hours or sites into nanometres.
   At the isotropic `0.65 T_c≈1.475` finish, the mean-field spinodal
   temperatures are `2.04` at `c=.15`, `1.44` at `c=.10` and `0.9024` at
   `c=.06` (the `c=.10` spinodal temperature is only about `0.035` below
   the finish temperature).
   Thus the earlier composition sweep does **not** put every
   mixture inside this approximate spinodal. Above it, the corresponding
   binodal distinguishes metastability from a single-phase region *within
   this mean-field model*.
   The [separately verified common-tangent derivation](REGULAR_SOLUTION_BINODAL_2026-09-18.md)
   now gives `T_b=Ω(1-2c)/[k_B ln((1-c)/c)]`, continuous to `Ω/(2k_B)`
   at `c=.5`. At the isotropic `0.65T_c` finish, `.06` and `.10` lie
   between the *mean-field* curves, while `.15` and `.50` are below the
   mean-field spinodal. Do not turn those labels into a claim that the
   true 2D or real-alloy kinetics used a particular nucleation mechanism.
   The exact zero-field 2D Ising spontaneous magnetisation supplies a separate
   equilibrium check: `m0=[1-{sinh(2Jx/T)sinh(2Jy/T)}^{-2}]^(1/8)` below the
   exact `Tc`, and `c_low/high=(1∓m0)/2`. At `0.65Tc` with `Jx=Jy=1`,
   `c_low≈0.006056` and `c_high≈0.993944`, placing all studied overall
   fractions in the exact **thermodynamic-limit coexistence interval**. This
   neither provides an exact spinodal nor says that any finite-time trajectory
   has reached that equilibrium. See [the separate theory check](EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md)
   and [Yang 1952](https://doi.org/10.1103/PhysRev.85.808).
4. **Length observable.** For off-critical Model B, the periodic raw
   equal-time spatial correlation is `C(r,t)=<s_i(t)s_(i+r)(t)>` and
   `g(r,t)=[C(r,t)-m²]/[1-m²]`. With exchange, `m` is exactly constant;
   `g(0,t)=1`. The primary directional length is the linearly
   interpolated first `g=0.5` crossing along each lattice axis; the mean
   is `(ℓ_x+ℓ_y)/2`. No crossing is **unresolved**, not zero or a guessed
   maximum. Model A's established baseline instead uses its raw spatial
   correlation: its magnetisation changes during ordering, and replacing
   that observable with a time-connected one would change the question.
   The finite-image applied tool uses a **separate**, non-periodic,
   pair-count-normalised covariance with its own observed-image mean; do
   not present it as identical to the periodic engine estimator.
5. **Scaling expectations, not fitted constraints.** A curvature-driven
   interface has speed scaling as `1/ℓ`, yielding `dℓ/dt∝1/ℓ` and
   `ℓ∝t^(1/2)` in the ideal late regime. In diffusion-limited conserved
   coarsening, a chemical-potential scale `∝1/ℓ` and a gradient over
   distance `ℓ` give flux `∝1/ℓ²`, hence `dℓ/dt∝1/ℓ²` and
   `ℓ∝t^(1/3)` under the standard assumptions. These are heuristic
   long-time scaling arguments, not formulas that force finite-run fits
   to equal 1/2 or 1/3. A [2021 two-dimensional Cahn–Hilliard study](https://doi.org/10.1039/D1CP03229A)
   reports composition-dependent fitted late-stage values under its own
   assumptions; it is not directly comparable to this Kawasaki estimator.
   See also [Bray 1994](https://doi.org/10.1080/00018739400101505).
6. **Reported finite-window slope.** Fit the slope `α_eff` of
   `log(<ℓ(t)>_replicas)` against `log t` over a stated window and jointly
   resolved checkpoints. It is not an average of per-replica slopes.
   Resample **whole independent trajectories** for bootstrap intervals;
   not pixels, crops or timepoints. The interval omits model,
   fit-mask-selection and observable-definition uncertainty. Always quote
   actual retained times and `n`.

## Figure-to-claim route using completed evidence

| Figure/output | Responsible claim | Required caption qualification |
|---|---|---|
| `figures/fig_regular_solution_spinodal.png` | Couplings imply a mean-field phase-diagram guide. | Not exact 2D binodal/spinodal or measured alloy diagram. |
| `figures/fig_regular_solution_binodal_spinodal.png` | The symmetric regular-solution common tangent separates coexistence, metastability and local instability *in mean field*. | `c=.06` and `.10` being between curves does not prove nucleation; not exact 2D or Fe–Cr. |
| `figures/fig_exact_vs_meanfield_coexistence.png` | Exact infinite-2D equilibrium coexistence versus the mean-field guides; all studied final compositions fall within the exact coexistence interval. | No exact spinodal, finite-size onset, ageing rate or real-alloy calibration follows from this curve. |
| `research/runs/overnight/analysis/growth_c0.png` and `growth_c1.png` | Time-window and size diagnostics from 64 runs. | Bands are replica standard errors; the z=3 display is a candidate, not a fitted or successful collapse. c=.50 L=32 has unresolved late points. |
| `research/runs/overnight/analysis/exponents.csv` | At c=.50 L=128, α_eff goes from 0.197 to 0.258 as the nominal fit start moves from sweep 2 to 1,000 (same end 200,000). | Overlapping fits; no independent p-value or asymptotic claim. |
| `research/results/paired_window_sensitivity_2026-09-18/paired_window_differences.csv` | The late-minus-early shift stays positive when the same eight L=128 trajectories are paired in each whole-run bootstrap draw. | [Post-result conditional audit](PAIRED_WINDOW_AUDIT_2026-09-18.md), not an independently chosen test of the asymptotic law. |
| `research/runs/overnight/initial_length_sensitivity_v1/paired_initial_length_fits.csv` | A fixed measured early-length subtraction changes large-L finite-window slopes substantially. | Exploratory post-result test, not a fitted bare-length correction or proof of one-third; see [the sensitivity note](INITIAL_LENGTH_SENSITIVITY_2026-09-17.md). |
| `research/runs/overnight/estimator_analysis_v1/paired_fits.csv` | Four definitions give 0.258, 0.251, 0.167, 0.204 at c=.50 L=128 in the nominal late-start window. | Different observables; not four radii of one known physical particle. |
| `research/runs/overnight/imaging_v1/` and `research/runs/imaging_validation/imaging_v1/` | Binning+thresholding changes apparent α_eff, repeated in fresh seeds. | Synthetic operators; distinguish original n=8, fresh n=4, differing checkpoint grids; crop behaviour less robust. |
| `research/runs/{overnight,imaging_validation}/binning_decomposition_v1/` | A post-hoc stage comparison separates greyscale block averaging from binary thresholding on identical snapshots. | The short-window balance differs by composition and changes in a longer fit window; see [the follow-up](BINNING_DECOMPOSITION_RESULTS_2026-09-17.md). |
| `research/runs/synthetic_growth_control_v2/` | A constructed `t^(1/3)` square-domain sequence returns a finite-image fitted slope above its known geometric value; the difference shrinks as field of view grows. | [This exploratory control](SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md) is not Kawasaki physics or experimental validation. Its binning response is small and pattern-specific; it cannot explain the low engine slope. |
| `research/runs/alge_feasibility/qa/experimental_feasibility.png` and QA JSON | Real-image metadata and comparability audit. | No experimental exponent, registered volume, or alloy validation. |
| `research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv` and metadata QA | A fixed 4× observation step on Fell's segmented Al–Ge alloy ROI stacks produces unresolved early interior measurements and stage-specific static length shifts later. | [One-specimen exploratory audit](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md); correlated planes, image motion and source-author 3D prior art. No growth exponent or outside use. |
| `figures/fig_alge_fixed_plane_audit.png` | Displays every planned Al–Ge plane, including unresolved cases, and the within-plane 4×/native static ratios. | Its red medians appear only for stages with all 11 planes resolved. This is not a four-point kinetic curve, precipitate-size measure or hardness prediction. |
| `research/runs/public_mask_pilot/reference_scale_v1/per_image.csv` | On published austenite annotations, 4× block averaging plus re-binarisation raised the measured static correlation length in all 42 images; median coarse/native ratio 1.050 for the predeclared tie rule. | Images may share specimens; label and scale limits remain. This is not an ageing exponent, physical feature radius, independent-use claim or inferential result. |
| `research/runs/main_065_multisize_v1/analysis_declared_v1/` (local only) | Four-size million-sweep growth, local-slope and matched-time comparison figures; all 80 fit rows are in `appendix_v1/APPENDIX.md`. | Completed and internally checked, but not a public release. L32 at 15:85 flattens; L32 at 50:50 becomes unresolved late. Do not claim an onset or universal one-third plateau. |
| `research/runs/main_065_multisize_v1/image_holdout_v1/` (local only) | Fixed new-seed 4× image-operator repeat on 16 width-128 trajectories per composition. | Selected after the earlier effect; altered operation changes apparent phase fraction and is not microscope validation. |
| The 40-run literature reference | Raw data passed integrity checks, but no paper-method-matched fit or figure has been approved. | Follow the student's literature-method declaration gate before calling it a benchmark result. |

The exact completed numerical statements and caveats are in
`docs/CLAIM_AUDIT_2026-09-17.md`. The type of uncertainty mark must be
named correctly: standard-error bands, bootstrap intervals and variation
across method choices are **not** interchangeable.

## Source reading and citation checks

- [Hohenberg & Halperin 1977](https://doi.org/10.1103/RevModPhys.49.435):
  classification by conservation. The implementation here is **Metropolis**
  Model A and Metropolis-accepted Kawasaki Model B; never call its flip rule
  “Glauber.”
- [Bray 1994](https://doi.org/10.1080/00018739400101505): phase-ordering
  scaling, finite-time caveats, composition-dependent morphology/scaling
  functions. Check the relevant pages yourself before quoting a claim.
- [Majumder & Das 2010](https://doi.org/10.1103/PhysRevE.81.050102) and
  [2011](https://doi.org/10.1103/PhysRevE.84.021110): prior two-dimensional
  conserved-order work on early growth, measurements and finite-size
  scaling. Compare their observable and initial-length treatment before
  calling the now-complete raw run a reproduction.
- [Majumder & Das 2013](https://doi.org/10.1039/C3CP50612F): temperature and
  composition variation, including off-critical droplets, already studied in
  this model family. Do not use composition dependence alone as a novelty
  claim; see the [method-by-method reading note](LITERATURE_COMPARISON_2026-09-17.md).
- [König, Ronsin & Harting 2021](https://doi.org/10.1039/D1CP03229A): a
  different conserved 2D Cahn–Hilliard model reports composition-dependent
  fitted late-stage exponents and differences between energy- and
  structure-factor measures. Useful counterpoint, not an equivalent Kawasaki
  benchmark.
- [Chan et al. 2020](https://doi.org/10.1038/s41524-019-0267-z) and
  [Stuckner et al. 2022](https://doi.org/10.1038/s41524-022-00878-5):
  materials-image work already quantifies effects of preprocessing,
  resolution and segmentation on downstream microstructure measurements.
  Our growth-fit sensitivity is narrower; it should not be described as the
  first recognition of image-analysis bias.
- [Sun et al. 2017](https://doi.org/10.1016/j.actamat.2017.04.054):
  two-point correlations on time-resolved Al–Cu tomography already yield
  dendrite length estimates compared with direct measurements. A future
  real-image extension must not claim this broad translation as new; its
  possible contribution is a narrower, predeclared observation-choice audit.
- [Onsager 1944](https://doi.org/10.1103/PhysRev.65.117): exact 2D
  square-lattice critical-temperature reference, not the Bragg–Williams
  spinodal maximum.
- [Yang 1952](https://doi.org/10.1103/PhysRev.85.808),
  [Baxter 2011](https://arxiv.org/abs/1103.3347) and
  [Pleimling & Selke 2000](https://arxiv.org/pdf/cond-mat/0001178): exact
  spontaneous magnetisation, including anisotropic couplings, and its use as
  the coexistence boundary of the fixed-magnetisation 2D lattice. The last
  paper also cautions that finite-lattice droplet behaviour is subtler.
- [MetalDAM annotated steel micrographs](https://github.com/ari-dasci/OD-MetalDAM)
  and [AlGe nano-CT dataset](https://doi.org/10.5281/zenodo.14923133):
  candidate applied-measurement materials, each serving a different
  question. The static annotated steel set cannot validate ageing kinetics;
  the AlGe time series cannot yet provide a defensible exponent from the
  currently inspected slices.
- [Fell's labelled Al–Ge ROI stacks](https://doi.org/10.17632/hj9njz3rxp.1)
  supply a separate 60-nm segmented solid-state-ageing case. The
  [bounded within-image test](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md) found
  both failed and resolved measurements, but no stage-to-stage 3D
  registration, independent specimen or kinetic calibration. The linked
  source paper already reports feature evolution and hardness.

Check exact bibliographic details, formula conventions and permissions when
the final reference list is assembled. A citation supports a claim only if
the cited work actually studied that quantity in a comparable regime.

## Your explanation prompts before sending to a reviewer

1. Why does an exchange conserve composition while a flip does not?
2. Why can a connected correlation be useful for Model B off criticality,
   yet changing Model A's established raw observable is not a neutral fix?
3. What exactly is plotted in the growth panel, and which uncertainty does
   its band show?
4. How can four definitions of length produce four slopes without any one
   of them being a software error?
5. Why is fourfold binning **plus thresholding** an observation change,
   not altered physics, and why is its apparent exponent shift not a
   universal correction?
6. What evidence in the completed extension suggests finite-time drift or
   a small-box departure, and why can it still not assign an onset time or
   demonstrate the asymptotic one-third law?
7. Why do the exact 2D coexistence boundary and the mean-field spinodal
   answer different questions? Why does neither calibrate a real alloy?
8. If an engineer supplied an image series, which metadata and permissions
   would you need before reporting a physical growth rate?

Keep a dated change log after expert feedback: criticism, evidence examined,
change made or rejected, and reason. Neither a courteous reply nor an AI
review is academic endorsement.
