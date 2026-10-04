"""Recheck four completed campaigns without rerunning post-quench dynamics.

Metadata, source identities, conservation and all heat intervals are checked.
The first interval uses seeded preparation replay with the original kernel,
not a separately implemented Monte Carlo algorithm. Never alters raw inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import numba

from research.verify_study import verify
from research.replay_first_energy_interval import replay_file

ROOT=Path(__file__).resolve().parents[1]
CAMPAIGNS=(('overnight','research/frozen_sources/2026-09-10'),
           ('main_065_multisize_v1','.'),('majumder_das_2010_l128','.'),
           ('growth_reliability_holdout_v1','.'))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output):
    if output.exists():raise FileExistsError('Choose a new audit output')
    records=[]
    for name,source_root in CAMPAIGNS:
        folder=ROOT/'research/runs'/name
        checked=verify(folder,ROOT/source_root)
        maximum=0.;raw_hashes={}
        manifest=json.loads((folder/'manifest.json').read_text())
        engine_path=ROOT/'model_b/kawasaki_engine.py'
        if sha(engine_path)!=manifest['identity']['sources']['model_b/kawasaki_engine.py']:
            raise ValueError('Loaded preparation kernel differs from archive')
        for path in sorted(folder.glob('*.npz')):
            actual,reported=replay_file(path)
            maximum=max(maximum,abs(actual-reported))
            raw_hashes[path.name]=sha(path)
        records.append(dict(campaign='research/runs/'+name,source_root=source_root,
            **{**checked,'first_energy_interval_independently_checked':True},
            first_interval_max_absolute_energy_difference=maximum,
            campaign_manifest_sha256=sha(folder/'manifest.json'),raw_npz_sha256=raw_hashes))
        print('Complete campaign check:',name,flush=True)
    sources=('research/audit_campaign_contracts.py','research/verify_study.py',
             'research/replay_first_energy_interval.py','model_b/kawasaki_engine.py')
    result=dict(status='passed',scope=__doc__,campaigns=records,
        replicas=sum(r['replicas'] for r in records),snapshots=sum(r['snapshots'] for r in records),
        source_sha256={name:sha(ROOT/name) for name in sources},
        python=platform.python_version(),numpy=np.__version__,numba=numba.__version__,
        limitations=['Preparation replay shares the original update kernel.',
                     'No confirmation of asymptotic kinetics, literature replication or material calibration.'])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Verified',result['replicas'],'replicas and',result['snapshots'],'snapshots')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    run(parser.parse_args().output)
