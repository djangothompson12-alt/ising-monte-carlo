# Five-workstream research build: status on 13 September 2026

**Historical snapshot, not live status.** By 18 September the 40-run
reference campaign had completed and passed internal integrity checks (but
not a student-approved paper-method comparison), the 128-run 0.65 Tc
extension was in progress, and a separate
[fixed public Al–Ge image audit](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md)
had produced both unresolved and resolved static measurements. No
experimental growth exponent or external adoption followed. The table below
records what was true **on 13–14 September**, not what is still pending now.

Update on 14 September: the 0.6Tc literature campaign is paused after 7 of
40 planned runs at its compute-budget boundary. It has not been analysed as a
completed benchmark. The 0.65Tc extension has not begun.

This is a build and evidence inventory, not a claim of publication, external
validation or an asymptotic exponent. The existing Model B engine is unchanged:
none of these additions requires altering its Metropolis exchange rule or the
off-critical connected correlation. Model A's raw-correlation convention is
also unchanged.

| Workstream | Implemented now | Evidence not yet available |
|---|---|---|
| Matched literature benchmark | Frozen 0.6 Tc, c=0.5, L=128, 40-independent-run plan; majority-filter/chord measurement; a complete-inventory and student-method-verification gate; fixed-window analysis with whole-run bootstrap and a *measured*, not tuned, initial-length sensitivity. | Paused at 7/40. Its output cannot yet be compared with Majumder–Das. The student must check the exact source method and set `student_verified` only after doing so. |
| Main 0.65 Tc size/time extension | Separate frozen plan for c=0.5 and c=0.15, L=32/64/96/128, 16 fresh runs each, 1 million sweeps; dedicated analysis that rejects partial runs and reports declared windows, unresolved directions and sensitivity to the 0.15 length/L filter. | 128 costly replicas have not begun; run after the benchmark stops to avoid machine contention. A finite-size onset is a result to test, not an input. |
| Dynamic scaling | Exploratory 2D connected-correlation and radial structure-factor rescaling of the existing eight-replica, L=128 archive; raw and rescaled panels, overlap descriptors, immutable input hashes. | The limited common wave-number range and short early domains do not demonstrate full scaling collapse. Repeat and refine only after longer independent runs. |
| Measurement reliability | Operator-by-operator original/fresh-seed map for blur, binning and cropping; paired length/exponent changes, unresolved fractions and phase-fraction bias are retained, not pooled into a universal correction. | These are simulated image transformations. The fresh small holdout is a replication check, not independent experimental validation. |
| Real-image review | Written intake, rights/metadata/phase/ROI questions, decision criteria, and a machine-readable template for a specialist-approved ageing series. | No suitable new image series or expert review has been obtained. Existing AlGe slices support feasibility only. No material time calibration or kinetics comparison is justified. |

The exploratory scaling output is in
`research/runs/overnight/dynamic_scaling_v2/`: four checkpoints between about
1,000 and 200,000 sweeps from eight L=128 replicas per composition. Correlation
shapes align fairly closely over the displayed `r/ell <= 3` range, but the
threshold-based `ell` itself enforces a shared crossing near `r/ell = 1`.
The common scaled Fourier range ends below `q ell = 0.9`, too narrow to call a
broad structure-factor collapse. Neither panel establishes a 1/3 exponent.
The original/fresh image-operator map is in
`research/runs/measurement_reliability_map_v1/`; its crop and binning panels
should be described as sensitivity to specific operators and seed sets, not as
a transfer function for a real microscope.

## Reporting order

1. Put the scientific question and the model's scope before an application story.
2. Show raw ensemble trajectories, sample counts and what is unresolved.
3. Place the matched c=0.5 benchmark beside the main 0.65 Tc study only after
   its own measurement definition and source-method cross-check are complete.
4. For c=0.5 and c=0.15, compare sizes at the **same times**, primary
   unfiltered windows first; distinguish shared time drift from size-dependent
   departure. Show the length/L cut only as a sensitivity analysis.
5. Use the scaling and observation plots to challenge the robustness of an
   exponent claim, not to manufacture agreement with 1/3.
6. Treat real images as a separate, permissioned measurement audit. Report a
   failed validation attempt honestly if the metadata do not support kinetics.

## Commands after the relevant inputs are complete

```bash
# After all 40 symmetric runs: student verifies the source-method declaration;
# only then produce reference measurements and their analysis.
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.reference_benchmark --help
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.analyse_reference_benchmark --help

# After all 128 fresh 0.65 Tc runs:
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.analyse_main_extension \
  research/runs/main_065_multisize_v1 \
  --output research/runs/main_065_multisize_v1/analysis_declared_v1
```

If someone asks to review the work now, share the technical methods, existing
eight-replica figures, test results, and a concrete request for criticism. Do
not present pending runs as findings or a helpful conversation as an endorsement.
