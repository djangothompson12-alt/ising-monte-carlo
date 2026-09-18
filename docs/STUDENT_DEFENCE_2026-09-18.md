# Can I explain this project without the report in front of me?

*AI-assisted study sheet, not wording to recite as my own. Try each question
aloud first, then check the answer and the linked evidence. If an academic
asks about something uncertain, say what you tested and what you do not yet
know. Memorising an exponent is less valuable than explaining how it was
measured.*

1. **What is the research question now?** In finite conserved Ising runs,
   how much does a reported coarsening exponent depend on actual time range,
   lattice size and operational length definition? The later image study
   asks what changes when the *same snapshots* are observed through a
   declared processing pipeline. See the [working draft](../manuscript/REPORT_DRAFT_2026-09-18.md).
2. **Why use Kawasaki exchanges?** A neighbouring +1 and −1 trade places;
   neither species count changes. This is a deliberately simple model of a
   conserved binary composition. It is not a vacancy-mediated diffusion
   simulation of a particular alloy. A Monte Carlo sweep is `L²` *attempts*,
   not `L²` accepted swaps.
3. **Why is Model A not the same physical problem?** Its Metropolis
   single-spin flips can change total magnetisation. For a literal binary
   mixture, they would change the overall species count. Model A is the
   non-conserved comparison, not the more realistic atom-exchange rule.
