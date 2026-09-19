"""Paired dynamics control and external static-mask test under one operator set."""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import numpy as np
from research.fraction_matching import integrate,match_fraction,TIE_SEEDS
from research.imaging import image_length
from research.volume_metrology import measure
from research.volume_audit import load_box,sha

FACTORS=(2,4,8)
ROOT=Path(__file__).resolve().parents[1]


def lengths(field,spacing):
    if field.ndim==2:
        a=image_length(field,spacing)
        return [a['length_y'],a['length_x']]
    a=measure(field,[spacing]*3)
    return [a['half_height_z'],a['half_height_y'],a['half_height_x']]


def observe(field,spacing,context):
    target=float(field.mean()); native=lengths(field,spacing); ref=float(np.mean(native))
    rows=[]
    for factor in FACTORS:
        averaged=integrate(field,factor)
        if abs(averaged.mean()-target)>1e-12: raise AssertionError('Integration changed mean')
        versions=[('native',-1,field,{}),('integrated',-1,averaged,{}),('fixed',-1,averaged>=.5,{})]
        versions += [('matched',seed,*match_fraction(averaged,target,seed)) for seed in TIE_SEEDS]
        for stage,seed,observed,meta in versions:
            resolution=spacing if stage=='native' else factor*spacing
            axis=native if stage=='native' else lengths(observed,resolution)
            length=float(np.mean(axis)); fraction=float(observed.mean())
            rows.append(dict(**context,factor=factor,stage=stage,tie_seed=seed,
                length=length,length_ratio=length/ref if np.isfinite(ref) and ref>0 else np.nan,
                native_length=ref,voxel_over_native_length=factor*spacing/ref if np.isfinite(ref) and ref>0 else np.nan,
                native_fraction=target,observed_fraction=fraction,fraction_error=fraction-target,
                min_voxels_per_directional_length=float(np.min(np.asarray(axis)/resolution)),
                quantization_bound=meta.get('quantization_bound',np.nan),
                cutoff_ties=meta.get('cutoff_ties',0),ties_selected=meta.get('ties_selected',0),
                resolved=bool(np.all(np.isfinite(axis))),dimensions=field.ndim))
    return rows


def slope(t,a):
    if len(t)<4 or t[-1]/t[0]<5: return float('nan')
    x=np.log(t); x-=x.mean(); y=np.log(a.mean(axis=0))
    return float(x@(y-y.mean())/(x@x))


def fit_simulations(rows):
    fits=[]
    for c in (.5,.15):
        for factor in FACTORS:
            group=[r for r in rows if r['composition']==c and r['factor']==factor]
            ids=sorted(set(r['id'] for r in group)); times=np.array(sorted(set(r['sweep'] for r in group)))
            if len(ids)!=16: raise ValueError('Need all 16 trajectories')
            lookup={(r['id'],r['sweep'],r['stage'],r['tie_seed']):r['length'] for r in group}
            values={stage:np.array([[lookup[i,int(t),stage,-1] for t in times] for i in ids]) for stage in ('native','integrated','fixed')}
            tied=np.array([[[lookup[i,int(t),'matched',seed] for t in times] for i in ids] for seed in TIE_SEEDS])
            values['matched']=tied.mean(axis=0)
            common=np.all(np.isfinite(tied)&(tied>0),axis=(0,1))
            for a in values.values(): common &= np.all(np.isfinite(a)&(a>0),axis=0)
            for upper in (20000,200000):
                keep=common&(times>=1000)&(times<=upper); t=times[keep]
                reference=values['native'][:,keep]; alpha0=slope(t,reference)
                indices=np.random.default_rng(912).integers(16,size=(500,16))
                for stage in ('integrated','fixed','matched'):
                    a=values[stage][:,keep]; alpha=slope(t,a)
                    if np.isfinite(alpha):
                        deltas=[slope(t,a[ix])-slope(t,reference[ix]) for ix in indices]
                        low,high=np.percentile(deltas,[2.5,97.5])
                        tie_slopes=[slope(t,b[:,keep])-alpha0 for b in tied] if stage=='matched' else [np.nan]
                    else: low=high=np.nan; tie_slopes=[np.nan]
                    fits.append(dict(composition=c,factor=factor,stage=stage,nominal_t_max=upper,
                        retained_points=int(keep.sum()),actual_t_min=int(t[0]) if len(t) else '',actual_t_max=int(t[-1]) if len(t) else '',
                        native_alpha=alpha0,alpha=alpha,delta_alpha=alpha-alpha0,low=low,high=high,
                        tie_delta_min=min(tie_slopes),tie_delta_max=max(tie_slopes),independent_trajectories=16))
    return fits


