"""The browser pixel check must match the project's Python estimator."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from research.imaging import image_length, observe

PAGE = Path('tools/pixel_check/index.html')
RUN = Path('research/runs/main_065_multisize_v1/c0_L128_rep000.npz')


@unittest.skipUnless(shutil.which('node') and PAGE.exists(), 'needs node and a built page')
class PixelCheckMatchesPython(unittest.TestCase):
    def test_lengths_and_exponents_match(self):
        core = re.search(r'<script id="core">(.*?)</script>', PAGE.read_text(), re.S).group(1)
        d = np.load(RUN)
        snaps, ref = [], []
        for i in (10, 30, 50, 70):
            s = d['snapshots'][i].astype(float)
            snaps.append(s.ravel().tolist())
            ref.append([image_length(s)['length'],
                        image_length(observe(s, factor=2), pixel_size=2)['length']])
        js = core.replace('const Core', 'globalThis.Core') + """
        const snaps = %s; const out = snaps.map(s => { const f = Float32Array.from(s);
          const c = Core.coarsen(f, 128, 128, 2);
          return [Core.measure(f, 128, 128).length, Core.measure(c.f, c.w, c.h).length * 2]; });
        console.log(JSON.stringify(out));""" % json.dumps(snaps)
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
            f.write(js)
        got = json.loads(subprocess.run(['node', f.name], capture_output=True,
                                        text=True, check=True).stdout)
        np.testing.assert_allclose(got, ref, rtol=1e-6)


if __name__ == '__main__':
    unittest.main()
