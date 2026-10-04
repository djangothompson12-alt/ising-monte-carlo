# Frozen observable comparison for the L=128 reference trajectories

**AI-assisted protocol prepared before inspecting the new chord-fit output, 22 September 2026.**
It remains gated on the student's review of
`reference_benchmark.declaration.draft.json`. It is not a claim of replication.

## Question

On the same 40 completed symmetric Kawasaki trajectories, how much does the
finite-window exponent change when domain length is defined as (a) the native
connected-correlation half-height or (b) a one-pass majority-filtered mean
periodic chord length inspired by Majumder and Das (2010)?

## Frozen choices

- Input: every saved snapshot from all 40 `L=128`, `c=0.5`, `T=0.6Tc`
  trajectories ending at 4.5 million attempted-exchange sweeps.
- Comparator A: mean of the two archived connected-correlation half-height
  crossings on each unfiltered snapshot.
- Comparator B: one simultaneous periodic five-site majority pass, followed by
  the pooled arithmetic mean of every finite same-spin chord along both axes.
- Windows: 1,000–200,000; 1,000–4,500,000; and 200,000–4,500,000 sweeps.
- Fits: direct log(mean length) versus log(time), plus a separately labelled
  sensitivity subtracting the measured checkpoint nearest 20 sweeps. No fitted
  initial-length offset is allowed.
- Uncertainty: 500 paired bootstrap draws resampling whole trajectories. The
  paired observable difference uses the same resampled trajectories and a
  shared resolved-time mask.
- Additional diagnostic: native and post-filter `+1` fractions are retained.

## Interpretation boundary

The comparison may establish measurement sensitivity on this archived cohort.
It cannot identify a uniquely correct domain length, prove asymptotic one-third
growth, reproduce a multi-size finite-size collapse, map sweeps to alloy time,
or validate a real alloy. The majority operator is paper-inspired because the
paper does not fully specify pass count and update ordering. Results will not
be selected, discarded or retuned according to proximity to one third.
