"""Prepare the declared Al–Ge boxes without inspecting their length outcomes."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.volume_audit import sha

EXPECTED={
    15:'0d86052b4ea7e70fbfece3f78adc9440c4a750f389ed314d85d54c2744be0b45',
    105:'c902533697d0b6ff3350000dbe8eb99c3b1187ef0133b8313d4597d9df9ca9cc',
    195:'6ea208e3754ca60d1910e6cc36eb61bba9482dd0a040f000157848c469e393f8',
    315:'c75147d514e162b94de8fcdfaa9848c3acd8d68683098f07f5566363077ca153'}


def prepare(source, destination):
    records=[]
    for minutes,digest in EXPECTED.items():
        path=(source/f'ROI_{minutes}min.tif').resolve()
        if sha(path)!=digest:
            raise ValueError(f'Source mismatch: {path.name}')
        with Image.open(path) as image:
            image.seek(169)
            plane=np.asarray(image)
            y,x=np.nonzero((plane==2)|(plane==3))
            if not len(y): raise ValueError('No solid centroid on declared middle page')
            y0,x0=int(round(y.mean()-128)),int(round(x.mean()-128))
        records.append(dict(id=f'AlGe_{minutes}min',specimen='Al–Ge source time series',
            path=str(path),sha256=digest,roi_zyx=[[41,297],[y0,y0+256],[x0,x0+256]],
            spacing_zyx=[.06]*3,unit='um',foreground=3,background=2,tie_rule='foreground',
            roi_reason='Fixed 256-cube at page 169 and solid centroid on that page; no outcome-based relocation.',
            phase_definition='Ge label 3 versus Al label 2; other labels invalidate the box.',
            mask_authority='Depositor segmentation; no independent accuracy validation.'))
    plan=dict(source='Jonas Fell (2023), Microstructural evolution of an Al-Ge alloy revealed by nano-CT, Mendeley Data v1, doi:10.17632/hj9njz3rxp.1; https://data.mendeley.com/datasets/hj9njz3rxp/1',
        license='CC BY 4.0; attribution and source DOI must accompany reuse.',
        protocol_sha256=sha(Path(__file__).with_name('VOLUME_AUDIT_PROTOCOL_2026-09-19.md')),
        records=records)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x') as stream: json.dump(plan,stream,indent=2)
    return destination


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    args=p.parse_args()
    print(prepare(args.source,args.plan))
