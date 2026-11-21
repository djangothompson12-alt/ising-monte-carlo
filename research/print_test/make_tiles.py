"""Turn archived Kawasaki snapshots into 3D-printable two-colour tiles.

Each tile is a 1 mm-per-site copy of one 128x128 snapshot, framed for photo
alignment. +1 sites are raised and printed in white; everything else is the
black base. Outputs per tile: a combined STL (print black, pause at the base
height, swap to white) and a white-only STL to pair with base.stl on
multi-material printers. Also writes truth.json: the exact native lengths and
exponent of the printed snapshots, plus the block-average camera model's
prediction, so photographs can be scored against a known answer.

Usage: python -m research.print_test.make_tiles --out output/print_test
"""
import argparse
import json
import struct
from pathlib import Path

import numpy as np

from research.imaging import image_length, observe

RUN_DIR = Path('research/runs/main_065_multisize_v1')
SOURCES = {'5050': 'c0_L128_rep000.npz', '1585': 'c1_L128_rep000.npz'}
TIMES = (646, 1300, 2617, 5266, 10600, 21336)

SITE_MM = 1.0
MARGIN = 8            # cells of border around the lattice
FRAME = (1, 4)        # frame ring occupies cells [1, 4) from the tile edge
MARKER = (5, 7)       # orientation square, top-left corner
BASE_MM = 1.2
RAISE_MM = 0.6


def tile_layout(snapshot):
    """Boolean white-cell map for the whole tile, row 0 at the top."""
    n = snapshot.shape[0]
    size = n + 2 * MARGIN
    white = np.zeros((size, size), bool)
    a, b = FRAME
    white[a:size - a, a:size - a] = True
    white[b:size - b, b:size - b] = False
    m0, m1 = MARKER
    white[m0:m1, m0:m1] = True
    white[MARGIN:MARGIN + n, MARGIN:MARGIN + n] = snapshot > 0
    return white


def _quad(tris, a, b, c, d):
    """Append a quad a-b-c-d (counter-clockwise seen from outside)."""
    tris.append((a, b, c))
    tris.append((a, c, d))


def heightmap_mesh(height, cell=SITE_MM):
    """Watertight surface of a grid of square columns standing on z=0.

    height[r, c] is the column height; row 0 is placed at the largest y so the
    printed tile reads the same way as the image.
    """
    rows, cols = height.shape
    tris = []
    levels = np.unique(np.concatenate([[0.0], height.ravel()]))

    def wall(p0, p1, lo, hi):
        # Split at every height level so neighbouring walls share vertices.
        cuts = [lo] + [z for z in levels if lo < z < hi] + [hi]
        (xa, ya), (xb, yb) = p0, p1
        for z0, z1 in zip(cuts[:-1], cuts[1:]):
            _quad(tris, (xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1))

    def xy(r, c):
        return c * cell, (rows - r) * cell

    for r in range(rows):
        for c in range(cols):
            h = height[r, c]
            if h <= 0:
                continue
            x0, y1 = xy(r, c)
            x1, y0 = xy(r + 1, c + 1)
            _quad(tris, (x0, y0, h), (x1, y0, h), (x1, y1, h), (x0, y1, h))
            _quad(tris, (x0, y0, 0), (x0, y1, 0), (x1, y1, 0), (x1, y0, 0))
            # East wall: to the neighbour at c+1, or the outer edge.
            hn = height[r, c + 1] if c + 1 < cols else 0.0
            if h > hn:
                wall((x1, y0), (x1, y1), hn, h)
            # West wall. Each wall between unequal columns is drawn once, by
            # the taller column.
            hw = height[r, c - 1] if c > 0 else 0.0
            if h > hw:
                wall((x0, y1), (x0, y0), hw, h)
            # South wall (towards row r+1, smaller y).
            hs = height[r + 1, c] if r + 1 < rows else 0.0
            if h > hs:
                wall((x0, y0), (x1, y0), hs, h)
            # North wall (towards row r-1, larger y).
            hnn = height[r - 1, c] if r > 0 else 0.0
            if h > hnn:
                wall((x1, y1), (x0, y1), hnn, h)
    return np.asarray(tris, dtype=np.float32)


def slab_mesh(mask, z0, z1, cell=SITE_MM):
    """Surface of the cells in mask, extruded from z0 to z1."""
    tris = heightmap_mesh(np.where(mask, z1 - z0, 0.0), cell)
    tris[:, :, 2] += z0
    return tris


def write_stl(path, tris):
    tris = np.asarray(tris, np.float32)
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals),
                        where=lengths > 0)
    record = np.zeros(len(tris), dtype=[('n', '<f4', 3), ('v', '<f4', (3, 3)),
                                        ('attr', '<u2')])
    record['n'] = normals
    record['v'] = tris
    with open(path, 'wb') as f:
        f.write(b'ising print-test tile'.ljust(80, b' '))
        f.write(struct.pack('<I', len(tris)))
        f.write(record.tobytes())


def ols_slope(t, length):
    x, y = np.log(t), np.log(length)
    return float(np.polyfit(x, y, 1)[0])


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    truth = dict(site_mm=SITE_MM, margin_cells=MARGIN, frame_cells=FRAME,
                 marker_cells=MARKER, base_mm=BASE_MM, raise_mm=RAISE_MM,
                 times=list(TIMES), compositions={})
    base_written = False
    for comp, name in SOURCES.items():
        data = np.load(RUN_DIR / name, allow_pickle=True)
        t_all = data['t']
        cfg = json.loads(str(data['config']))
        entry = dict(source=str(RUN_DIR / name), seed=cfg['seed'],
                     T_final=cfg['T_final'], concentration=cfg['concentration'],
                     tiles=[])
        native, model = [], {k: [] for k in (2, 4)}
        for t in TIMES:
            i = int(np.flatnonzero(t_all == t)[0])
            snap = data['snapshots'][i].astype(float)
            tile_id = f'{comp}_t{t:05d}'
            white = tile_layout(snap)
            if not base_written:
                write_stl(out / 'base.stl',
                          slab_mesh(np.ones_like(white), 0.0, BASE_MM))
                base_written = True
            height = np.where(white, BASE_MM + RAISE_MM, BASE_MM)
            write_stl(out / f'{tile_id}_combined.stl', heightmap_mesh(height))
            write_stl(out / f'{tile_id}_white.stl',
                      slab_mesh(white, BASE_MM, BASE_MM + RAISE_MM))
            np.save(out / f'{tile_id}_snapshot.npy', snap.astype(np.int8))
            n_len = image_length(snap)['length']
            native.append(n_len)
            for k in model:
                model[k].append(image_length(observe(snap, factor=k),
                                             pixel_size=k)['length'])
            entry['tiles'].append(dict(id=tile_id, t=t, index=i,
                                       native_length_sites=n_len,
                                       white_fraction=float((snap > 0).mean())))
        entry['native_exponent'] = ols_slope(TIMES, native)
        entry['block_model_exponent'] = {
            f'factor_{k}': ols_slope(TIMES, v) for k, v in model.items()}
        truth['compositions'][comp] = entry
    (out / 'truth.json').write_text(json.dumps(truth, indent=2))
    return truth


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=Path('output/print_test'))
    t = build(p.parse_args().out)
    for comp, e in t['compositions'].items():
        print(comp, 'native n =', round(e['native_exponent'], 4),
              'block model', {k: round(v, 4)
                              for k, v in e['block_model_exponent'].items()})
