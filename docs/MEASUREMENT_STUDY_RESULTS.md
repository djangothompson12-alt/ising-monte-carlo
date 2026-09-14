# Measurement study: results and claim boundaries

10 September 2026. Computational work executed with AI assistance; student
verification and external technical review are still required. This is an
evidence note to write from, not a paper written in the student's voice.

## What is complete

- Four-observable reanalysis of all 64 long-run Kawasaki replicas.
- Finite-window, non-periodic image measurement, independently checked against
  explicit pair products; controlled crops, blur, binning and segmentation.
- The observation benchmark on all 64 long-run replicas and eight new seeded
  replicas (four per composition, L=128, 20,000 sweeps). The fresh seeds do not
  overlap the original 64. No engine dynamics or Model A correlations changed.
- Original experimental TIFF slices at five annealing stages, retrieved under
  CC-BY-4.0, with source metadata, member CRC checks and local SHA-256 hashes.
  Their role is **feasibility and data-quality assessment**, not validation.

## Results worth writing about

### 1. Estimator disagreement persists in the long runs

At c=.50, L=128, nominal 1,000–200,000 sweeps, the original correlation
threshold gives 0.258, the positive-lobe integral 0.251, the full-spectrum
moment 0.167 and the inverse-interface proxy 0.204. The spectral-minus-threshold
difference is −0.091 [−0.094, −0.089], using a paired replica bootstrap.
These are defined observables, not four measurements of an established true
particle radius. Different weighting of microscopic structure is a possible
explanation, not a mechanism uniquely established by this comparison.

Source: `research/runs/overnight/estimator_analysis_v1/paired_fits.csv`.

### 2. Observation operators change the apparent exponent without changing dynamics

The primary observation window is nominally 1,000–20,000 sweeps. Its actual
retained points are 1,069–19,557 in the original ensemble and 1,224–20,000 in
the new ensemble. The sampling grids differ; each reported difference is
paired within its own ensemble. Inter-ensemble agreement is a repeatability
check, not a perfectly matched-time statistical comparison.

| Composition | Treatment | Original ensemble delta [95% interval], n=8 | Fresh ensemble delta [95% interval], n=4 |
|---|---|---|---|
| .50 | 4x block averaging + threshold | −0.056 [−0.060, −0.052] | −0.057 [−0.059, −0.056] |
| .15 | 4x block averaging + threshold | −0.072 [−0.077, −0.068] | −0.073 [−0.088, −0.060] |
| .50 | sigma=2 blur + threshold | −0.057 [−0.059, −0.054] | −0.055 [−0.058, −0.052] |
| .15 | sigma=2 blur + threshold | −0.001 [−0.010, 0.007] | −0.003 [−0.027, 0.018] |

Delta means treatment exponent minus the full finite-window image reference.
Pixel spacing is accounted for after reduction. A time-dependent length
distortion remains; it cannot be removed by merely relabelling the pixel size.
This supports a bounded practical conclusion: report sensitivity to the
observation/segmentation pipeline before attributing a fitted slope entirely
to physical kinetics. It does NOT establish a microscope-independent correction.

The operator is **binning plus thresholding**, not resolution alone. Exact
threshold ties are assigned to +1; this changes apparent phase fraction,
which is retained in the raw measurement table. Gaussian blur uses reflecting
image boundaries and is not an experimentally calibrated point-spread function.

### 3. Small-field behaviour is less robust than the binning result

For c=.15, the 32-site crop's primary-window delta is −0.004 [−0.028, 0.019]
in the original ensemble but −0.046 [−0.062, −0.034] in the fresh ensemble.
For c=.50 it is −0.002 [−0.018, 0.018] versus +0.016 [−0.002, 0.038].
This is not a stable universal crop correction. Retain both ensembles.

At the final long-run time, the c=.15, 32-site crop gives about 77% of the
full-image reference length. A true L=32 system also shows late flattening.
The descriptive box-versus-window plot illustrates that observation effects
can resemble physical size limitation; it does not prove those effects have
identical causes. Crops use a locally estimated composition and omit crossing
edge pairs, so their effect includes covariance-estimation changes.

Sources: `research/runs/overnight/imaging_v1/` and
`research/runs/imaging_validation/imaging_v1/`, each containing REPORT.md,
paired_fits.csv, observations.csv, figures and a source/input hash manifest.

## Actual experimental data: an important limitation was found

Source: Jonas Fell, *X-ray computed tomography dataset: 3D microstructural
evolution of an annealed Al alloy imaged using SEM-based nano-CT*,
[Zenodo 14923133](https://doi.org/10.5281/zenodo.14923133), CC-BY-4.0.
Associated paper: [Three-dimensional imaging of microstructural evolution in
SEM-based nano-CT](https://doi.org/10.1016/j.tmater.2023.100009).

Five central slices were selected mechanically before viewing. They are not
registered sections of the same plane and are not five independent specimens.
The sample outline and external background are substantial, so whole-frame
thresholding would mix specimen geometry with internal phase structure.

The 195-minute slice differs sharply from the others: 1362x1362 rather than
1280x1280, strongly negative background intensities, and no voxel size recovered
by the current header parser. Other retrieved headers give about
0.06012–0.06025 micrometres per voxel. The source paper also reports an imaging
stage upgrade during the sequence. These observations prevent treating one
unchanged intensity threshold or the same pixel coordinates as directly
comparable measurements across stages.

Accordingly, **no experimental growth exponent or validated phase size is
reported**. Next requirements are author/expert guidance on intensity/scaling
metadata, a specimen-interior ROI and phase segmentation, and registration or
a justified unregistered sampling design. The usable result now is a documented
data-quality audit. The raw slices were not edited. Full archive MD5 checks
were not performed because only selected members were fetched; ZIP-member CRC
and saved-file SHA-256 were checked instead.

Files: `research/runs/alge_feasibility/manifest.json`, the five original TIFFs,
and `qa/experimental_feasibility.png` / `qa/QA.json`.

## Established literature versus possible contribution

[Majumder & Das (2011)](https://arxiv.org/abs/1101.4524) already address noise,
length definitions, early-time behaviour and finite-size interpretation. Their
processing and definitions differ from ours; a faithful reproduction remains
an outstanding benchmark, not a result delivered here. Finding a low exponent
or changing it through image processing is not itself a new physical discovery.

The present contribution is a reproducible controlled-observation case study
with independent seeded repetition and an experimental feasibility audit.
Its originality and usefulness are not established by this document. A reviewer
should judge whether to extend it, narrow it to a technical report, or develop
it toward a methods paper. Do not describe the tool as lab-adopted, endorsed,
experimentally validated or predictive of alloy strength.

## Statistical limitations

Eight original and four fresh replicas per composition are small ensembles.
Intervals use 500 whole-replica resamples and fixed pair-specific resolved-time
masks. They omit mask-selection and model uncertainty. Four corner crops are
averaged within each replica, never counted as four more independent runs.
All crop directions must resolve; failures are retained, not replaced.
Many correlated comparisons are displayed; no family-wise significance claim
or discovery-screening p-value is made. Equal/unequal slopes do not prove
asymptotic universality or its breakdown. No trained reliability score or
validated universal safe-resolution threshold has been produced.
