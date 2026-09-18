"""Read-only integrity and physical-contract audit of a completed campaign."""
import argparse
import json
import re
from pathlib import Path
import numpy as np
from research.imaging_benchmark import sha


def verify(folder, source_root=None):
    m=json.loads((folder/'manifest.json').read_text());plan=m['identity']['plan']
    expected={f'c{ci}_L{L}_rep{rep:03d}.npz' for ci,_ in enumerate(plan['concentrations'])
        for L in plan['sizes'] for rep in range(plan['replicas'])}
    paths=sorted(folder.glob('*.npz'))
    if {p.name for p in paths}!=expected:raise ValueError('Incomplete or unexpected replica inventory')
    root=Path(__file__).resolve().parents[1] if source_root is None else Path(source_root)
    for name,digest in m['identity']['sources'].items():
        source_path=root/name
        if not source_path.is_file():raise FileNotFoundError(f'Missing simulation source: {source_path}')
        if sha(source_path)!=digest:raise ValueError(f'Simulation source changed: {name}')
    seeds=set();snapshots=0
    for path in paths:
        match=re.fullmatch(r'c(\d+)_L(\d+)_rep(\d+)\.npz',path.name)
        if match is None:raise ValueError(f'Unexpected replica filename: {path.name}')
        ci,L,rep=(int(value) for value in match.groups())
        li=plan['sizes'].index(L)
        expected_seed=int(np.random.SeedSequence([plan['seed'],rep,ci,li]).generate_state(1)[0])
        with np.load(path,allow_pickle=False) as d:
            c=json.loads(str(d['config']));s=d['snapshots'];t=d['t']
            expected_config=dict(L=L,concentration=plan['concentrations'][ci],
                Jx=plan['Jx'],Jy=plan['Jy'],max_sweeps=plan['max_sweeps'],
                n_time_samples=plan['time_samples'],eq_sweeps_initial=plan['equilibration'],
                seed=expected_seed,n_replicas=1)
            for key,value in expected_config.items():
                if c.get(key)!=value:raise ValueError(f'{path.name}: config {key} does not match plan/filename')
            if c['seed'] in seeds:raise ValueError('Duplicate seed')
            seeds.add(c['seed'])
            if t[-1]!=plan['max_sweeps'] or not np.all(np.diff(t)>0):raise ValueError('Bad checkpoint times')
            if not np.all(np.isin(s,[-1,1])):raise ValueError('Non-Ising spins')
            if s.shape!=(len(t),c['L'],c['L']):raise ValueError('Bad snapshot shape')
            magnet=s.sum(axis=(1,2))
            if not np.all(magnet==d['magnetization']):raise ValueError('Magnetisation mismatch')
            np.testing.assert_allclose((magnet/s[0].size+1)/2,d['realized_concentration'])
            f=s.astype(float)
            e=-c['Jx']*np.sum(f*np.roll(f,1,axis=2),axis=(1,2))-c['Jy']*np.sum(f*np.roll(f,1,axis=1),axis=(1,2))
            np.testing.assert_allclose(np.diff(e),d['delta_energy'][1:],atol=1e-9)
            snapshots+=len(t)
    result=dict(replicas=len(paths),snapshots=snapshots,unique_seeds=len(seeds),
        source_hashes_match=True,plan_configs_and_seeds_match=True,
        magnetisation_and_later_energy_intervals_checked=True,
        first_energy_interval_independently_checked=False)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path)
    p.add_argument('--source-root',type=Path,default=None,
                   help='Root containing the exact source files recorded in the campaign manifest')
    args=p.parse_args();verify(args.folder,args.source_root)
