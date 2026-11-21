import collections
import unittest

import numpy as np

from research.print_test.make_tiles import (RUN_DIR, SOURCES, heightmap_mesh,
                                            slab_mesh, tile_layout)
from research.print_test.analyse_photos import measure, render


def _closed(tris):
    tris = np.round(tris.astype(float), 4)
    directed = collections.Counter()
    for t in tris:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            directed[(tuple(t[a]), tuple(t[b]))] += 1
    return all(directed.get((b, a), 0) == c for (a, b), c in directed.items())


def _volume(tris):
    t = tris.astype(float)
    return np.sum(np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2]))) / 6


class MeshTests(unittest.TestCase):
    def test_heightmap_is_closed_with_outward_normals(self):
        h = np.where(np.random.default_rng(3).random((15, 15)) > .5, 1.8, 1.2)
        tris = heightmap_mesh(h)
        self.assertTrue(_closed(tris))
        self.assertAlmostEqual(_volume(tris), h.sum(), places=3)

    def test_slab_is_closed_and_lifted(self):
        m = np.random.default_rng(4).random((15, 15)) > .5
        tris = slab_mesh(m, 1.2, 1.8)
        self.assertTrue(_closed(tris))
        self.assertAlmostEqual(_volume(tris), m.sum() * .6, places=3)
        self.assertAlmostEqual(float(tris[:, :, 2].min()), 1.2, places=5)


class PhotoPipelineTests(unittest.TestCase):
    def test_sharp_render_recovers_scale_and_length(self):
        from research.imaging import image_length
        data = np.load(RUN_DIR / SOURCES['5050'])
        snap = data['snapshots'][40].astype(float)
        truth = dict(margin_cells=8, frame_cells=[1, 4])
        m = measure(render(tile_layout(snap), 4.0, blur_px=0, noise=0), truth)
        self.assertAlmostEqual(m['px_per_site'], 4.0, delta=0.02)
        native = image_length(snap)['length']
        self.assertAlmostEqual(m['length_sites'], native, delta=0.05 * native)


if __name__ == '__main__':
    unittest.main()
