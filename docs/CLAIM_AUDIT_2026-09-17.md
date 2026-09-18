# Claim audit for the next technical report — 17 September 2026

This is an evidence ledger, **not** prose for the student to submit as their
own paper. It audits the central numerical and interpretive claims in the
completed 64-run and observation studies against saved outputs. It is not a
line-by-line independent replication of every citation or older manuscript
result. The student must read the sources, inspect the figures, and approve the
interpretation before sharing a report.

## Completed-data claims

| Claim the report may make | Checked evidence | Boundary that belongs beside it |
|---|---|---|
| The isotropic 0.65 Tc study has 64 independent seeded Model B trajectories (L=32,64,96,128; c=.50,.15; eight per group), each to 200,000 sweeps. | `research/runs/overnight/manifest.json`, `status.json`; `python -m research.verify_study research/runs/overnight --source-root research/frozen_sources/2026-09-10` returned 64 distinct seeds, 3,840 snapshots and matching source hashes on 17 September. A separate source-matched preparation replay checked the first recorded heat interval in all 64 main and eight repeat files. | This verifies storage/energy accounting, not an independent implementation of the dynamics. It does not prove that the domain estimator measures a unique physical particle radius. |
| The archived directional correlations and lengths can be reproduced from the saved lattices. | The separate [observable audit](ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md) recomputed 7,680 main-study and 608 repeat-study directional lengths, including the same 35 unresolved main-study values, to floating-point tolerance. | This tests stored-measurement consistency, not the physical correctness of the Monte Carlo dynamics or suitability of the observable for real materials. |
| The reported primary growth table follows the declared archived analysis recipe. | A separate arithmetic audit rebuilt all 48 fit rows and 480 ensemble-mean/SE rows from the hash-matched main trajectories; see the [audit note](ARCHIVED_OBSERVABLE_AUDIT_2026-09-17.md). | Agreement checks the calculation, not whether the selected window or estimator is physically optimal. |
| At c=.50, L=128, the primary effective exponent changes from 0.197 (nominal 2–200,000 sweeps) to 0.258 (1,000–200,000). | Exact values 0.197073 and 0.257745 in `research/runs/overnight/analysis/exponents.csv`; analysis command and hashes in `docs/OVERNIGHT_RESULTS.md`. | These fits overlap in data; they are not independent experiments. They are finite-window slopes, not asymptotic exponents. |
| For L=64,96,128, late-start slopes are about 0.26 for both c=.50 and c=.15. | Six rows at nominal 1,000–200,000 in the same `exponents.csv`; intervals and actual retained times in `docs/OVERNIGHT_RESULTS.md`. | Similar effective slopes neither prove composition-independent asymptotics nor explain why they are below 1/3. |
| The smallest system has additional late-time problems. | c=.15 L=32 length flattening and c=.50 L=32 unresolved values are documented in `docs/OVERNIGHT_RESULTS.md`; inspect `growth_c0.png` and `growth_c1.png`. | Do not compare c=.50 L=32's nominal late fit with large L as though it spans the same times: it ends at 34,974 sweeps. Do not say finite size *alone* explains all sub-1/3 slopes. |
| Four length definitions on the same c=.50, L=128 snapshots give about 0.258, 0.251, 0.167 and 0.204 over nominal 1,000–200,000 sweeps. | Exact rows in `research/runs/overnight/estimator_analysis_v1/paired_fits.csv` for `threshold_05`, `positive_lobe`, `spectral_moment`, `inverse_interface_proxy`. | These are different observables, not four estimates of a known true radius. Their disagreement alone does not identify a physical coarsening mechanism. |
| Fourfold binning **plus thresholding** shifts the image-based fitted exponent by −0.056 at c=.50 and −0.072 at c=.15 in the original L=128 ensemble; shorter fresh-seed runs show −0.057 and −0.073. | `research/runs/overnight/imaging_v1/paired_fits.csv` and `research/runs/imaging_validation/imaging_v1/paired_fits.csv`, rows `bin4`, nominal 1,000–20,000. | New ensemble has four replicas/composition and a different checkpoint grid. This is an observation-pipeline effect, not a resolution-only effect or a microscope-independent correction. |
| The 4× operation's slope shift can be decomposed into greyscale blocking and binary thresholding on the same snapshots. | [The post-hoc analysis](BINNING_DECOMPOSITION_RESULTS_2026-09-17.md) checks both original and fresh L=128 cohorts and two fit windows. | The relative contributions change across composition and window; they are numerical stage differences, not unique physical causes. |
| The 0.6 Tc, L=128 reference campaign has **40 completed trajectories**. The 0.65 Tc extension was incomplete at this ledger's original 17 September check; it completed on 18 September (addendum below). | [Reference integrity check](REFERENCE_RUN_INTEGRITY_2026-09-17.md): 40 unique seeds, 3,600 snapshots, matching plan/source hashes and independently recomputed stored observables. | Completion is not a matched-paper result. Do not call the 40-run case a reproduction: the student's literature-method declaration remains unverified, and one size cannot reproduce a multi-size finite-size claim. |
| The AlGe images demonstrate a data-quality problem, **not** experimental validation. | `docs/MEASUREMENT_STUDY_RESULTS.md` and `research/runs/alge_feasibility/manifest.json`/QA outputs. | The five selected slices are not registered specimens; the 195-minute reconstruction has different dimensions/background and unresolved scale metadata in the current parser. No experimental exponent or physical sweep-to-hours calibration has been established. |

