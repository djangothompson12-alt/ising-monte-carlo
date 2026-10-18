# Resolution re-analysis and draft brief, 18 October 2026

AI-assisted work on existing archives; no new simulations. Not yet reviewed by
any outside specialist.

- `l128_resolution_reanalysis/`: pre-declared protocol (`PROTOCOL.md`, written
  by the AI assistant before any coarse measurement, not a student
  pre-registration), script, per-bin results and verdicts. Re-run from the repo
  root with `python3 review/resolution_reanalysis_2026-10-18/l128_resolution_reanalysis/reanalyse.py`
  (needs numpy and scipy; about 10 s). `posthoc_unresolved_sensitivity.*` is a
  labelled post-hoc check, not a primary result.
- `figures/`: key figure (exponent error against native domain size in coarse
  pixels) and the script that draws it from `bin_slopes.csv`.
- `brief_v3/`: restructured two-page draft brief. The `[DJANGO WRITES]` blocks
  are deliberately unfilled; this is not an approved or sent version.

Headline: at 4x coarsening, the fraction-matched exponent error falls from
-0.051 / -0.066 (domains below one coarse pixel) to -0.012 / -0.017 (one to two
coarse pixels) at 50:50 / 15:85. The pre-declared study-level verdict is "not
established", and resolution is confounded with time. See
`l128_resolution_reanalysis/RESULTS.md`.
