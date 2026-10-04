"""Recalculate the older manuscript's numerical baselines from saved summaries.

These aggregate CSVs do not supply per-replica histories, so this check cannot
validate their uncertainty bars or recover their original random trajectories.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from model_b.kawasaki_engine import lsw_scaling_function

ROOT=Path(__file__).resolve().parents[1]


def fit(times,lengths,width):
    t,a=np.asarray(times,float),np.asarray(lengths,float)
    if t.shape!=a.shape or t.ndim!=1:raise ValueError('Matching vectors required')
    keep=np.isfinite(t)&np.isfinite(a)&(t>2)&(a>0)&(a<=.15*width)
    if keep.sum()<3:raise ValueError('Too few retained points')
    x,y=np.log(t[keep]),np.log(a[keep])
    xc=x-x.mean()
    if xc@xc==0:raise ValueError('Times must vary')
    return dict(alpha=float(xc@(y-y.mean())/(xc@xc)),retained_points=int(keep.sum()),
                first_sweep=float(t[keep][0]),last_sweep=float(t[keep][-1]),
                length_cutoff=.15*width)


def run(output):
    if output.exists():raise FileExistsError('Choose a new audit output')
    files=('model_a/results/quench_kinetics.csv','model_b/results/kawasaki_kinetics.csv',
           'model_a/results/concentration_exponent_sweep.csv','model_b/results/concentration_exponent_sweep.csv',
           'model_b/results/droplet_sizes_dilute_quench.csv')
    data=[np.genfromtxt(ROOT/name,names=True,delimiter=',') for name in files]
    a,b,ca,cb,droplets=data
    slopes={}
    for label,table,column,width,rounded,digits in (
        ('model_a',a,'domain_size',128,.4999,4),
        ('model_b_x',b,'domain_size_x',96,.183,3),
        ('model_b_y',b,'domain_size_y',96,.138,3)):
        result=fit(table['t_sweeps'],table[column],width)
        if round(result['alpha'],digits)!=rounded:raise ValueError('Legacy slope claim changed: '+label)
        slopes[label]=result
    heat={}
    for label,table in (('model_a',a),('model_b',b)):
        first,last=table['entropy_production_rate'][[0,-1]]
        heat[label]=dict(first=float(first),last=float(last),endpoint_ratio=float(first/last),
            first_sweep=float(table['t_sweeps'][0]),last_sweep=float(table['t_sweeps'][-1]))
    moments=[]
    for power in (0,1):
        value,error=quad(lambda u:u**power*float(lsw_scaling_function(np.array([u]))[0]),
            0,1.5,epsabs=1e-11,epsrel=1e-11,points=[1,1.4,1.49])
        if abs(value-1)>1e-9 or error>1e-8:raise ValueError('LSW moment check failed')
        moments.append(dict(order=power,value=value,quadrature_error_estimate=error))
    n=int(droplets.size)
    if n!=513 or np.min(droplets['droplet_size_lattice_sites'])<4:raise ValueError('Droplet-count claim differs')
    result=dict(status='passed_with_scope_limits',scope=__doc__,slopes=slopes,bath_flow_endpoints=heat,
        concentration_exponents=dict(model_a=ca['fitted_exponent'].tolist(),model_b=cb['fitted_exponent'].tolist(),
            model_a_mean=float(ca['fitted_exponent'].mean()),model_a_sample_sd=float(ca['fitted_exponent'].std(ddof=1))),
        droplet_count=n,lsw_moments=moments,
        input_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
            ('research/audit_legacy_numbers.py','model_b/kawasaki_engine.py')},
        limitations=['Original raw replica uncertainty cannot be reconstructed from aggregate tables.',
            'No monotonicity or total entropy-production claim follows from two bath-flow endpoints.',
            'LSW normalization and first moment do not validate its 3D assumptions for 2D clusters.',
            'Length cutoff is the historical fitting choice, not a verified asymptotic criterion.'])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output)
