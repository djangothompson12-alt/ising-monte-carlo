# A real-data companion to the Kawasaki study

This is a local research prototype, not an alloy-property predictor or a
validated laboratory product. It asks a narrower question that follows from
the simulation study: **how much does a microstructure measurement change
when the field of view or voxel resolution changes?**

The simulation engine remains 2D. This companion measures supplied **3D
experimental phase masks**. It does not turn Kawasaki sweeps into hours of
alloy ageing, and agreement between image lengths would not validate a
kinetic model of that alloy.

## What it does

- Reads a user-declared region of a 3D NPY array or multipage TIFF.
- Requires phase labels, voxel spacing, source rights and the reason for the
  region selection. Any undeclared label makes the full box ineligible.
- Compares three concentric fields and native, twofold and fourfold voxel
  spacing. Block averaging keeps partial-volume values; a separate binary
  threshold step reveals the additional effect of segmentation.
- Measures directional connected-correlation half-height lengths, a
  positive-lobe integral, and complete binary chords. These quantities have
  different definitions; none is automatically a particle radius.
- Excludes boundary-crossing chords and reports the number excluded. It
  never joins opposite faces as a periodic simulation would.
- Exports measurements, hashes and a portable HTML report with a volume
  selector. Missing crossings stay missing rather than becoming zero.

The three-axis mean is reported only when all three directions resolve.
Field sizes are fractions **per axis**, not volume fractions. The smallest
field has one eighth of the full volume. Local phase volume fraction is not
the chemical composition of the alloy.

## Public-data example

Source: Jonas Fell (2023), *Microstructural evolution of an Al-Ge alloy
revealed by nano-CT*, Mendeley Data v1,
[doi:10.17632/hj9njz3rxp.1](https://data.mendeley.com/datasets/hj9njz3rxp/1),
CC BY 4.0. The depositor supplies segmented Al/Ge stacks after annealing at
375 °C, with 60 nm voxels. This audit crops, averages and resegments those
labels; it does not independently verify the original segmentation.

The [declared protocol](../research/VOLUME_AUDIT_PROTOCOL_2026-09-19.md)
fixes all four regions before calculating their length measurements.
This is an exploratory extension on previously inspected source data, not
a preregistered or blind validation experiment. The time labels identify
scans; no cross-time growth exponent is inferred.

To reproduce after obtaining the four ROI stacks from the source:

```bash
python -m research.prepare_alge_volume_audit \
  --source research/runs/alge_time_series_source_v1 \
  --plan output/alge_volume_plan.json
python -m research.volume_audit output/alge_volume_plan.json \
  --output output/alge_volume_report
```

Use new output names: the tool refuses to overwrite an earlier audit.
Open `report.html` in the generated directory. The JSON plan also serves as
an example for other masks. Specify z/y/x bounds as start-inclusive,
stop-exclusive; spacings are in that same order. Each box side must be at
least 32 voxels and divisible by 16, with at most 256³ voxels in total.
Boxes must contain only the two declared labels, not air, missing pixels or
other phases. Do not change a failed region to obtain a nicer result.

## What would make it useful outside this project?

Ask one researcher for a bounded pilot: one measurement question, permission
to use a small number of phase masks, and their definition of an acceptable
measurement change. Run the audit, show the failures as well as the resolved
results, and ask whether it changed any choice of field size, image
resolution or analysis method. Record their criticism and any revision.

That would test usefulness. A download, a courtesy reply or an attractive
report is not evidence of adoption or endorsement. Cropping one specimen
does not supply independent specimen replicates or confidence intervals.
The current prototype measures sensitivity relative to an input mask; it
does not establish ground-truth segmentation, a representative volume size,
or a universally optimal imaging method.

## Ownership and next student task

The new implementation, tests and protocol draft were AI-assisted. Before
presenting it, the student should explain one comparison unaided: why block
averaging preserves the mean but binary thresholding can change it, and why
a smaller field is a different test from coarser voxels. Then choose a claim
supported by the output and write its limitation in their own words.