def write_table(path,rows):
    with path.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def report(fits,external):
    def table(rows,columns):
        def fmt(v):
            if isinstance(v,float): return f'{v:.5g}' if np.isfinite(v) else 'unresolved / n.a.'
            return str(v)
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+escape(c)+'</th>' for c in columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(fmt(r[c]))+'</td>' for c in columns)+'</tr>' for r in rows)+'</tbody></table></div>'
    primary=[r for r in fits if r['factor']==4 and r['nominal_t_max']==20000]
    overview=[]
    for name in dict.fromkeys(r['id'] for r in external):
        for factor in FACTORS:
            for stage in ('integrated','fixed','matched'):
                group=[r for r in external if r['id']==name and r['factor']==factor and r['stage']==stage]
                ratios=np.array([r['length_ratio'] for r in group]); errors=np.array([r['fraction_error'] for r in group])
                overview.append(dict(scan=name,factor=factor,stage=stage,
                    length_ratio_mean=float(np.mean(ratios)),tie_ratio_min=float(np.min(ratios)),tie_ratio_max=float(np.max(ratios)),
                    fraction_error=float(errors.mean()),resolved=f'{np.isfinite(ratios).sum()}/{len(ratios)}'))
    return '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fraction matching: simulation and real-mask comparison</title><style>