Two visual spot checks on 17 September: `analysis/growth_c0.png` labels its
bands as replica **standard errors** and its proposed z=3 collapse as **not
fitted**. `imaging_v1/observation_ratios_c0.5.png` shows strong early-time
operator effects; its very early points are not the declared primary fit
window. Figure captions should retain those qualifications. A full page-level
figure inspection is still required before release.

## 18 September addendum — later checks, not new kinetics claims

| Additional claim | Evidence | Boundary |
|---|---|---|
| The regular-solution coexistence and spinodal curves are a **mean-field** thermodynamic guide; the exact infinite-2D Ising coexistence check differs. | [Common-tangent derivation](REGULAR_SOLUTION_BINODAL_2026-09-18.md), [exact boundary comparison](EXACT_ISING_COEXISTENCE_CHECK_2026-09-18.md), `phase_diagram.py` tests and figures. | No exact 2D spinodal or measured Fe–Cr phase diagram is thereby obtained. Equilibrium coexistence does not identify a finite-run nucleation mechanism. |
| A synthetic image with an imposed geometric one-third scale growth is not necessarily measured at one-third by a finite-image estimator. | [Known-growth control](SYNTHETIC_KNOWN_GROWTH_CONTROL_2026-09-18.md) and versioned output/provenance. | Its aligned square pattern has different geometry and even a different bias sign from the Kawasaki result. It does not explain the observed low Model B slopes. |
| The real published steel masks show static resolution sensitivity. | [All-42-mask test](METALDAM_REFERENCE_MASK_SCALE_RESULTS_2026-09-18.md), per-image CSV and hashes. | Pixel-unit descriptive audit only; images may share specimens, and no real-alloy ageing exponent or user adoption was tested. |
| A larger new-seed repeat of the selected image operator has been specified **before the extension finished**. | [Fixed holdout protocol](../research/PROSPECTIVE_IMAGE_HOLDOUT_2026-09-18.md) and code/tests that reject partial 128-run input. | It was designed after the original and first fresh-seed results, not before any data existed. No holdout result may be claimed yet. |
| The L=128 fitting-window shift is stable when the *same* eight trajectories are resampled in both fits. | [Paired window audit](PAIRED_WINDOW_AUDIT_2026-09-18.md), [all four rows](../research/results/paired_window_sensitivity_2026-09-18/paired_window_differences.csv) and source/raw hashes. | This is a post-result, conditional bootstrap for chosen windows; it neither selects an asymptotic window nor attributes the shift to finite size. |
| A 4× observation step on published segmented Al–Ge images is not uniformly measurable under a fixed central-ROI rule. | [Bounded real-image audit](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md), [all 44 planes](../research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv), [hashes and summary](../research/results/alge_static_operator_2026-09-18/summary.json). | One aged specimen, correlated slices and unverified cross-stage registration. The two resolved late-stage static ratios are not a growth exponent or experimental validation of Kawasaki dynamics. |

