"""Build index.html: inject the example ageing series into template.html.

The example is one archived 0.65 Tc, 50:50 Kawasaki trajectory at six times,
stored as packed bits (+1 sites) so the page stays self-contained.
Usage: python tools/pixel_check/build.py
"""
import base64
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RUN = Path('research/runs/main_065_multisize_v1/c0_L128_rep000.npz')
TIMES = (646, 1300, 2617, 5266, 10600, 21336)


def main():
    data = np.load(RUN)
    samples = []
    for t in TIMES:
        snap = data['snapshots'][int(np.flatnonzero(data['t'] == t)[0])]
        bits = np.packbits((snap > 0).astype(np.uint8).ravel())
        samples.append(dict(t=t, n=int(snap.shape[0]),
                            bits=base64.b64encode(bits.tobytes()).decode()))
    html = (HERE / 'template.html').read_text()
    html = html.replace('/*SAMPLES*/[]', json.dumps(samples))
    (HERE / 'index.html').write_text(html)
    print('wrote', HERE / 'index.html', len(html) // 1024, 'KB')


if __name__ == '__main__':
    main()