body{background:#edf2f1;color:#17373d;font:16px/1.55 system-ui;margin:0}main{max-width:1150px;background:white;margin:24px auto;padding:30px;border-top:6px solid #187e7e}h1{line-height:1.15}h2{margin-top:30px}a{color:#176c72}.warning{background:#fff1d5;padding:16px}.scroll{overflow:auto;max-height:600px}table{border-collapse:collapse;font-size:13px}th,td{padding:9px;border-bottom:1px solid #ddd;white-space:nowrap;text-align:left}th{background:#e5efed;position:sticky;top:0}select{padding:8px}summary{cursor:pointer}</style></head><body><main>
<p>EXPLORATORY CONTROL STUDY · NOT AN ALLOY PREDICTOR</p>
<h1>Does matching the phase fraction recover the measurement?</h1>
<p>The binary control selects the highest-intensity coarse pixels until their count matches the native fraction as closely as the coarse grid permits. Five fixed spatial tie orderings are retained. This uses knowledge of the original fraction: it is an oracle control, not a new automatic segmentation method.</p>
<p class="warning">Two different outcomes are shown below: a <b>growth exponent</b> from 2D simulation trajectories, and a <b>static length ratio</b> from real 3D masks. They must not be numerically identified. Real phase volume fraction is not alloy chemical composition; the supplied masks are references, not independently verified truth.</p>
<h2>1. Primary simulation result</h2><p>Factor 4; nominal 1,000-20,000 sweeps; 16 complete trajectories per composition. The five tie outcomes are averaged within a trajectory, not treated as five independent experiments. Intervals use 500 paired trajectory resamples. Compare the magnitude of each delta with zero; no slope was tuned to 1/3.</p>'''+table(primary,['composition','stage','retained_points','actual_t_min','actual_t_max','native_alpha','alpha','delta_alpha','low','high','tie_delta_min','tie_delta_max'])+'''
<h2>2. External real-mask test</h2><p>Jonas Fell (2023), <a href="https://data.mendeley.com/datasets/hj9njz3rxp/1">Al-Ge nano-CT, Mendeley Data v1</a>, CC BY 4.0. The same four previously fixed 256-cubes are used, with 0.06 micrometre native voxels. No field was moved to improve the result. Ratios compare each processing choice with its own native box. A ratio of 1 means the same length, not a validated physical model. The ranges are tie sensitivity, not specimen confidence intervals.</p>'''+table(overview,['scan','factor','stage','length_ratio_mean','tie_ratio_min','tie_ratio_max','fraction_error','resolved'])+'''
<p>Sparse Ge and near-voxel lengths limit interpretation. Cross-time registration and representativeness have not been established, so no experimental growth exponent is fitted. A residual length error despite matching fraction tests the sufficiency of that control; it does not isolate a unique causal mechanism.</p>
<details><summary>All simulation sensitivity fits</summary>'''+table(fits,list(fits[0]))+'''</details>
<h2>Reproduce and inspect</h2><p><a href="simulation_fits.csv">All fitted comparisons</a> · <a href="simulation_observations.csv">Every simulated measurement</a> · <a href="external_observations.csv">Every real-mask measurement</a> · <a href="manifest.json">Provenance</a></p>
<p>This follows known processing effects and is not preregistered confirmation. The source protocol and literature-gap assessment define what is and is not claimed. Expert criticism, student verification and any outside pilot remain pending.</p>
</main></body></html>'''


def run(campaign,plan_path,output):
    if output.exists(): raise FileExistsError('Choose a new output directory')
    source=json.loads((campaign/'conservation_aware_holdout_v2/manifest.json').read_text())
    simulation=[]
    for name,digest in sorted(source['input_sha256'].items()):
        path=campaign/name
        if sha(path)!=digest: raise ValueError('Archived trajectory changed')
        with np.load(path,allow_pickle=False) as raw:
            config=json.loads(raw['config'].item())
            if config['L']!=128: raise ValueError('Unexpected size')
            snapshots=raw['snapshots']
            if np.any(snapshots.sum(axis=(1,2))!=int(raw['magnetization'])): raise ValueError('Composition not conserved')
            for t,snapshot in zip(raw['t'],snapshots):
                simulation.extend(observe((snapshot+1)/2,1.,dict(id=name,composition=config['concentration'],sweep=int(t),unit='lattice sites')))
        print('Measured',name,flush=True)
    fits=fit_simulations(simulation)
    plan=json.loads(plan_path.read_text()); external=[]; real_hashes={}
    for record in plan['records']:
        path=plan_path.parent/record['path']; digest=sha(path)
        if digest!=record['sha256']: raise ValueError('Experimental source changed')
        box=load_box(path,record['roi_zyx'])
        if not np.all((box==record['foreground'])|(box==record['background'])): raise ValueError('Undeclared labels; no replacement region allowed')
        if record['spacing_zyx']!=[.06]*3: raise ValueError('Unexpected physical calibration')
        external.extend(observe((box==record['foreground']).astype(float),.06,dict(id=record['id'],composition='not chemical composition',sweep='not a simulation',unit='um')))
        real_hashes[record['id']]=digest; print('Measured',record['id'],flush=True)
    output.mkdir(parents=True)
    for name,rows in [('simulation_fits.csv',fits),('simulation_observations.csv',simulation),('external_observations.csv',external)]: write_table(output/name,rows)
    (output/'report.html').write_text(report(fits,external))
    files=['fraction_matched_benchmark.py','fraction_matching.py','imaging.py','volume_metrology.py','volume_audit.py','metrology.py','FRACTION_MATCHED_PROTOCOL_2026-09-19.md']
    manifest=dict(status='Exploratory fraction-matched control; not external validation',
        simulation_input_sha256=source['input_sha256'],external_input_sha256=real_hashes,
        external_plan_sha256=sha(plan_path),external_records=[{k:v for k,v in r.items() if k!='path'} for r in plan['records']],
        sources={name:sha(ROOT/'research'/name) for name in files},
        factors=FACTORS,tie_seeds=TIE_SEEDS,simulation_rows=len(simulation),external_rows=len(external),fit_rows=len(fits),
        outputs={p.name:sha(p) for p in output.iterdir() if p.is_file()})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(output/'report.html')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('campaign',type=Path); p.add_argument('plan',type=Path)
    p.add_argument('--output',type=Path,required=True); a=p.parse_args(); run(a.campaign,a.plan,a.output)