Additional prior art matters to the paper's novelty statement: [Ezad et al.
(2022)](https://doi.org/10.2138/am-2021-7797) compared image-analysis methods
on experimental grain-growth data and found consequences for fitted kinetic
interpretation. The student's paired Kawasaki observation test is not the
first demonstration that image measurement can affect inferred kinetics.

## 18 September completion audit — new local results

| Claim the working draft may make | Checked evidence | Boundary that belongs beside it |
|---|---|---|
| The 0.65 Tc extension completed all 128 new, million-sweep trajectories: 16 per width/composition group. | Local `research/runs/main_065_multisize_v1/status.json` is complete; `research.verify_study` checked 128 unique seeds, 9,600 snapshots, source/plan identity, conserved magnetisation and later heat intervals. `first_interval_replay_v1.json` independently recomputed the first heat interval for all 128. | Internal checks do not validate a real alloy or constitute a separately written dynamics implementation. The raw files remain local, not in a public release. |
| Saved observables and declared analyses match recomputation. | Local `observable_audit_v1.json` checked 19,200 directional lengths and every saved correlation and interface fraction; `analysis_declared_v1/independent_table_audit.json` rebuilt 600 ensemble rows, 80 fit rows and 450 matched-size rows from hash-matched raw files. | One length exactly at the strict 0.5 boundary flipped between two FFT roundings. It is counted explicitly as a numerical ambiguity, not a changed engine measurement or physical disagreement. |
| At L=128, the 20,000–1,000,000-sweep effective slopes were 0.300 [0.291, 0.309] at 50:50 and 0.281 [0.268, 0.293] at 15:85. | Local `analysis_declared_v1/fit_windows.csv`; all rows, actual windows and unresolved cases in `appendix_v1/APPENDIX.md`. | These are broad finite-window slopes, not a one-third plateau. Every 200,000–1,000,000 nominal fit fails the predeclared factor-of-five time-span rule. |
| The smallest 15:85 system departs at late matched time. | At one million sweeps, `matched_size_ratios.csv` gives L32/L128 = 0.475 [0.448, 0.505] for mean half-height lengths. The plotted L32 curve flattens. | This supports a small-box effect in this run and observable, not a unique onset time. L128 is itself finite; 50:50 small-box comparisons become unresolved late. |
| The selected image operation repeats a negative exponent shift on 16 new L128 seeds per composition. | Local `image_holdout_v1/paired_fits.csv` and `REPORT.md`: primary bin-minus-native shifts −0.056 [−0.059, −0.053] at 50:50 and −0.074 [−0.077, −0.069] at 15:85. | The protocol followed earlier positive findings; this is directional repetition, not blind discovery. Apparent +1 fractions shift by +0.0214 and −0.0211 respectively, so it is not a resolution-only effect or universal microscope correction. |

## Important corrections to the older `manuscript/main.tex`

1. The Metropolis detailed-balance example had a sign error, corrected in the
   LaTeX source on 17 September: when a forward move has `ΔE < 0`, the
   reverse acceptance is `exp(βΔE) < 1`, not `exp(−βΔE) < 1`. The underlying
   rule and engine are unchanged; the tracked PDF remains stale.
2. It calls Model A's binary interfaces an ordinary *grain-growth* model.
   Curvature-driven kinetics is a useful analogy, but two Ising states do not
   represent a polycrystal's many orientations or crystallographic grain
   boundaries. Avoid saying it **directly** simulates alloy grain growth.
3. It calls neighbour exchange the *correct description* of atomic transport
   in a binary alloy and later a *first-principles complement* to phase-field
   modelling. These overstate a 2D, vacancy-free, nearest-neighbour model with
   uncalibrated Monte Carlo time. Say it is a minimal conserved-dynamics model.
4. It says ordered patches *nucleate all over* after a quench. Nucleation and
   spinodal amplification are different early-stage mechanisms; morphology
   and this model alone do not establish which occurred in a real alloy.
5. Its section on correlation length initially says the same raw definition
   is used in both models, but its later section correctly distinguishes
   Model A's raw correlation and Model B's normalized connected correlation
   off critical composition. The next report must state that asymmetry up
   front and preserve Model A's time-dependent magnetization signal.
6. The old concentration-sweep and anisotropic numbers are real prior
   exploratory work but are **not** the newly replicated 64-run result. Keep
   their run settings and status separate. The current report should not
   recycle the old manuscript as if it already included the observation study.
7. The old Model A draft value 0.4841 is not the refit of the archived CSV;
   `README.md` reports 0.4999 with its current fit settings. Do not reuse
   0.4841 without recovering its original data and settings.
8. The Model A temperature-sweep code stores
   `Var(|M|)/(N T)` under the old `susceptibility` field name. That is an
   absolute-magnetization fluctuation proxy, **not** the zero-field magnetic
   response `Var(M)/(N T)`. The README and visualizer label now distinguish
   them. `fig1_phase_transitions_corrected.png` was redrawn from the unchanged
   archived CSV; the original figure is retained only as a historical artifact.
9. The old Model A and anisotropic Model B baseline curves differ in lattice
   width, couplings and quench conditions as well as update rule. Their
   fitted-slope gap cannot isolate conservation's *causal* effect. The
   LaTeX introduction, comparison caption and conclusion were corrected
   on 18 September; a future matched-condition comparison would be a
   distinct experiment.
10. The old per-spin bath-entropy-flow equation omitted division by
    `N=L²`, although both engines actually divide the total interval energy
    change by `N`. The LaTeX equation now matches the code and identifies
    the historical `entropy_production` field as bath flow, not total
    stochastic entropy production. The tracked PDF remains stale.

## Status and authorship gates

- The old manuscript PDF is stale relative to the LaTeX source. Do not send it
  as the present technical report.
- The updated report should cite actual selected windows, observables and
  independent-replica counts, including unresolved cases and limitations.
- A reviewer may criticise originality or usefulness; the repository does not
  prove either. A response to feedback is evidence of revision, not an
  endorsement unless the reviewer explicitly agrees to that description.
- The 2013 Majumder–Das study already tests temperature and composition
  dependence in 2D conserved Ising coarsening. Do not describe our asymmetric
  mixture or low finite-window slope as new by itself; see the
  [literature comparison](LITERATURE_COMPARISON_2026-09-17.md).
- A [2021 Cahn–Hilliard study](https://doi.org/10.1039/D1CP03229A) reports
  off-critical fitted exponents below one-third in a different conserved
  model, with an observable-dependent difference. The 0.65 Tc extension must
  not be framed as a foregone demonstration that every low slope is only
  finite time or size. Compare assumptions and methods first.
- Record substantive AI help in `AI_USE_AND_CONTRIBUTIONS.md`. The student's
  own understanding, choices and final wording must remain identifiable.
