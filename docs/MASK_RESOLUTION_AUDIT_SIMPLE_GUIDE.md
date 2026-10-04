# Phase-mask resolution audit: simple reviewer guide

## The question

If the same binary microstructure mask is viewed at a coarser pixel resolution,
does its measured characteristic length remain similar?

## What the tool does

1. The user supplies an already-segmented 2D mask, its physical pixel spacing,
   the phase labels and a fixed rectangular region.
2. The tool measures a correlation half-height length in the horizontal and
   vertical directions without joining opposite image edges.
3. It block-averages the same field to 2x and 4x coarser resolution, applies one
   declared rule to exact 50:50 blocks, and repeats the measurement in physical
   units.
4. It reports phase fraction, both directional lengths, the mean length, change
   from the native result, directional geometry, unresolved crossings and a
   warning when the measured length spans fewer than three coarse pixels.
5. It saves the input, code and output hashes so the calculation can be checked
   and repeated.
6. A materials pilot must declare the alloy or material, processing condition,
   imaging method, section geometry, calibration source and intended use. It can
   classify a change only when the problem owner declares a tolerance in advance.

## What the result means

A large change means that this particular measurement is sensitive to the
tested loss of resolution in the selected field. A small change means only that
it was stable under these two numerical reductions. It does not prove that the
original segmentation was correct or that the field represents the material.

## What it does not do

The tool does not segment raw microscopy images, simulate a real alloy, fit an
ageing exponent, measure bulk chemical composition, predict strength or prove
laboratory usefulness. Numerical downsampling is also not identical to taking
a new image with a lower-resolution microscope. External usefulness would
require a materials researcher to define the relevant phase, field, tolerance
and decision before running a bounded pilot on approved data.

## One-sentence description

I built a reproducible check that shows whether a correlation-based length
measured from a supplied binary microstructure mask changes when the same field
is represented at a coarser pixel resolution, while retaining unresolved and
under-resolved cases instead of hiding them.
