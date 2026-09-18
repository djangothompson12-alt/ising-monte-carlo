# A bounded test on real Al–Ge segmentation: useful failure, not validation

*AI-assisted exploratory materials-image note, 18 September 2026. The four
public ROI stacks are from [Fell's Mendeley Data release](https://doi.org/10.17632/hj9njz3rxp.1),
CC BY 4.0. The image-processing protocol was fixed after the data and a
metadata/single-plane QA view were inspected, but before the numbers below
were calculated. This is not a blind preregistration, a new experimental
measurement, independent use by the source authors, or a test of Kawasaki
kinetics.*

## Why these images, and what was checked first

Unlike a set of unrelated micrographs, the release contains four segmented
stacks of the **same solid-state-aged Al–Ge specimen** at 15, 105, 195 and
315 minutes. The [associated paper](https://doi.org/10.1016/j.tmater.2023.100009)
already analyses 3D feature evolution and separate hardness results. Our
potential contribution is therefore not to re-report the ageing trend; it
is to test whether an observation choice changes one length measured from
published labels. The initial overview scan was excluded because its voxel
spacing is 260 nm rather than 60 nm.

The four ROI TIFFs are public and 6.0–7.9 MB compressed each. They each have
338 z planes, but their x/y dimensions and TIFF `BoundingBox` coordinates
differ: 15 min is 1071×1050 pixels; 105 min is 1052×1045; 195 min is
1362×1362; 315 min is 1025×1046. All align numerically with a roughly
0.06 µm voxel spacing. A [coordinate-based QA panel](../research/results/alge_time_series_metadata_qa_2026-09-18/common_coordinate_slice_qa.png)
shows obvious movement of the round specimen within the field. Bounding-box
arithmetic alone is **not** independently verified registration of individual
microstructural features. The `BoundingBox` also does not by itself verify
which end of the TIFF page sequence corresponds to low physical z; the
12–18 µm labels below use the declared lower-bound-plus-page-index
convention and need author confirmation before cross-stage anatomy is
interpreted. Besides the documented air=0, Al=2 and Ge=3,
sampled slices contain rare pixels labelled 1 and, at 315 minutes, 4. We
recorded those labels rather than silently calling them Al or Ge. The
[metadata and source-hash record](../research/results/alge_time_series_metadata_qa_2026-09-18/metadata_qa.json)
contains exact dimensions, bounds, sampled counts and source hashes. The QA
panel is an adaptation of Fell's labelled stacks (CC BY 4.0), for inspection
only; it is not a registered time-lapse movie.

## Fixed within-image test and outcome

The [protocol](../research/ALGE_STATIC_OPERATOR_PROTOCOL_2026-09-18.md)
selected 11 physical z planes, 12.0–18.0 µm, for each stage. For each plane
it centred a 300×300-pixel, 18×18-µm square on the Al/Ge specimen centroid.
Within that square it compared the published Ge-vs-Al binary mask at native
60-nm spacing with the *same* mask after the project's 4× block-average and
binary threshold operation, carrying the new 240-nm pixel spacing into the
non-periodic connected-correlation half-height length. This is a **static
length** comparison, not a comparison of fitted growth exponents.

| Stage | Fixed planes with resolved paired length | Predeclared stage result | 4×/native length ratio if all 11 resolve |
|---:|---:|---|---:|
| 15 min | 4/11 | Unresolved: the other seven interior squares contain no Ge, so no binary variance exists | Not reported |
| 105 min | 10/11 | Unresolved: one plane has only 1 Ge pixel in 90,000 and the 4× image becomes one phase | Not reported |
| 195 min | 11/11 | All fixed planes resolved | Median 1.200, range 1.074–1.292 |
| 315 min | 11/11 | All fixed planes resolved | Median 1.082, range 0.990–1.261 |

The 195- and 315-minute numbers are descriptive across **correlated slices
of one specimen**, not confidence intervals from 11 independent samples.
Apparent Ge fraction changed by a median −0.00059 and −0.00048 respectively
after the operator. The selected squares had zero non-2/3 pixels in all 44
planes, so the predeclared worst-case assignment of unknown labels makes no
difference here. All 44 rows—including the eight unresolved outcomes—are in
the [measurement table](../research/results/alge_static_operator_2026-09-18/fixed_plane_measurements.csv),
with [source/protocol hashes and summaries](../research/results/alge_static_operator_2026-09-18/summary.json).
The [all-plane figure](../figures/fig_alge_fixed_plane_audit.png) shows every
planned resolution outcome and the resolved per-plane ratios without
imputing missing values or fitting a time trend.

The positive static length ratios at two late stages cannot be equated with
the **negative shift in a fitted image-growth exponent** in the simulated
time series: these are different quantities and different materials.
The primary lesson is that the supposedly simple length fails to exist in
some reasonable interior regions, and that ROI/phase definitions are part of
the scientific question. Choosing a new crop after seeing these failures
would be a new exploratory analysis, not a rescue of the fixed test.

## Check against the source paper's feature definitions

The [source paper, section 3.5](https://doi.org/10.1016/j.tmater.2023.100009)
does **not** treat all Ge pixels as one population whose correlation length
predicts a property. It separates pre-existing Ge lamellae from smaller
Ge precipitates, then measures lamellar area/shape and precipitate count,
volume and three-dimensional maximum length separately. It also reports a
Fe/Ni-bearing plate-like phase and applies extra ring-artifact correction
to the 195-minute reconstruction. Its starting microstructure came from
casting and includes Al dendrites and eutectic Ge lamellae, rather than the
homogeneous, random binary lattice used at the start of our quench. This
specimen is therefore not a literal two-component, single-mechanism
Kawasaki alloy. Hardness was measured on a separately prepared block,
not by indenting the scanned ROI itself. The paper interprets that hardness
trend in terms of competing recovery, lamellar coarsening and later
precipitation processes; our 2D all-Ge correlation cannot isolate any of
them. Those are reasons **not** to turn the four image stages into a new
growth or strength curve.

This changes the best question for outside review. A microscopist should
first decide which population and decision matter: for example, whether a
resolution check is useful on a lamella-only mask, a precipitate-only mask,
or neither. Reproducing the authors' 3D feature separation is a distinct
study requiring method details and expert review; it is not implied by the
present binary-mask test.

## What this enables—and what it does not

An imaging researcher could give a useful independent critique now:
*Which Al–Ge feature and specimen region would they actually measure to
characterise lamellar coarsening, and how would they handle 3D registration,
air and minor labels?* The present test gives concrete failure cases for that
conversation. It does not yet establish a practically adopted tool, a new
Al–Ge ageing result, a Monte Carlo-to-minutes calibration, a strength
prediction, or an academic/industrial endorsement. The source TIFFs are
kept outside version control; the code and aggregate measurements are
reproducible with attribution and the exact public files.
