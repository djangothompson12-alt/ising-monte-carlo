"""Check a minimal copied audit outside the checkout under another interpreter.

This is a clean-copy/cross-runtime check, not a from-network installation test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np


def run(interpreter,output):
    if output.exists(): raise FileExistsError('Choose a new result file')
    root=Path(__file__).resolve().parents[1]
    names=['research/volume_audit.py','research/volume_metrology.py','research/metrology.py','tests/test_volume_audit.py']
    with tempfile.TemporaryDirectory(prefix='ising-review-',dir='/private/tmp') as temp:
        work=Path(temp)
        for name in names:
            dest=work/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(root/name,dest)
        tests=subprocess.run([str(interpreter),'-E','-s','-m','unittest','discover','-s','tests','-p','test_volume_audit.py','-v'],cwd=work,capture_output=True,text=True)
        if tests.returncode: raise RuntimeError(tests.stdout+tests.stderr)
        z,y,x=np.indices((32,32,32)); mask=((z-15.5)**2+(y-15.5)**2+(x-15.5)**2<49).astype(np.uint8)
        np.save(work/'mask.npy',mask)
        plan=dict(source='Generated sphere, not an experiment',license='CC0 synthetic example',records=[dict(
            id='sphere',specimen='synthetic',path='mask.npy',spacing_zyx=[.1,.2,.3],unit='um',foreground=1,background=0,
            tie_rule='foreground',roi_zyx=[[0,32]]*3,roi_reason='Whole synthetic cube',phase_definition='Binary sphere',mask_authority='Analytical coordinate construction')])
        (work/'plan.json').write_text(json.dumps(plan))
        cli=subprocess.run([str(interpreter),'-E','-s','-m','research.volume_audit','plan.json','--output','demo'],cwd=work,capture_output=True,text=True)
        if cli.returncode: raise RuntimeError(cli.stdout+cli.stderr)
        versions=subprocess.check_output([str(interpreter),'-E','-s','-c','import sys,json,numpy,PIL; print(json.dumps(dict(python=sys.version,numpy=numpy.__version__,Pillow=PIL.__version__)))'],cwd=work,text=True)
        audit=json.loads((work/'demo/manifest.json').read_text())
        result=dict(status='passed',scope='Clean copied sources and CLI in a second existing runtime; not fresh pip installation',
            versions=json.loads(versions),tests=tests.stderr.replace(str(work),'<clean-copy>'),
            source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names},
            demo_outputs_sha256=audit['outputs'])
        output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2)+'\n')
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--python',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True); a=p.parse_args(); run(a.python,a.output)
