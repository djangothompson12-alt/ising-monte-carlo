"""Freeze source/protocol hashes and audit new seeds before any holdout run."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
from research.audit_growth_reliability import sources,ROOT


def run(output):
    if output.exists(): raise FileExistsError('Never overwrite a validation freeze')
    plan=json.loads((ROOT/'research/plans/growth_reliability_holdout_v1.json').read_text())
    old_seeds={902100};manifests=[]
    for folder in ('smoke','pilot','overnight','imaging_validation','main_065_multisize_v1','majumder_das_2010_l128'):
        directory=ROOT/'research/runs'/folder
        if not directory.exists(): continue
        for path in directory.glob('*.npz'):
            with np.load(path,allow_pickle=False) as raw:
                old_seeds.add(int(json.loads(raw['config'].item())['seed']))
        manifests.append(str(directory.relative_to(ROOT)))
    new=[int(np.random.SeedSequence([plan['seed'],rep,ci,0]).generate_state(1)[0]) for rep in range(plan['replicas']) for ci in range(2)]
    if len(set(new))!=len(new) or old_seeds.intersection(new): raise ValueError('Seed reuse detected')
    destination=ROOT/'research/runs/growth_reliability_holdout_v1'
    if destination.exists(): raise ValueError('Holdout directory already exists; cannot assert pre-generation freeze')
    result=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),sources=sources(),
        new_seeds=new,checked_prior_seed_count=len(old_seeds),checked_campaigns=manifests,
        boundary='Frozen before generation; exact old-source papers not replicated by directional adaptation.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:json.dump(result,f,indent=2)
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
