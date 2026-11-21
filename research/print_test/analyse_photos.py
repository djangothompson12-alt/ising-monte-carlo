"""Measure growth exponents from photographs of the printed tiles.

Each photo is segmented blind (Otsu threshold on the lattice region only, no
knowledge of the true phase fraction), its correlation length is measured with
the same estimator as the simulations, and the six tiles of one composition
photographed under one setting are fitted as a growth series. The result is
compared with the exact exponent of the printed snapshots in truth.json.

Manifest CSV columns: file,tile_id,setting
  setting: any label for one camera distance/zoom, e.g. "d1.5m".
Photograph square-on, on a dark background, with even lighting.

Usage:
  python -m research.print_test.analyse_photos --photos DIR --manifest M.csv \
      --truth output/print_test/truth.json --out output/print_test/results
  python -m research.print_test.analyse_photos --self-check \
      --truth output/print_test/truth.json
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.filters import threshold_otsu

from research.imaging import image_length

LATTICE = 128


def _geometry(truth):
    margin = truth['margin_cells']
    f0 = truth['frame_cells'][0]
    size = LATTICE + 2 * margin
    return dict(frame_span=size - 2 * f0, lattice_start=margin - f0,
                lattice_end=margin - f0 + LATTICE)


def load_gray(path):
    img = np.asarray(Image.open(path).convert('L'), dtype=float) / 255.0
    return img


def measure(gray, truth):
    """Locate the tile frame, crop the lattice, segment blind, measure."""
    g = _geometry(truth)
    bright = gray > threshold_otsu(gray)
    labels, n = ndimage.label(bright)
    if n == 0:
        raise ValueError('No bright region found; is the background dark?')
    # The frame encloses everything else, so its bounding box is the largest,
    # even when a percolating lattice cluster has more bright pixels.
    boxes = ndimage.find_objects(labels)
    frame = max(boxes, key=lambda b: (b[0].stop - b[0].start)
                * (b[1].stop - b[1].start))
    top, bottom = frame[0].start, frame[0].stop
    left, right = frame[1].start, frame[1].stop
    ppc_y = (bottom - top) / g['frame_span']
    ppc_x = (right - left) / g['frame_span']
    ppc = (ppc_x + ppc_y) / 2
    r0 = int(np.ceil(top + g['lattice_start'] * ppc_y))
    r1 = int(np.floor(top + g['lattice_end'] * ppc_y))
    c0 = int(np.ceil(left + g['lattice_start'] * ppc_x))
    c1 = int(np.floor(left + g['lattice_end'] * ppc_x))
    crop = gray[r0:r1, c0:c1]
    if min(crop.shape) < 8:
        raise ValueError('Lattice region is under 8 pixels across.')
    field = np.where(crop > threshold_otsu(crop), 1.0, -1.0)
    m = image_length(field)
    return dict(px_per_site=ppc, aspect=ppc_x / ppc_y,
                length_px=m['length'], length_sites=m['length'] / ppc,
                resolved=m['resolved'],
                white_fraction=float((field > 0).mean()),
                crop_px=list(crop.shape))


def analyse(rows, truth):
    tiles = {t['id']: (comp, t) for comp, e in truth['compositions'].items()
             for t in e['tiles']}
    records = []
    for row in rows:
        comp, tile = tiles[row['tile_id']]
        rec = dict(row, composition=comp, t=tile['t'],
                   true_length_sites=tile['native_length_sites'],
                   true_white_fraction=tile['white_fraction'])
        rec.update(measure(row['gray'], truth))
        rec['px_per_domain'] = tile['native_length_sites'] * rec['px_per_site']
        rec.pop('gray')
        records.append(rec)
    fits = []
    for comp, entry in truth['compositions'].items():
        for setting in sorted({r['setting'] for r in records
                               if r['composition'] == comp}):
            group = [r for r in records
                     if r['composition'] == comp and r['setting'] == setting]
            ok = [r for r in group if r['resolved']
                  and np.isfinite(r['length_sites'])]
            fit = dict(composition=comp, setting=setting, n_tiles=len(group),
                       n_resolved=len(ok),
                       median_px_per_domain=float(np.median(
                           [r['px_per_domain'] for r in group])),
                       min_px_per_domain=float(min(
                           r['px_per_domain'] for r in group)),
                       true_exponent=entry['native_exponent'])
            if len(ok) == len(entry['tiles']):
                x = np.log([r['t'] for r in ok])
                y = np.log([r['length_sites'] for r in ok])
                fit['photo_exponent'] = float(np.polyfit(x, y, 1)[0])
                fit['error'] = fit['photo_exponent'] - fit['true_exponent']
            else:
                fit['photo_exponent'] = fit['error'] = None
            fits.append(fit)
    return records, fits


def render(tile_white, px_per_site, blur_px=0.6, noise=0.02, seed=0):
    """Synthetic photo of a tile, for checking this pipeline only."""
    rng = np.random.default_rng(seed)
    over = 16
    hi = np.kron(np.where(tile_white, 0.85, 0.10), np.ones((over, over)))
    n = tile_white.shape[0]
    side = max(int(round(n * px_per_site)), 8)
    img = np.asarray(Image.fromarray((hi * 255).astype(np.uint8)).resize(
        (side, side), Image.BOX), dtype=float) / 255.0
    pad = max(side // 6, 4)
    canvas = np.full((side + 2 * pad, side + 2 * pad), 0.05)
    canvas[pad:pad + side, pad:pad + side] = img
    if blur_px:
        canvas = ndimage.gaussian_filter(canvas, blur_px)
    return np.clip(canvas + rng.normal(0, noise, canvas.shape), 0, 1)


def self_check(truth_path):
    from research.print_test.make_tiles import tile_layout
    truth = json.loads(Path(truth_path).read_text())
    out_dir = Path(truth_path).parent
    rows = []
    for comp, entry in truth['compositions'].items():
        for tile in entry['tiles']:
            snap = np.load(out_dir / f"{tile['id']}_snapshot.npy")
            white = tile_layout(snap)
            for ppc in (4.0, 2.0, 1.0, 0.6, 0.4):
                rows.append(dict(file='synthetic', tile_id=tile['id'],
                                 setting=f'{ppc:.1f}px_per_site',
                                 gray=render(white, ppc)))
    _, fits = analyse(rows, truth)
    for f in fits:
        err = 'unresolved' if f['error'] is None else f"{f['error']:+.4f}"
        print(f"{f['composition']} {f['setting']:>15}  median px/domain "
              f"{f['median_px_per_domain']:5.2f}  error {err}")
    return fits


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--truth', type=Path, required=True)
    p.add_argument('--photos', type=Path)
    p.add_argument('--manifest', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--self-check', action='store_true')
    a = p.parse_args()
    if a.self_check:
        self_check(a.truth)
        return
    truth = json.loads(a.truth.read_text())
    with open(a.manifest, newline='') as f:
        rows = [dict(r, gray=load_gray(a.photos / r['file']))
                for r in csv.DictReader(f)]
    records, fits = analyse(rows, truth)
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / 'photos.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    (a.out / 'fits.json').write_text(json.dumps(fits, indent=2))
    for r in records:
        if abs(r['aspect'] - 1) > 0.03:
            print(f"warning: {r['file']} frame aspect {r['aspect']:.3f}; "
                  'retake square-on')
    for f in fits:
        err = 'unresolved' if f['error'] is None else f"{f['error']:+.4f}"
        print(f"{f['composition']} {f['setting']:>12}  median px/domain "
              f"{f['median_px_per_domain']:5.2f}  error {err}")


if __name__ == '__main__':
    main()
