# From simulations to a defensible materials study

Working research plan, 10 September 2026. This is a guide for student review,
not a finished paper or a claim of originality.

## The question worth answering

How reliably can a finite 2D Kawasaki simulation identify a domain-growth law,
and how does the answer depend on composition, observation time, lattice size
and the definition of domain size?

This is narrower and more defensible than claiming to predict an industrial
alloy. It starts with an unresolved observation in the existing work: the
measured Model B growth exponent is below the familiar late-stage 1/3 value.
Finite size is one possible explanation, not the established answer.

Bray's review distinguishes late-time scaling from the earlier evolution:
[Theory of Phase Ordering Kinetics](https://arxiv.org/abs/cond-mat/9501089).
Reproducing known results is useful verification; publication-level novelty
requires a closer literature review and an expert's assessment.

## Evidence, in order

| Question | Data / comparison | What it can support | What it cannot yet support |
|---|---|---|---|
| Are the simulations internally correct? | Conserved Model B magnetisation, energy bookkeeping, seeded reruns, analytic observable tests | Correctness of tested contracts | Every implementation detail is correct |
| Does the apparent exponent drift with time? | Fixed-size trajectories and declared early/late fitting windows | Finite-time sensitivity | An asymptotic exponent from one fit |
| Does lattice size change that drift? | L=32,64,96,128 at matched times, eight replicas per composition/size | Evidence for or against size dependence over this range | That all finite-size effects have vanished |
| Does measurement choice matter? | Four observables on identical saved snapshots; paired replica bootstrap | Observable-dependent effective slopes | Four different universal growth laws |
| Does composition change morphology and kinetics? | c=0.50 versus 0.15, correlations, saved snapshots, existing cluster analysis | Comparisons at the simulated temperatures and times | Composition independence at all late times |

### 1. Finish the existing campaign

Keep the running campaign and engine sources frozen. It targets 64 independent
replicas, 200,000 sweeps each. The [protocol](PROTOCOL.md) fixes the primary
analysis. Save all replicas, including unusual ones. A time checkpoint is not
an independent replica. Report the actual completed inventory, not the target.

### 2. Compare observables on the same data

`metrology.py` defines:

- The original mean directional 0.5 connected-correlation crossing.
- The mean directional integral of the positive correlation lobe, ending at
  its interpolated first zero. No observed zero means unresolved.
- The inverse first moment of the complete Fourier power spectrum, with wave
  number in cycles/site. It returns the wavelength for a pure sinusoidal field.
- The inverse fraction of unlike nearest-neighbour bonds, an interface proxy.

These are explicitly defined measurements, not interchangeable precipitate
radii. The spectrum includes high-frequency power; thermal fluctuations and
sharp interfaces can affect its moment. Interface counts likewise include
small thermal features. Do not smooth, subtract a background or choose a
wave-number cutoff simply because it improves agreement with 1/3. Any such
follow-up needs a physical justification, independent controls and sensitivity
analysis. The analytic normalisation, known wavelength, periodic stripe count
and paired-bootstrap behaviour are tested in `tests/test_metrology.py`.

This secondary analysis was designed after inspecting the pilot. Label it
exploratory. Fits use the same resolved times across observables and replicas,
with paired resampling of entire trajectories. If an observable fails to
resolve, this strict common mask may remove late times; inspect `points` and
`used_t_min/used_t_max` in the CSV. Do not compare the resulting threshold slope
to a primary-analysis slope as if their masks were necessarily identical.

Run after the long campaign finishes, choosing a fresh output directory:

```bash
MPLCONFIGDIR=.mplconfig .venv311/bin/python -m research.compare_estimators research/runs/overnight --output research/runs/overnight/estimator_analysis_v1
```

### 2a. Separate literature benchmark: do not rewrite the main study

The main campaign remains a study of composition, estimator and observation
sensitivity. It should not be retrofitted to match a published exponent. A
separate frozen L=128 reference campaign instead uses the symmetric,
isotropic, `T=0.6 Tc` conditions and the reported 40-replica/4.5-million-sweep
scale of Majumder and Das (2010). Its plan is
`research/plans/majumder_das_2010_l128.json`.

The comparison question is deliberately narrow: after one declared
majority-spin measurement pass, do the resulting chord-length trajectories
show compatible long-time behaviour under this independently implemented
protocol? A disagreement is not evidence that either study is wrong. First
check differences in initial equilibration, update implementation, time
sampling, chord weighting, finite ensemble and fitting/offset conventions.

Report the sequence honestly: a short/pilot ensemble motivated a longer
independent-replica campaign; whole trajectories, rather than time points or
crops, are the independent units. More replicas reduce run-to-run variation,
but cannot remove systematic finite-time, finite-size or measurement-definition
uncertainty.

### 3. Choose the next simulation only after those results

If large lattices agree at matched times but their slopes drift together,
prioritise longer times. If small lattices depart from large ones at the same
time, investigate size dependence and saturation. If observables disagree,
prioritise temperature/measurement controls before another huge size grid.
Both transient and size effects can coexist. A failed candidate z=3 collapse
is a result to report, not a reason to adjust axes until it looks successful.

Use Model A as a non-conserved Metropolis reference. A future matched control
should archive its time-dependent magnetisation and RAW correlation, including
the state after high-temperature equilibration. An assigned initial spin
fraction need not survive that equilibration in Model A; check rather than
equating it with Model B's fixed composition. Do not copy the Model B connected
correlation subtraction into Model A. No new Model A campaign is launched by
this document.

Only then extend anisotropy. Changing Jx/Jy can change both interfacial
anisotropy and Tc; distinguish fixed absolute temperature from fixed T/Tc.
Keep directional measurements instead of hiding anisotropy in an average.
Specify each follow-up before running it and retain the reference model.

## The materials-engineering connection

The phase diagram describes the thermodynamic setting; Kawasaki exchange
imposes solute conservation; domain geometry and interface reduction describe
microstructural evolution. These connections are useful even without a
calibration to nanometres or hours. The existing regular-solution spinodal is
a mean-field construction, not the exact fluctuation-driven 2D phase boundary.

There is a concrete engineering reason to care about coarsening. Jang et al.
model TiC precipitates in high-strength steels because their coarsening during
slow cooling can reduce strength. Their study includes alloy-specific
interfacial energies and diffusion, which this Ising model does not:
[Materials Science and Technology 29 (2013), 1074–1079](https://www.phase-trans.msm.cam.ac.uk/2013/coarsening_MST.pdf).
Use this as motivation and a contrast in modelling scope, not validation of
the present simulation or a claim to predict TiC behaviour.

The most defensible practical extension is a comparison of a clearly matched
observable with a published or collaborator-provided microstructure time
series. Before extracting data, establish image permissions, scale bars,
ageing times, phase identification, segmentation uncertainty, and whether a
2D section of a 3D material can be compared with this genuinely 2D system.
Use independently measured calibration where possible; fitting a length/time
conversion to the same curve is calibration, not a held-out prediction.
An expert conversation can decide whether such a dataset is suitable.

Do not claim alloy strength, embrittlement lifetime, industrial deployment or
real ageing-time prediction from these simulations. The Fe–Cr comparison is
qualitative: the cited 35Cr alloy uses weight percent, not model site fraction.
The classical 3D dilute LSW distribution is not an exact 2D cluster benchmark.

## Write the report around results, not features

Working title: **Measuring coarsening in a conserved lattice model: finite-time,
finite-size and observable dependence**.

1. Introduction: why microstructural stability matters; the precise numerical
   question; what the idealised model excludes.
2. Methods: Hamiltonian, Metropolis versus Kawasaki, quench protocol, realised
   composition, random seeds, observables, fit rules and replica uncertainty.
3. Verification: compact evidence for conservation, energy and analytic checks.
4. Results: phase-diagram context; size/time comparisons; paired observables;
   composition and morphology. Put a question and a limitation under each figure.
5. Discussion: distinguish observations from explanations. Compare relevant
   literature without claiming agreement from a similar exponent alone.
6. Limitations and reproducibility: 2D, finite runtime, estimator sensitivity,
   no material calibration, AI assistance, raw-data archive and source hashes.

The full technical report can retain every diagnostic and unsuccessful test.
A shorter paper should make one supported argument, with secondary plots in
supplementary material. Do not insert provisional results into the manuscript
as final findings before reviewing the completed ensemble.

## What the student needs to do

Explain one spin exchange and its energy change by hand; distinguish a
conserved composition from an initial condition; calculate one log–log slope;
explain why the bootstrap samples replicas; and describe one figure without
reading its caption. Record questions and your own interpretations in a dated
notebook. Re-run a small test yourself and document what you changed or checked.

Ask an academic for a narrow critique of the observable and finite-time
interpretation, not an endorsement before they have seen the work. A specific
review plus a documented revision would make the technical account stronger.
The separate tennis experiment is optional and is not a prerequisite for
strengthening this paper.
