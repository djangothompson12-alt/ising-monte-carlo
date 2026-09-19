"""Separately coded arithmetic checks of the reported observation experiment.

No production fitting, image-correlation or crossing helper is imported.
This is internal verification, not an independent researcher endorsement.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform

import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def direct_lengths(field, spacing=1):
    a=np.asarray(field,dtype=float)
    a=a-a.mean()
    variance=np.mean(a*a)
    lengths=[]
    for axis in (1,0):
        if variance == 0:
            lengths.append(float('nan')); continue
        values=[]
        for lag in range(min(a.shape)//2+1):
            left=[slice(None)]*2; right=left.copy()
            left[axis]=slice(0,a.shape[axis]-lag)
            right[axis]=slice(lag,a.shape[axis])
            values.append(np.mean(a[tuple(left)]*a[tuple(right)])/variance)
        length=float('nan')
        for i in range(len(values)-1):
            if values[i]>=.5 and values[i+1]<.5:
                length=spacing*(i+(values[i]-.5)/(values[i]-values[i+1])); break
        lengths.append(length)
    return np.asarray(lengths)


def slope(times, trajectories):
    x=np.log(times); x=x-x.mean()
    y=np.log(trajectories.mean(axis=0))
    return float(np.dot(x,y-y.mean())/np.dot(x,x))


def differences(times, treatment, reference, draws, seed):
    rng=np.random.default_rng(seed)
    delta=[]
    for _ in range(draws):
        ix=rng.integers(len(treatment),size=len(treatment))
        delta.append(slope(times,treatment[ix])-slope(times,reference[ix]))
    return np.percentile(delta,[2.5,97.5])


def run(campaign, analysis, output):
    if output.exists(): raise FileExistsError('Choose a new output directory')
    manifest=json.loads((analysis/'manifest.json').read_text())
    for name,expected in manifest['input_sha256'].items():
        if digest(campaign/name)!=expected: raise ValueError('Raw input changed: '+name)
    root=Path(__file__).resolve().parents[1]
    for name,expected in manifest['source_sha256'].items():
        if digest(root/name)!=expected: raise ValueError('Analysis source changed: '+name)
    observations=list(csv.DictReader((analysis/'per_checkpoint.csv').open()))
    index={(r['file'],int(r['sweep'])):r for r in observations}
    if len(index)!=len(observations): raise ValueError('Duplicate file/checkpoint row')
    errors=[]; checks=0
    # Fixed first, middle and final checkpoint in every included trajectory.
    for name in sorted(manifest['input_sha256']):
        with np.load(campaign/name,allow_pickle=False) as raw:
            for k in (0,len(raw['t'])//2,len(raw['t'])-1):
                field=raw['snapshots'][k]; t=int(raw['t'][k])
                integrated=np.array([[field[y:y+4,x:x+4].mean()
                    for x in range(0,128,4)] for y in range(0,128,4)])
                if integrated.mean()!=field.mean(): raise AssertionError('Mean not preserved')
                segmented=np.where(integrated>=0,1,-1)
                row=index[(name,t)]
                for label,image,spacing in [('native',field,1),('integrated',integrated,4),('segmented',segmented,4)]:
                    actual=direct_lengths(image,spacing)
                    expected=np.array([float(row[label+'_x']),float(row[label+'_y'])])
                    np.testing.assert_allclose(actual,expected,atol=1e-10,rtol=1e-10,equal_nan=True)
                    finite=np.isfinite(actual)&np.isfinite(expected)
                    errors.extend(abs(actual[finite]-expected[finite]).tolist()); checks+=2
    fit_rows=list(csv.DictReader((analysis/'paired_fits.csv').open()))
    results=[]
    for composition in sorted(set(float(r['composition']) for r in observations)):
        selected=[r for r in observations if float(r['composition'])==composition]
        files=sorted(set(r['file'] for r in selected)); times=np.array(sorted(set(int(r['sweep']) for r in selected)))
        if len(files)!=16 or len(selected)!=len(files)*len(times): raise ValueError('Incomplete trajectories')
        values={stage:np.array([[[float(index[(file,int(t))][stage+'_'+axis]) for axis in ('x','y')]
                    for t in times] for file in files]) for stage in ('native','integrated','segmented')}
        common=np.all(np.isfinite(np.stack(list(values.values()))) & (np.stack(list(values.values()))>0),axis=(0,1,3))
        lengths={key:array.mean(axis=2) for key,array in values.items()}
        for old in [r for r in fit_rows if float(r['composition'])==composition]:
            mask=common&(times>=int(old['nominal_t_min']))&(times<=int(old['nominal_t_max']))
            used=times[mask]; a=lengths[old['treatment']][:,mask]; b=lengths[old['reference']][:,mask]
            assert len(used)==int(old['retained_points'])
            assert int(used[0])==int(old['actual_t_min']) and int(used[-1])==int(old['actual_t_max'])
            delta=slope(used,a)-slope(used,b)
            original=differences(used,a,b,500,912)
            np.testing.assert_allclose([slope(used,a),slope(used,b),delta,*original],
                [float(old[k]) for k in ('treatment_alpha','reference_alpha','delta_alpha','delta_low','delta_high')],atol=1e-12)
            extended=differences(used,a,b,5000,90817)
            loo=[slope(used,np.delete(a,i,axis=0))-slope(used,np.delete(b,i,axis=0)) for i in range(16)]
            results.append(dict(composition=composition,comparison=old['comparison'],
                nominal_t_max=int(old['nominal_t_max']),actual_t_min=int(used[0]),actual_t_max=int(used[-1]),
                points=len(used),delta_alpha=delta,original_low=original[0],original_high=original[1],
                draws5000_low=extended[0],draws5000_high=extended[1],leave_one_out_min=min(loo),leave_one_out_max=max(loo)))
    output.mkdir(parents=True)
    with (output/'fit_checks.csv').open('x',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    report=dict(status='passed',independence='Separately coded arithmetic; same AI assistant, not external review',
        selected_snapshots=checks//6,directional_length_checks=checks,max_absolute_length_difference=max(errors),
        fit_rows_checked=len(results),original_draws=500,sensitivity_draws=5000,
        primary_analysis_unchanged=True,python=platform.python_version(),numpy=np.__version__,
        audit_source_sha256=digest(Path(__file__)),input_analysis_manifest_sha256=digest(analysis/'manifest.json'),
        analysis_table_sha256={name:digest(analysis/name) for name in ('per_checkpoint.csv','paired_fits.csv')},
        output_sha256={'fit_checks.csv':digest(output/'fit_checks.csv')})
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('campaign',type=Path); p.add_argument('analysis',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); run(a.campaign,a.analysis,a.output)
