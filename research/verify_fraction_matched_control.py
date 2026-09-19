"""Separately reconstruct the new control and its primary paired statistics.

Uses full sorting instead of the production partition/cutoff method, explicit
block loops, direct pair products instead of FFT correlations, and the separate
reviewer arithmetic. Internal AI-assisted verification, not external review.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from research.reviewer_numerical_audit import digest, direct_lengths, slope, differences


def run(campaign, analysis, output):
    if output.exists(): raise FileExistsError('Choose a new verification directory')
    manifest=json.loads((analysis/'manifest.json').read_text())
    for name,expected in manifest['outputs'].items():
        if digest(analysis/name)!=expected: raise ValueError('Analysis output changed')
    root=Path(__file__).resolve().parents[1]
    for name,expected in manifest['sources'].items():
        if digest(root/'research'/name)!=expected: raise ValueError('Analysis source changed')
    rows=list(csv.DictReader((analysis/'simulation_observations.csv').open()))
    lookup={(r['id'],int(r['sweep']),int(r['factor']),r['stage'],int(r['tie_seed'])):float(r['length']) for r in rows}
    if len(lookup)!=len(rows): raise ValueError('Duplicate observation')
    seeds=manifest['tie_seeds']; checks=0; errors=[]
    for name,expected in sorted(manifest['simulation_input_sha256'].items()):
        if digest(campaign/name)!=expected: raise ValueError('Trajectory changed')
        with np.load(campaign/name,allow_pickle=False) as raw:
            for k in (0,len(raw['t'])//2,len(raw['t'])-1):
                field=(raw['snapshots'][k]+1)/2; t=int(raw['t'][k])
                coarse=np.array([[field[y:y+4,x:x+4].mean() for x in range(0,128,4)] for y in range(0,128,4)])
                count=int(np.floor(coarse.size*field.mean()+.5))
                for seed in seeds:
                    priority=np.random.default_rng(seed).random(coarse.size)
                    order=np.lexsort((priority,-coarse.ravel()))
                    binary=np.zeros(coarse.size); binary[order[:count]]=1
                    actual=float(np.mean(direct_lengths(binary.reshape(coarse.shape),4)))
                    reference=lookup[name,t,4,'matched',seed]
                    np.testing.assert_allclose(actual,reference,atol=1e-10,rtol=1e-10,equal_nan=True)
                    if np.isfinite(actual): errors.append(abs(actual-reference))
                    checks+=1
    fits=list(csv.DictReader((analysis/'simulation_fits.csv').open())); verified=[]
    for composition in (.5,.15):
        selected=[r for r in rows if float(r['composition'])==composition and int(r['factor'])==4]
        names=sorted(set(r['id'] for r in selected)); times=np.array(sorted(set(int(r['sweep']) for r in selected)))
        values={stage:np.array([[lookup[name,int(t),4,stage,-1] for t in times] for name in names]) for stage in ('native','integrated','fixed')}
        tied=np.array([[[lookup[name,int(t),4,'matched',seed] for t in times] for name in names] for seed in seeds])
        common=np.all(np.isfinite(tied)&(tied>0),axis=(0,1))
        for a in values.values(): common &= np.all(np.isfinite(a)&(a>0),axis=0)
        keep=common&(times>=1000)&(times<=20000)
        t=times[keep]; reference=values['native'][:,keep]; treatment=tied.mean(axis=0)[:,keep]
        delta=slope(t,treatment)-slope(t,reference)
        old=next(r for r in fits if float(r['composition'])==composition and int(r['factor'])==4 and r['stage']=='matched' and int(r['nominal_t_max'])==20000)
        original=differences(t,treatment,reference,500,912)
        np.testing.assert_allclose([delta,*original],[float(old[key]) for key in ('delta_alpha','low','high')],atol=1e-12)
        longer=differences(t,treatment,reference,5000,90817)
        loo=[slope(t,np.delete(treatment,i,axis=0))-slope(t,np.delete(reference,i,axis=0)) for i in range(16)]
        verified.append(dict(composition=composition,delta_alpha=delta,draws5000_low=longer[0],draws5000_high=longer[1],leave_one_out_min=min(loo),leave_one_out_max=max(loo)))
    output.mkdir(parents=True)
    report=dict(status='passed',description=__doc__,selected_mask_measurements=checks,
        max_absolute_length_difference=max(errors),primary_fit_checks=verified,
        input_manifest_sha256=digest(analysis/'manifest.json'),source_sha256=digest(Path(__file__)),
        separate_arithmetic_sha256=digest(Path(__file__).with_name('reviewer_numerical_audit.py')))
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('campaign',type=Path);p.add_argument('analysis',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.campaign,a.analysis,a.output)
