# A paired check of fitting-window sensitivity

*AI-assisted, post-result analysis of the completed 64-run campaign, 18 September
2026. This check was prompted by an already visible window effect. It is not a
prospectively selected discovery test or a measurement of the asymptotic
coarsening exponent. The running million-sweep extension was not touched.*

The earlier table showed separate bootstrap intervals for each fitted slope,
but the 2–200,000 and 1,000–200,000-sweep fits reuse the **same eight
trajectories** at each composition. Separate error bars are not the right way
to quantify the difference between those correlated estimates. I therefore
resampled entire trajectories with identical indices for both windows in each
of 5,000 bootstrap draws and recalculated `α_late − α_early`.

The length is the mean of the Model B directional connected-correlation
half-height crossings. The slope is fitted to `log(ensemble mean length)`
against `log(sweeps)`. This audit uses the original analysis rule
`mean length/L < 0.15` and keeps each original full-ensemble time mask fixed
during resampling. Each row uses `L=128`, `T=0.65 Tc`, `Jx=Jy=1` and eight
independent runs. The actual late window begins at sweep **1,069**. The
original raw files, not images or interpolated curves, are the inputs.

| +1 fraction | Earlier nominal window | Earlier α | Later α, 1,000–200,000 | Later minus earlier, 95% paired bootstrap interval |
|---:|---|---:|---:|---:|
| 0.50 | 2–200,000 | 0.197 | 0.258 | +0.061 [0.057, 0.065] |
| 0.50 | 100–200,000 | 0.233 | 0.258 | +0.025 [0.022, 0.028] |
| 0.15 | 2–200,000 | 0.196 | 0.260 | +0.064 [0.057, 0.071] |
| 0.15 | 100–200,000 | 0.236 | 0.260 | +0.024 [0.019, 0.029] |

The positive shift is stable under replica resampling *for these selected
windows and this observable*. That is stronger evidence for a reproducible
finite-window effect than merely noticing that two point estimates differ.
It still does **not** show that the later window is asymptotic, that the true
law differs from or equals one-third, or that finite size caused the shift.
Bootstrap intervals do not include uncertainty from choosing the observable,
the fit windows, the `length/L` threshold or the physical model. Since the
audit followed inspection of the original table, it should be described as
a sensitivity check, not confirmatory significance testing.

The [CSV](../research/results/paired_window_sensitivity_2026-09-18/paired_window_differences.csv)
records actual retained times, point counts and all 5,000 valid draws per row;
the [provenance file](../research/results/paired_window_sensitivity_2026-09-18/provenance.json)
records the 16 selected NPZ hashes, source hash and original campaign hashes.
The calculation is in [paired_window_sensitivity.py](../research/paired_window_sensitivity.py)
and has a constant-power-law control in the tests.
