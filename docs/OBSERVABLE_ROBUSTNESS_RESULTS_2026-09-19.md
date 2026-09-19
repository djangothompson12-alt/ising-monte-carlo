# Which conclusions survive a change of observable?

*Post-result AI-assisted robustness audit, 19 September 2026. The protocol was
frozen before these full-extension values were calculated, but after the
primary correlation results and an earlier estimator pilot were known. This is
not a blind confirmation or external review.*

## Design

The [frozen protocol](../research/FULL_EXTENSION_OBSERVABLE_ROBUSTNESS_PROTOCOL_2026-09-19.md)
remeasured all 9,600 saved states from the completed 128-trajectory extension.
It compared four existing, tested quantities on identical trajectories:

- the primary connected-correlation half-height length;
- the area under its positive lobe;
- an inverse first moment of the full structure factor; and
- the inverse fraction of unlike nearest-neighbour bonds.

Within every fit, the same checkpoint had to be resolved for every estimator
in every one of the 16 trajectories. The five time windows were inherited from
the extension analysis. Paired 95% intervals used 2,000 whole-trajectory
bootstrap draws. Matched-size ratios resampled trajectories independently
between sizes. All 160 fit rows, 48 size-ratio rows and 9,600 per-state rows
are retained in [`observable_robustness_v1`](../research/runs/main_065_multisize_v1/observable_robustness_v1/REPORT.md).

## Result 1: the numerical exponent is not observable-invariant

At `L=128`, the common-mask fits were:

| Composition | Window | Half-height | Positive-lobe | Spectral moment | Inverse-interface |
|---:|---|---:|---:|---:|---:|
| 0.50 | 1,000–200,000 | 0.256 | 0.248 | 0.166 | 0.204 |
| 0.50 | nominal 20,000–1,000,000* | 0.285 | 0.282 | 0.187 | 0.216 |
| 0.15 | 1,000–200,000 | 0.252 | 0.241 | 0.151 | 0.182 |
| 0.15 | 20,000–1,000,000 | 0.281 | 0.271 | 0.166 | 0.182 |

*At 50:50, the common mask retained only 21,336–246,834 sweeps because the
positive-lobe length later became unresolved in at least one trajectory. It
would be misleading to call that row a complete million-sweep comparison.

The half-height and positive-lobe estimates are relatively close, but the
full-spectrum and interface proxies are systematically lower. This does not
mean either pair is wrong. Thermal short-wavelength power and small interfaces
enter the latter two definitions, whereas the correlation crossings emphasise
a larger structural scale. The important conclusion is that a fitted
finite-window exponent must always be reported with its observable.

The direction of the later-start shift is shared by all four point estimates
at 50:50 over the shortened common range. At 15:85, three estimates increase,
but the inverse-interface value is essentially unchanged (`0.18226` to
`0.18233`). Therefore **time-window dependence exists, but the size of the
drift is not an observable-independent physical quantity**.

## Result 2: the late 15:85 small-box departure is robust

At exactly 1,000,000 sweeps, the `L=32`/`L=128` mean-length ratios were:

| Observable | Ratio | 95% whole-trajectory interval |
|---|---:|---:|
| Half-height | 0.475 | 0.445–0.504 |
| Positive-lobe | 0.477 | 0.451–0.504 |
| Spectral moment | 0.648 | 0.617–0.674 |
| Inverse-interface | 0.640 | 0.598–0.679 |

Every resolved definition places the small system well below `L=128`. The
magnitude depends on the measurement, but the direction does not. This is
stronger evidence that the late `L=32`, 15:85 flattening is a real finite-box
feature of these trajectories rather than an artefact of one correlation
threshold. It still does not locate a universal onset or prove that `L=128`
is in the thermodynamic limit.

For 50:50 at the same time, the half-height and positive-lobe measures are
unresolved under the strict all-trajectory rule. The spectral and
inverse-interface ratios are resolved at `0.618` and `0.591`. The unresolved
rows are part of the result: once the morphology approaches the box scale,
some correlation-based lengths stop being measurable rather than merely
becoming noisier.

## What this adds—and what it does not

This audit tightens the paper's hierarchy of claims:

1. **Robust:** the late 15:85 small-box departure appears under four different
   morphology measures.
2. **Conditional:** fitted exponents rise or remain steady when the fit begins
   later, but the amount depends strongly on the observable and available
   common time range.
3. **Not supported:** one finite-window exponent can be quoted as the true
   growth law, or one estimator can be called the physical particle radius.

That distinction is more useful to a reviewer than another parameter sweep.
It shows which conclusion survives an adversarial measurement change and
which must remain qualified. The audit is still entirely computational and
AI-assisted. A specialist must judge whether the four quantities and the
strict common-mask rule are the right robustness test.
