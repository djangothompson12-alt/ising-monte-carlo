# What caused the apparent 4×-binning slope shift?

**Exploratory AI-assisted follow-up, 17 September 2026.** This analysis was
designed *after* the original controlled-observation results, to understand
them rather than to add an independent confirmation. The simulation trajectories
and engines were unchanged. See the [local method declaration](../research/BINNING_DECOMPOSITION_PROTOCOL.md)
and `research/decompose_binning.py`.

## A more precise question

The earlier result called `bin4` is not "resolution" alone: it first averages
each 4×4 site block and then turns the greyscale result back into a binary
mask. This follow-up measures the same finite-image connected-correlation
length at each stage, keeping the original-site pixel spacing:

`full binary image → 4×4 greyscale block average → binary threshold at zero`.

It also repeats the last step with exact zero-valued blocks assigned to −1
instead of +1. All stage comparisons use the **same archived trajectories,
replicas and jointly resolved checkpoints** within each campaign, so their
point-estimate slope changes add arithmetically. The 64-run campaign has eight
L=128 replicas per composition; the shorter fresh-seed repeat has four.

The [two-window decomposition figure](../figures/fig_binning_decomposition_v2.png)
shows the point estimates. Its bars are **not** uncertainty intervals; consult
the paired-fit tables for those.

## Primary 1,000–20,000-sweep window

Changes below are in fitted effective exponent, not in the physical growth
law. Negative means a lower fitted slope than the preceding stage. Times
actually retained were 1,069–19,557 sweeps in the main campaign and
1,224–20,000 in the repeat.

| Campaign | Composition | n | Greyscale block minus full | Binary threshold minus greyscale | Total binary `bin4` minus full | Tie + versus tie − |
|---|---:|---:|---:|---:|---:|---:|
| Main | 0.50 | 8 | +0.0001 | −0.0557 | −0.0557 | −0.0004 |
| Main | 0.15 | 8 | −0.0278 | −0.0446 | −0.0724 | +0.0041 |
| Fresh repeat | 0.50 | 4 | +0.0003 | −0.0573 | −0.0570 | −0.0004 |
| Fresh repeat | 0.15 | 4 | −0.0258 | −0.0477 | −0.0735 | +0.0074 |

For example, the main c=0.50 greyscale-stage difference has a 95% paired
whole-replica bootstrap interval of **[−0.0040, +0.0035]**, while the
following threshold-stage difference has **[−0.0584, −0.0530]**. In the
four-replica fresh repeat those intervals are **[−0.0021, +0.0035]** and
**[−0.0623, −0.0535]**. They quantify variation from resampling these
trajectories at a fixed resolved-time mask; they are not uncertainty on the
choice of method, fitting window, or a population of real alloys.

The previously reported full and `bin4` lengths were recomputed and matched
their saved observation table for all **2,528** file/checkpoint values. The
new stage measurements therefore do not depend on a changed baseline
definition. Full paired-bootstrap intervals, retained-point counts and
individual measurements are saved in the two `paired_fits.csv` and
`per_snapshot.csv` outputs under
`research/runs/{overnight,imaging_validation}/binning_decomposition_v1/`.
Those folders are local ignored analysis output; rerun the script for a new
output name to reproduce them.

For the symmetric mixture in this **short** window, the binary threshold
step produces almost all of the original `bin4` slope change. In the dilute
mixture both block averaging and thresholding contribute. Exact-zero ties
matter much less to these slopes, although they visibly change the apparent
phase fraction. Across primary-window snapshots, the median fraction of
exact-zero coarse blocks was about 0.042 (main) and 0.039 (repeat) at c=0.50,
and 0.0205 in both campaigns at c=0.15. The c=0.15 image's original +1
fraction is about 0.15; after 4× thresholding its median apparent fraction
was 0.131 with ties assigned +1 and 0.110 with ties assigned −1 in the main
campaign. Those are descriptive snapshot medians, not independent samples.

## Important time-window reversal

On the main campaign's longer nominal 1,000–200,000-sweep window, the balance
changes. At c=0.50, greyscale blocking changes the slope by −0.0246 and the
subsequent threshold by −0.0113, for a total −0.0358. At c=0.15 the
respective changes are −0.0371 and −0.0111, total −0.0482. Thus the
short-window description "mostly thresholding" **does not generalise across
the full run**. The apparent contribution of each processing stage is itself
fit-window dependent.

This is a stronger methodological statement than "lower image resolution
reduces the exponent": the effect depends on composition, binarisation and
the time interval. The greyscale length is a different statistic from a
binary-domain length, so these stage differences are a transparent numerical
decomposition of *one pipeline*, not uniquely identified physical causes.
The paired intervals omit model, observable and mask-selection uncertainty;
four-replica repeat intervals are especially limited. No universal threshold
correction or microscope response is inferred.

## How to use this in a paper or expert conversation

This deserves a concise figure/table in a methods-oriented discussion only
after the student can explain how a 4×4 average, threshold at zero and
half-height correlation length are calculated. A reviewer should be asked
whether a greyscale-versus-binary comparison reflects a real micrograph
analysis decision they care about. It does **not** validate a physical alloy
growth exponent or show that the Kawasaki dynamics itself changed.

Reproduction, with **new** output folders:

```bash
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.decompose_binning \
  research/runs/overnight research/runs/overnight/imaging_v1/observations.csv \
  --output research/runs/overnight/binning_decomposition_new
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.decompose_binning \
  research/runs/imaging_validation research/runs/imaging_validation/imaging_v1/observations.csv \
  --output research/runs/imaging_validation/binning_decomposition_new
```
