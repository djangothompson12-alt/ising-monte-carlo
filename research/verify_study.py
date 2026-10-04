"""Read-only integrity and physical-contract audit of a completed campaign."""
import argparse
import json
import re
from pathlib import Path
import numpy as np
from research.imaging_benchmark import sha


def planned_temperatures(plan):
    """Independently solve the anisotropic condition; preserve old defaults."""
    jx,jy=float(plan['Jx']),float(plan['Jy'])
    if not np.all(np.isfinite([jx,jy])) or min(jx,jy)<=0:
        raise ValueError('Finite positive ferromagnetic couplings required')
    low,high=.05*min(jx,jy),50*max(jx,jy)
    for _ in range(100):
        midpoint=(low+high)/2
        with np.errstate(over='ignore'):
            product=np.sinh(2*jx/midpoint)*np.sinh(2*jy/midpoint)
        if product>1:low=midpoint
        else:high=midpoint
    tc=(low+high)/2
    values={}
    for key,default in (('T_initial',3.),('T_final',.65)):
        ratio=plan.get(key+'_over_tc')
        ratio=default if ratio is None else float(ratio)
        if not np.isfinite(ratio) or ratio<=0:raise ValueError('Invalid temperature ratio')
        values[key]=ratio*tc
    return values


def verify(folder, source_root=None):
    m=json.loads((folder/'manifest.json').read_text());plan=m['identity']['plan']
    temperatures=planned_temperatures(plan)
    expected_times=np.unique(np.round(np.logspace(0,np.log10(plan['max_sweeps']),plan['time_samples'])).astype(np.int64))
    expected_times=expected_times[expected_times>=1]
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
            for key,value in temperatures.items():
                actual=c.get(key)
                if actual is None or not np.isfinite(actual) or not np.isclose(actual,value,rtol=1e-11,atol=1e-11):
                    raise ValueError(f'{path.name}: config {key} does not match the planned quench')
            if c['seed'] in seeds:raise ValueError('Duplicate seed')
            seeds.add(c['seed'])
            if t[-1]!=plan['max_sweeps'] or not np.all(np.diff(t)>0):raise ValueError('Bad checkpoint times')
            if not np.array_equal(t,expected_times):raise ValueError('Checkpoint grid does not match the plan')
            if not np.all(np.isin(s,[-1,1])):raise ValueError('Non-Ising spins')
            if s.shape!=(len(t),c['L'],c['L']):raise ValueError('Bad snapshot shape')
            magnet=s.sum(axis=(1,2))
            expected_magnet=2*round(c['concentration']*L*L)-L*L
            if not np.all(magnet==expected_magnet):raise ValueError('Species count does not match nominal composition rounding')
            if not np.all(magnet==d['magnetization']):raise ValueError('Magnetisation mismatch')
            np.testing.assert_allclose((magnet/s[0].size+1)/2,d['realized_concentration'])
            f=s.astype(float)
            e=-c['Jx']*np.sum(f*np.roll(f,1,axis=2),axis=(1,2))-c['Jy']*np.sum(f*np.roll(f,1,axis=1),axis=(1,2))
            np.testing.assert_allclose(np.diff(e),d['delta_energy'][1:],atol=1e-9)
            snapshots+=len(t)
    result=dict(replicas=len(paths),snapshots=snapshots,unique_seeds=len(seeds),
        source_hashes_match=True,plan_configs_and_seeds_match=True,
        temperatures_checkpoint_grid_and_nominal_species_count_checked=True,
        magnetisation_and_later_energy_intervals_checked=True,
        first_energy_interval_independently_checked=False)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path)
    p.add_argument('--source-root',type=Path,default=None,
                   help='Root containing the exact source files recorded in the campaign manifest')
    args=p.parse_args();verify(args.folder,args.source_root)
