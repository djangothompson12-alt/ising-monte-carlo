# A second length measurement and a majority-filter check

AI-assisted exploratory appendix, 26 September 2026. The existing research
question stays fixed: after reducing image resolution, is matching the native
species-site fraction sufficient to preserve the native finite-window exponent?
This is not a new holdout, a new simulation campaign or an exact reproduction
of Majumder and Das. The data and original half-height results were already known.

## What was actually done

The same 16 archived L=128 trajectories were reanalysed: eight at c=0.50 and
eight at c=0.15, Jx=Jy=1, T=0.65 Tc. Each contributed 24 saved lattices between
1,119 and 20,000 post-quench sweeps. All times were resolved in every comparison;
none were removed. These short windows test observation sensitivity, not the
asymptotic growth law. No simulation state or dynamics were changed.

Three observations were compared: native pixels; 4x4 block means followed by
nearest-count fraction matching; and one simultaneous five-site majority pass.
The fraction-matched lengths were averaged over the same five fixed tie
priorities within each trajectory/time. Those ties are not extra replications.

Two length definitions were applied to each observation: the existing
normalized finite-image covariance half-height, and the mean complete
foreground chord. Chords are straight stretches of +1-labelled pixels bounded
by background at both ends. Each horizontal or vertical chord is counted once;
edge-touching chords are excluded but counted separately. Both axes must supply
complete chords. Pixel spacing is converted to native lattice units.

## Results in plain English

The effect of processing depends on the length definition. Fraction matching
changed the chord-based exponent much less than the half-height exponent.
Majority filtering moved the two fitted exponents in opposite directions.
For fraction-matched c=0.15 images, the two definitions gave nearly the same
exponent. We should therefore **not** claim that every measurement change
causes a large discrepancy, or that one definition is the true answer.

| Species fraction | Length definition | Native exponent | Fraction-matched exponent | Majority-filtered exponent |
|---|---|---:|---:|---:|
| 0.50 | Half-height | 0.23141 | 0.18094 | 0.21924 |
| 0.50 | Foreground chord | 0.17623 | 0.16886 | 0.19311 |
| 0.15 | Half-height | 0.24214 | 0.16563 | 0.23074 |
| 0.15 | Foreground chord | 0.17816 | 0.16534 | 0.21730 |

All nine planned contrasts per composition were retained. Key processing
differences (processed minus native), with paired 95% bootstrap intervals:

| Fraction | Processing | Half-height shift | Chord shift |
|---|---|---|---|
| 0.50 | Fraction matching | −0.05047 [−0.05293, −0.04782] | −0.00738 [−0.01110, −0.00364] |
| 0.50 | Majority pass | −0.01217 [−0.01295, −0.01127] | +0.01688 [+0.01565, +0.01831] |
| 0.15 | Fraction matching | −0.07651 [−0.08006, −0.07255] | −0.01281 [−0.01534, −0.00999] |
| 0.15 | Majority pass | −0.01140 [−0.01231, −0.01054] | +0.03914 [+0.03535, +0.04255] |

For c=0.15 fraction-matched images, chord minus half-height is −0.00028,
with interval [−0.00564, +0.00453]. An interval including zero does not prove
exact equivalence, but these data do not resolve a difference for that contrast.

The intervals resample eight whole trajectories 1,000 times, with the same
resampled indices across all measurements. They are descriptive and unadjusted
for the 18 correlated comparisons. They measure run-resampling uncertainty,
not systematic bias or uncertainty about every analysis choice.

## Limits that must stay beside the results

- Complete-chord selection favours shorter chords. The ensemble-mean excluded
  run fraction reaches about 21.2% in the matched 50:50 images and 14.0% in
  the matched minority images. It changes with time and may affect chord slopes;
  it has not been corrected away. This is not a finite-size correction.
- The majority pass changes observed fraction and geometry together. At
  nominal c=0.15, its ensemble-mean observed fraction ranges from 0.1353 to
  0.1427. This does not isolate the effect of composition alone.
- Fraction matching is exact for 50:50. The actual native minority fraction
  is 0.1500244; the nearest coarse-grid count gives 0.1503906. Report the
  quantization residual rather than calling this exact conservation.
- Here fraction means labelled species-site/pixel fraction. In a real alloy,
  phase volume fraction and chemical composition are not generally identical.
- The chord convention is not a radius, uniquely correct size, or exact
  implementation of the literature measurement. This reanalysis does not
  determine why the native exponents are below 1/3 or validate an alloy forecast.

## Verification and where to read it

The original factor-four native/fraction-matched half-height estimates and
intervals reproduced to within 6e−17 using the original functions on archived
snapshots. This is a replay, not an implementation-independent check. The new
chord/filter and inference tests include analytic sizes, an independent scalar
counting oracle, boundary handling, units, source immutability, shared masks,
known power laws and paired-bootstrap equivalence. See the dated AI-use record
for the final complete-suite result.

The protocol was written before the new measurement run. The v2 rerun clarifies
report wording and original-mask indexing after the first successful v1 pass;
it does not change any processing parameter, window, observable or result beyond
floating-point roundoff. Input, primary-evidence and source hashes were checked
before and after each run. The original two-page brief and evidence pack are unchanged.

- [Readable results, figures and every contrast](../research/results/chord_observation_sensitivity_2026-09-26_v2/report.html)
- [Exploratory protocol](../research/CHORD_OBSERVATION_PROTOCOL_2026-09-26.md)
- [Results and masks](../research/results/chord_observation_sensitivity_2026-09-26_v2/summary.json)
- [Input/source verification](../research/results/chord_observation_sensitivity_2026-09-26_v2/manifest.json)

Reproduce from the repository root with the numerical environment:

```sh
MPLCONFIGDIR=/private/tmp/kawasaki_chord_mpl .venv311/bin/python -m research.observation_sensitivity --output research/results/chord_observation_replay_new
.venv311/bin/python -m unittest tests.test_chord_observation tests.test_observation_sensitivity -v
```

Choose a new output directory; the runner refuses to overwrite existing evidence.
The referenced raw archives must be present locally; they are not promised to be
available through the public repository. No results were pushed or sent externally.

## How this belongs in the report

Keep this as a supporting sensitivity check, not a new main question or claim of
novel measurement physics. A reviewer can now see a smaller effect, opposite
directions and a near-agreement case, as well as the original fraction-matching
failure. That is more informative than selecting only the largest differences.

Context: [Majumder and Das (2010)](https://arxiv.org/abs/1001.3985) use a local
majority-spin rule and interface-to-interface lengths; our boundary and phase
conventions differ. [Ledesma-Alonso et al.](https://arxiv.org/abs/1712.03183)
already study resolution sensitivity of microstructure descriptors. This
appendix is not a claim that those general ideas are original.
