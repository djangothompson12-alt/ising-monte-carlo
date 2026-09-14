# Start here

For a quick, honest account, read [progress and limits](PROGRESS_AND_LIMITS.md).
Then read [the completed long-run results](OVERNIGHT_RESULTS.md) and
[the observation study](MEASUREMENT_STUDY_RESULTS.md). The raw trajectories
for those studies are described in [the data guide](../research/DATA_README.md).
Experimental slices have been inspected for feasibility, not validated as a
quantitative coarsening benchmark.

The priority is to understand the replicated Kawasaki study well enough to
explain its figures and limits. [The research design](../research/STUDY_DESIGN.md)
connects data to questions and report figures. The tennis-string study is a
separate, optional mechanics experiment; it does not validate Ising.

## For a technical review

1. Read [the research design](../research/STUDY_DESIGN.md) and the
   [pilot estimator results](PILOT_ESTIMATOR_RESULTS.md).
   Write down what a change in measured exponent does and does not establish.
2. Read [the writing guide](../manuscript/WRITING_GUIDE.md) and write the short
   explanation yourself. Mark what you do not yet understand.
3. Open [the review brief](review_brief.html). Check every sentence against what
   has actually been done and understood. It is a draft, not a sent message.
4. Ask a reviewer for one narrow technical criticism, not general endorsement.

## Completed computation

The 24-replica pilot and all 64 replicas of the 200,000-sweep campaign are
complete. Read [the overnight results](OVERNIGHT_RESULTS.md) for the primary
analysis, its source/input provenance and the small-lattice missing-data caveat.
A separate 0.6Tc, 50:50, L=128 literature comparison has 7 of 40 planned
runs complete and is paused at a compute-budget boundary; it is not a result
yet. A longer 0.65Tc size/time extension has a plan but has not begun. See
[the campaign protocol](../research/PROTOCOL.md) for analysis commands.

The pilot already shows strong fitting-window sensitivity at c=0.5: about
0.17 using the wide window and 0.24 when fitting from 1,000 sweeps, with similar
values across L=32,64,96. This is preliminary evidence, not proof of the
asymptotic exponent or a finite-size explanation.

## What the software can measure

| Tool | Output | What is needed for a physical test |
|---|---|---|
| Ising engine / paused dashboard export | Raw directional length in sites, heat, lattice, parameters | Comparable observable and justified material/time mapping; not supplied by changing axis labels |
| Campaign analyser | Replica growth curves, effective exponents, candidate scaling plots | Independent review of estimator and fitting windows |
| Tennis string tool | Predicted frequency (Hz), conditional force estimate (N), validation residuals | Known load, loaded density and span, checked fundamental, real recordings |

No code here predicts racket performance or an industrial alloy's ageing time.
See [physical measurements and calibration limits](PHYSICAL_MEASUREMENTS.md)
for what would be needed to make those further claims.
There is no need to buy tennis-testing equipment to progress the Kawasaki
paper. Prioritise the numerical evidence and understanding it well enough to
discuss it with a materials researcher.

## Before publication or claims of validation

The source code and selected completed simulation archives are public working
materials, not a peer-reviewed release. A reply, introduction, submission or
DOI is not endorsement. Ask permission before naming or quoting a reviewer.
Keep specific criticism and any resulting revisions as part of the record.
