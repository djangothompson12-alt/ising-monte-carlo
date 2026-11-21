# Printed-tile camera test

My resolution results so far use a mathematical camera: block averaging,
added blur, and thresholding at the known phase fraction. This test swaps in
a real one. Simulation snapshots with a known growth exponent are 3D printed
at 1 mm per lattice site, photographed at increasing distance, segmented
blind, and refitted. Because the printed pattern is exactly known, any change
in the fitted exponent comes from the imaging chain: lens, sensor, the phone's
own processing, and blind thresholding.

It is a physical imaging test with a known answer, not an alloy experiment.
A phone photographing plastic is not an SEM imaging γ′.

## The tiles

Twelve tiles: six times (646 to 21,336 sweeps) from one 0.65 Tc trajectory at
each composition, 50:50 and 15:85. Each tile is 144 × 144 mm: the 128 × 128
lattice, a white frame used to find the tile and measure scale, and a small
white square marking the top-left corner. White raised squares are the +1
sites.

| Composition | Native exponent of the printed snapshots | Block-average model, 2× | Block-average model, 4× |
|---|---:|---:|---:|
| 50:50 | 0.239 | 0.232 | 0.181 |
| 15:85 | 0.231 | 0.214 | 0.143 |

Exact values are in `truth.json` next to the STL files.

Generate them with:

```bash
python -m research.print_test.make_tiles --out output/print_test
```

## Printing

- Use matte black and matte white PLA if you have them. Shiny filament glares.
- 0.2 mm layers, 100% infill is not needed; 3 walls and solid top/bottom are fine.
- **Single-colour printer:** load `<tile>_combined.stl`. Print in black and
  insert a filament change (colour change / pause) at the first layer above
  1.2 mm. Swap to white and resume. The base is 1.2 mm; the white squares
  rise 0.6 mm above it.
- **Multi-material printer:** load `base.stl` and `<tile>_white.stl` together
  as one object with two parts. Assign black to the base and white to the
  squares.
- The tile needs a 144 mm bed. Write the tile ID on the underside as soon as
  each print finishes. They are easy to mix up.
- Check every print against `<tile>_snapshot.npy` before photographing (a
  close-up photo analysed at high resolution should give the native length).

## Photographing

- Lay the tile on a dark, non-shiny background. The frame must be the
  brightest thing in the shot.
- Use even, diffuse light from above (overcast daylight, or a lamp bounced
  off the ceiling). Side light makes the raised squares cast shadows.
- Shoot square-on. The analysis warns if the frame's aspect ratio is more
  than 3% off.
- Use the phone's main camera at 1×, 12 MP, no zoom, no portrait mode.
  Record the phone model and settings.
- Use the same distance for all six tiles of a composition, then step back.
  The script measures pixels per site from the frame, so distances need not be
  exact. For a typical 12 MP phone:

| Target pixels per site | Approximate distance |
|---:|---:|
| 4 | 0.7 m |
| 2 | 1.4 m |
| 1 | 2.9 m |
| 0.6 | 4.8 m |
| 0.4 | 7 m |

- List every photo in a CSV with columns `file,tile_id,setting`, where setting
  names the distance (for example `d2.9m`). Keep every photo, including bad
  ones.

## Analysis

```bash
python -m research.print_test.analyse_photos --photos PHOTO_DIR \
    --manifest manifest.csv --truth output/print_test/truth.json \
    --out output/print_test/results
```

For each composition and distance it reports the median pixels per domain,
the fitted exponent from the photos and its error against the printed truth.

`--self-check` runs the same pipeline on synthetic renders of the tiles. On
the current tiles it gives errors within 0.003 at 1.9 or more pixels per
domain, and −0.03 to −0.06 at 0.8 to 1.5 pixels per domain. That checks the
code only; it says nothing about a real camera.

Rules for passing and failing go in `PROTOCOL.md` and must be committed before
any photo is taken.
