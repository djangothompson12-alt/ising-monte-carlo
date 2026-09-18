# Public time-series data: a possible measurement audit, not alloy validation

*AI-assisted source and feasibility note begun 17 September 2026. The Al–Cu
candidate below has not been analysed locally. The Al–Ge follow-up at the end
was inspected and given a bounded image-operator test on 18 September. None
of this is a claim of external use, endorsement, or an experimental test of
Kawasaki kinetics.*

## Candidate worth checking

The [Materials Data Facility Al–Cu 4D tomography release](https://acdc.alcf.anl.gov/mdf/detail/pub_7_gibbs_segmentation_v1.2/) (DOI [10.18126/M2CC73](https://doi.org/10.18126/M2CC73)) describes an *in situ*, time-resolved, isothermal coarsening experiment. It includes reconstructed and segmented 3D scans plus processed interface data. The source says scans were taken every 50–250 seconds over 2–15 hours. Its [segmentation methods paper](https://doi.org/10.1186/2193-9772-3-6) explains registration, segmentation and why small boundary errors matter to curvature/velocity measurements.

This is a stronger **data-quality candidate** than treating unrelated slices as a growth series: the same specimen evolves over measured time, and segmentation and physical voxel metadata may be available. But the experiment is a **liquid–solid Al–Cu mixture near the eutectic**, not solid-state spinodal decomposition of substitutional atoms. It has three image regions including sample holder and a 3D dendritic geometry. A 2D Kawasaki curve must **not** be fitted to its minutes or micrometres as if it were the same mechanism. A single 2D slice can also change as a 3D feature moves through the plane; that is a sampling limitation, not necessarily in-plane growth.

There is particularly relevant prior art: [Sun et al., *Acta Materialia* 132, 374–388 (2017)](https://doi.org/10.1016/j.actamat.2017.04.054) used two-point spatial correlations on time-resolved Al–Cu tomography and extracted characteristic dendrite lengths that they compared with direct measurements. This project cannot claim to introduce correlation analysis of experimental coarsening images. A possible remaining question is narrower: **how sensitive is one predeclared length or fitted growth rate to the observation choices on a genuinely registered experimental series, with published segmentation as a reference?** It would need to add something beyond that paper, and a domain expert may judge the answer already known.

## Read-only gate before coding or fitting

1. Confirm that the downloadable collection is accessible without a collaborator's account, identify the exact dataset/subseries, usage licence and citation requirements, and estimate volume size. “Get the Data” currently points through Globus; this note has not established open unauthenticated transfer or reuse rights for derived images.
2. Inspect *one* small, documented subset: specimen ID, timestamp, common coordinate frame/registration, voxel size, phase meanings, segmentation provenance and missing scans. Keep source-provided masks separate from any threshold derived from raw intensities.
3. Have a materials imaging researcher identify the decision-relevant outcome: phase fraction, specific arm spacing, interface density, or something else. A half-height correlation length is not automatically the right feature for a dendritic image.
4. Only then predeclare a 2D versus 3D analysis, region-of-interest rule, resolution perturbations, independent experimental-unit definition, failure thresholds and comparison to published direct measurements. Avoid treating every slice or time frame as an independent sample.
5. Publish a positive *or negative* measurement audit with raw-data citation and exact exclusions. Do not use the data to claim a Kawasaki-to-alloy timescale calibration, predictive strength, or a new growth law.

Until those gates pass, the existing [42-image steel test](EXTERNAL_USE_DECISION_2026-09-17.md) remains a useful **failure case**, not a deployment. A genuine outside use occurs only if a researcher chooses to try a bounded workflow on an approved question and independently reports whether it helped.

## 18 September follow-up: a labelled Al–Ge alternative

The [Mendeley Data release by Jonas Fell](https://doi.org/10.17632/hj9njz3rxp.1)
is a more promising **metadata** lead than using raw, unregistered central
slices alone. Its public record states CC BY 4.0, a 375 °C anneal of the same
Al–Ge specimen, segmented Al/Ge values 2/3 (air 0), an approximately 60 µm
high-resolution ROI and 60 nm voxels. It distinguishes the initial **overview**
scan (260 nm voxels) from four later ROI stacks. The associated
[primary methods paper](https://doi.org/10.1016/j.tmater.2023.100009)
documents heat-treatment stages, a change of rotation stage between scans,
an extra ring-artifact correction at 195 minutes, and the authors' own 3D
segmentation and feature measurements. They already connect those features
with separate hardness measurements. Repeating their published trend would
not be a novel materials result.
The paper's Fig. 5 labels four corresponding reconstructed cross-sections
at **15, 105, 195 and 315 minutes**. Its heat-treatment table also lists
0, 45 and 460 minutes. The public data page subsequently exposed the four
ROI filenames directly: `ROI_15min.tif`, `ROI_105min.tif`,
`ROI_195min.tif` and `ROI_315min.tif`.

Unlike the Al–Cu candidate above, this Al–Ge time series is **solid-state
annealing** of a cast alloy below its melting point, not observation of a
solid–liquid interface. That makes its processing context more relevant to
materials ageing. The paper describes Ge-lamella coarsening, precipitation,
recovery and hardness changes—not an initially homogeneous binary solution
following this lattice's simple quench, and not an exact kinetic or
thermodynamic match. The paper also identifies a plate-like Fe/Ni-containing
third phase in some views, whereas the public dataset description names
Al/Ge/air labels. Its treatment in each segmented volume needs checking.
Those differences still rule out mapping its minutes
or nanometres directly onto Monte Carlo sweeps or sites.

At the source-scout stage this was **not yet an analysed series**. The four
files were later downloaded through the public individual-file links and
inspected. Registration transforms and true same-feature correspondence
still need verification by an author or a materials-imaging expert. The
initial 260 nm overview must not be mixed into a 60 nm time series
as if it were the same observation scale. Even four high-resolution stages
from one specimen would support at most a carefully bounded measurement-
sensitivity audit, not independent-sample inference or a reliable new ageing
exponent. In fact, the source paper has already analysed the 3D feature
evolution; the only plausible additional question is whether this project's
**predeclared observation choices** materially alter a specific reported
measurement. A materials imaging researcher should decide if that question
is useful before a more interpretive analysis.

## 18 September file and bounded-test update

The public page lists the four ROI TIFFs at 6.56, 7.91, 7.17 and 5.99 MB
respectively; all were retrieved without logging in. Local SHA-256 hashes,
dimensions, bounding boxes and sample label counts are in the
[metadata QA](../research/results/alge_time_series_metadata_qa_2026-09-18/metadata_qa.json).
The four stacks each have 338 z planes, but **different x/y image extents**.
A common-coordinate 2D inspection shows specimen movement, not proven
same-feature registration. Rare label values 1 and 4 appear in sampled
slices alongside documented 0/2/3. No raw TIFF is committed.

A [fixed, exploratory within-image audit](ALGE_REAL_IMAGE_AUDIT_2026-09-18.md)
then tried the simulation's 4× observation step on 11 central specimen
squares per stage. It failed its full-stage resolution rule at 15 and 105
minutes; at 195 and 315 minutes all 11 paired lengths resolved and the
descriptive median 4×/native ratios were 1.200 and 1.082. This is a
**static measurement sensitivity** with one specimen and correlated planes,
not an ageing exponent or a direct test of the Kawasaki trajectory. It
provides concrete ROI and feature-definition questions for a microscopist,
not a claim of adoption by the dataset authors.

## Why this route is more honest than “the model predicts an alloy”

The transferable element of this project is **measurement discipline**: conserved-morphology toy data expose how observation and fitting choices alter an inferred length. The external data would challenge whether a carefully scoped part of that audit is useful on actual images. A mismatch is informative; forcing physical agreement is not. For Oxford Materials, this grounds the discussion in microstructure characterisation and processing history. For US applications, the strongest evidence would be a documented problem, reproducible attempt, independent criticism and revision—not the name of the institution or company on the email.