4. **Where does one-third come from?** In the ideal late-stage conserved
   scaling picture, curvature makes a chemical-potential difference of
   order `1/ℓ`, diffusion acts across `ℓ`, and the interface speed scales
   as `dℓ/dt ∼ 1/ℓ²`; hence `ℓ³ ∼ t`. This argument assumes the scaling
   regime and does not set a universal sweep number for reaching it.
   See [Bray's section 2.5](https://doi.org/10.1080/00018739400101505).
5. **What do +1 and −1 mean?** Magnetic spins in the original Ising model;
   labels for two components in the binary-mixture analogy. They are not
   automatically Al and Ge or Fe and Cr atoms with real jump rates.
6. **What is the primary domain length?** For each axis, compute the
   periodic connected correlation of the spin field and find its first
   interpolated fall through 0.5. Average x and y lengths. This is not a
   unique droplet radius. If either crossing is absent, the saved length is
   unresolved, not zero. See the [data dictionary](../research/DATA_DICTIONARY.md).
7. **Why subtract magnetisation in Model B but keep the established Model A
   measurement?** Off-centre Model B has a fixed nonzero mean spin, so raw
   correlation has a background of `m²` that can hide a crossing. Model A's
   magnetisation changes with time during ordering; changing to a connected
   statistic would define a new observable and alter its historical baseline.
   It is mathematically possible to compute it, but not a neutral fix.
8. **What is an independent run?** A fresh seeded trajectory with its own
   initial condition and random exchanges. The original controlled study
   has eight for each of two compositions and four sizes: 64 total. Saved
   times, image pixels and crops within one run are *not* new independent
   runs. The later extension has 16 **new** runs in each of those eight
   groups: 128 additional trajectories. Resample entire runs for the
   bootstrap, not checkpoints.
9. **Why is 0.258 not a refutation of one-third?** It is the slope of one
   selected finite-window log–log fit. On exactly the same `L=128,c=0.5`
   trajectories, beginning at sweep 2 gave 0.197 instead. The 128-run,
   million-sweep extension gives 0.300 [0.291, 0.309] in its broader
   20,000–1,000,000 window at that composition. That is still a finite-
   window fit, not a demonstrated plateau; its nominal later window is
   unresolved under the fixed fit rule. See the [all-row appendix](../research/runs/main_065_multisize_v1/analysis_declared_v1/appendix_v1/APPENDIX.md).
10. **What does fourfold binning actually do here?** Each 4×4 spin block is
    averaged, then assigned +1 if the average is at least zero and −1
    otherwise. The new pixel is four original sites wide. The exact-tie
    rule and threshold can change *apparent phase fraction*, not just
    resolution. A separate finite-image estimator measures the result;
    never compare its absolute exponent directly with the engine's
    periodic-correlation exponent. See the [paired-shift figure](../figures/fig_core_observation_shift_v1.png).
11. **Did the larger image test repeat the effect?** Yes, in direction. The
    [fixed new-seed holdout](../research/runs/main_065_multisize_v1/image_holdout_v1/REPORT.md)
    measured all 16 new `L=128` runs per composition after the extension
    finished. Its primary bin-minus-native slope shifts were −0.056 and
    −0.074, but processing also shifted apparent +1 fraction by +0.0214
    and −0.0211. The operator was fixed *after* the first effect was known,
    and a repeated sign is not a universal microscope correction.
12. **Why run 40 long 0.6 Tc trajectories?** They provide a symmetric,
    literature-adjacent comparison at `L=128` and 4.5 million sweeps.
    They are internally checked, but *not yet* a reproduction of Majumder
    and Das: the exact majority-filter pass, chord weighting and analysis
    still need a student-reviewed method match, and one size cannot
    reproduce their multi-size scaling argument. See the [crosswalk](MAJUMDER_DAS_METHOD_CROSSWALK_2026-09-18.md).
13. **What does the phase diagram add?** The regular-solution free-energy
    model gives an approximate coexistence curve and spinodal—materials
    language for a miscibility gap and local instability. Exact infinite-
    2D Ising coexistence gives a distinct equilibrium check. Neither an
    exact 2D spinodal, an experimental Fe–Cr diagram nor a kinetic pathway
    follows from those lines. See the [thermodynamics note](REGULAR_SOLUTION_BINODAL_2026-09-18.md).
14. **What did real images establish?** The 42 published static steel masks
    showed a descriptive resolution sensitivity in pixel units. Five loose
    Al–Ge slices showed why scale, specimen region and reconstruction
    comparability must be checked before fitting a real ageing series. A
    separate four-stack Al–Ge test found that a fixed 2D all-Ge length was
    unresolved in some chosen planes and changed under 4× binning in two
    later stages. The original authors distinguish lamellae from
    precipitates, which this all-Ge length does not. None of these checks
    validates Kawasaki kinetics against an alloy or shows outside lab use.
15. **Why might an engineer still care?** Not because the grid predicts
    hardness. A bounded image audit could help a researcher ask whether a
    *measurement they already use* changes under a declared resolution or
    segmentation choice. They must specify the phase, physical scale,
    decision and acceptable variation. A negative pilot is useful if it
    changes the measurement protocol; an internship title alone is not
    validation. See the [partner pilot](PARTNER_PILOT_PROTOCOL_2026-09-17.md).
16. **Do the old Model A and anisotropic Model B slopes prove that
    conservation alone caused their difference?** No. Those historical
    baselines used different lattice widths, couplings and quenches as well
    as different moves. Theory motivates the comparison, but isolating the
    move rule would require matched conditions. The older LaTeX manuscript
    was corrected on this point; see the [claim audit](CLAIM_AUDIT_2026-09-17.md).
17. **What is plotted as `entropy_production` in the engine?** It is the
    interval-averaged heat delivered to the bath divided by temperature,
    by the number of sites and by elapsed sweeps:
    `−⟨ΔE⟩/(N T Δt)` in the code's `k_B=1` units. It is bath entropy
    *flow per spin per sweep*, not total stochastic entropy production.
    Its falling rate does not mean cumulative heat loss has fallen by the
    same factor.
18. **Did the long run establish when finite size starts to matter?** No.
    At one million sweeps, the 15:85 `L=32` mean length is only 0.475
    [0.448, 0.505] of the `L=128` mean length at the same time, and its
    curve flattens. That shows a small-box departure in this observable.
    `L=128` is also finite, and the 50:50 small boxes lose resolvable
    half-height crossings, so one ratio cannot define a universal onset.
19. **What does the narrow late-window failure mean?** All eight nominal
    200,000–1,000,000-sweep fits are marked unresolved because the first
    saved point is 207,231 sweeps: the actual time ratio to one million is
    4.83, below the predeclared factor-five rule. A fit could be calculated
    by changing that rule, but reporting it as if it had passed would be
    selecting a method after seeing the results.

## Three questions I should answer in my own words before asking for review

- Which result surprised me, and what did I personally check when I saw it?
- What is the strongest way a reviewer could show that my claimed
  contribution is already known or methodologically weak?
- Which long-run result would I show first, and what further observation
  would help separate time drift from a finite-size departure?

Write answers from the raw figures and sources, not from memory of this
sheet. State candidly which work was done with AI assistance; the
[contributions record](../AI_USE_AND_CONTRIBUTIONS.md) is part of the project.
