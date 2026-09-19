"""Frozen measurement stress test for development and fresh simulation cohorts."""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import numpy as np
from research.fraction_matching import integrate,match_fraction,TIE_SEEDS
from research.growth_reliability import measures,decimation_limit,paired_fit,tolerance_label
from research.volume_audit import sha

ROOT=Path(__file__).resolve().parents[1]
SOURCE_FILES=('research/audit_growth_reliability.py','research/growth_reliability.py',
    'research/imaging.py','research/metrology.py','research/fraction_matching.py',
    'research/GROWTH_RELIABILITY_PROTOCOL_2026-09-19.md',
    'research/plans/growth_reliability_holdout_v1.json','research/campaign.py',
    'model_b/kawasaki_engine.py')


def sources(): return {name:sha(ROOT/name) for name in SOURCE_FILES}


def write_csv(path,rows):
    with path.open('x',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def observe(field,context):
    rows=[]
    for factor in (2,4,8):
        for origin,(dy,dx) in enumerate(((0,0),(factor//2,0),(0,factor//2),(factor//2,factor//2))):
            shifted=np.roll(field,(-dy,-dx),axis=(0,1))
            native=measures(shifted)
            cap=decimation_limit(field.shape,native['near_zero_min'])
            grey=integrate(shifted,factor)
            versions=[('native',-1,shifted),('integrated',-1,grey),('fixed',-1,grey>=.5)]
            versions += [('matched',s,match_fraction(grey,float(shifted.mean()),s)[0]) for s in TIE_SEEDS]
            for stage,seed,a in versions:
                m=native if stage=='native' else measures(a,factor)
                rows.append(dict(**context,factor=factor,origin=origin,dy=dy,dx=dx,stage=stage,tie_seed=seed,
                    fraction_error=float(a.mean()-field.mean()),native_allowed_factor=cap,**m))
    return rows


def analyse(rows):
    fits=[]
    for c in (.5,.15):
        for factor in (2,4,8):
            for origin in range(4):
                group=[r for r in rows if r['composition']==c and r['factor']==factor and r['origin']==origin]
                ids=sorted(set(r['id'] for r in group));times=np.array(sorted(set(r['sweep'] for r in group)))
                lookup={(r['id'],r['sweep'],r['stage'],r['tie_seed']):r for r in group}
                def array(stage,seed,metric): return np.array([[lookup[i,int(t),stage,seed][metric] for t in times] for i in ids])
                if len(lookup)!=len(group): raise ValueError('Duplicate observations')
                caps=array('native',-1,'native_allowed_factor')
                for observable in ('half','lobe'):
                    values={stage:array(stage,-1,observable) for stage in ('native','integrated','fixed')}
                    tied=np.array([array('matched',s,observable) for s in TIE_SEEDS])
                    values['matched']=tied.mean(axis=0)
                    common=np.all(np.isfinite(tied)&(tied>0),axis=(0,1))
                    for a in values.values(): common &= np.all(np.isfinite(a)&(a>0),axis=0)
                    t=times[common];reference=values['native'][:,common]
                    for stage in ('integrated','fixed','matched'):
                        fit=paired_fit(t,reference,values[stage][:,common])
                        minimum=np.array([array(stage,s,'min_half_pixels') for s in TIE_SEEDS]) if stage=='matched' else array(stage,-1,'min_half_pixels')[None,:,:]
                        minimum=minimum[:,:,common]
                        valid=bool(np.isfinite(fit['delta']))
                        allowed=caps[:,common]
                        screen='unknown' if not valid or not np.all(np.isfinite(allowed)) else 'pass' if np.all(allowed>=factor) else 'flag'
                        observed='unknown' if not valid or not np.all(np.isfinite(minimum)) else 'pass' if np.all(minimum>=3) else 'flag'
                        fits.append(dict(composition=c,factor=factor,origin=origin,observable=observable,stage=stage,
                            trajectories=len(ids),available_points=len(times),retained_points=len(t),
                            first_sweep=int(t[0]) if len(t) else '',last_sweep=int(t[-1]) if len(t) else '',
                            **fit,tolerance_label=tolerance_label(fit['low'],fit['high']),
                            directional_02_adaptation=screen,observed_three_pixel_screen=observed,
                            min_treatment_half_pixels=float(minimum.min()) if minimum.size else np.nan))
    return fits


def render(fits,cohort):
    def table(selected,columns):
        def fmt(v):
            if isinstance(v,float): return f'{v:.5g}' if np.isfinite(v) else 'unresolved'
            return str(v)
        return '<div class="scroll"><table><tr>'+''.join('<th>'+escape(k)+'</th>' for k in columns)+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(fmt(r[k]))+'</td>' for k in columns)+'</tr>' for r in selected)+'</table></div>'
    primary=[r for r in fits if r['origin']==0 and r['factor']==4 and r['stage']=='matched']
    counts=[]
    # Half-height, origin zero only: still correlated cases, not independent trials.
    for rule in ('directional_02_adaptation','observed_three_pixel_screen'):
        cases=[r for r in fits if r['origin']==0 and r['observable']=='half']
        passed=[r for r in cases if r[rule]=='pass']
        counts.append(dict(screen=rule,cases=len(cases),passing=len(passed),
            pass_outside=sum(r['tolerance_label']=='outside' for r in passed),
            pass_uncertain=sum(r['tolerance_label']=='uncertain' for r in passed),
            flagged_within=sum(r[rule]=='flag' and r['tolerance_label']=='within' for r in cases),
            unknown=sum(r[rule]=='unknown' for r in cases)))
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Growth measurement reliability</title><style>body{font:16px/1.55 system-ui;background:#edf2f1;color:#17373d;margin:0}main{max-width:1150px;margin:24px auto;background:white;padding:30px;border-top:6px solid #187e7e}.warning{background:#fff1d5;padding:16px}.scroll{overflow:auto;max-height:70vh}table{border-collapse:collapse;font-size:13px}th,td{padding:9px;border-bottom:1px solid #ddd;white-space:nowrap}th{background:#e5efed}h1{line-height:1.1}</style></head><body><main>
<p>INTERNAL RESEARCH CHECK · '''+escape(cohort)+'''</p><h1>When does image processing change a growth estimate?</h1>
<p class="warning">No new physical exponent or novel method is claimed. The slope of the log length ratio equals the difference of fitted exponents by algebra; confirming it is verification, not independent prediction. The published-method comparison is a directional-covariance adaptation, not the full multi-descriptor method.</p>
<h2>Primary factor-4 fraction-matched comparison</h2><p>Primary observable: half-height; positive-lobe integral is secondary. Nominal 1,000–20,000 sweeps. Intervals resample whole paired trajectories 1,000 times. Different retained windows limit cross-observable comparisons.</p>'''+table(primary,['composition','observable','trajectories','retained_points','first_sweep','last_sweep','native_alpha','alpha','delta','low','high','ratio_first','ratio_last','tolerance_label'])+'''
<h2>Do the fixed warning screens have useful coverage?</h2><p>The table includes 18 correlated comparisons: two compositions, three reduction factors, three treatments, origin zero, half-height. Cases share data. Zero passing cases is no coverage, not a perfect predictor. A numerical tolerance of ±0.02 is a declared benchmark choice, not an accepted industrial tolerance. A failure of the adapted screen cannot refute the original published criterion.</p>'''+table(counts,list(counts[0]))+'''
<h2>Every sensitivity result</h2><p>Four block-grid origins, two observables, three factors, all treatments. Translation also moves the finite observation window; these two origin effects are not isolated. Unknown and unresolved outcomes are retained.</p>'''+table(fits,list(fits[0]))+'''
<p><a href="fits.csv">All fit results</a> · <a href="observations.csv">Every checkpoint and tie</a> · <a href="manifest.json">Provenance</a></p>
<p>This is AI-assisted internal verification. Student understanding, full prior-method comparison and outside criticism remain necessary. Static real-alloy masks cannot validate a dynamic exponent.</p></main></body></html>'''


def run(campaign,output,cohort,freeze=None):
    if output.exists(): raise FileExistsError('Choose a new output directory')
    if cohort=='fresh':
        if freeze is None: raise ValueError('Fresh cohort requires pre-generation freeze')
        frozen=json.loads(freeze.read_text())
        if frozen['sources']!=sources(): raise ValueError('Frozen analysis changed; do not relabel as prospective')
    manifest=json.loads((campaign/'manifest.json').read_text());plan=manifest['identity']['plan']
    if plan['concentrations']!=[.5,.15] or plan['Jx']!=1 or plan['Jy']!=1 or plan['T_final_over_tc']!=.65:
        raise ValueError('Unexpected campaign conditions')
    if cohort=='fresh' and plan!=json.loads((ROOT/'research/plans/growth_reliability_holdout_v1.json').read_text()):
        raise ValueError('Fresh plan mismatch')
    rows=[];input_hashes={}
    for ci,c in enumerate(plan['concentrations']):
        for rep in range(plan['replicas']):
            path=campaign/f'c{ci}_L128_rep{rep:03d}.npz'
            input_hashes[path.name]=sha(path)
            with np.load(path,allow_pickle=False) as raw:
                config=json.loads(raw['config'].item())
                if config['L']!=128 or config['concentration']!=c or raw['t'][-1]!=plan['max_sweeps']:
                    raise ValueError('Unexpected raw configuration')
                if np.any(raw['snapshots'].sum(axis=(1,2))!=int(raw['magnetization'])): raise ValueError('Conservation failed')
                keep=(raw['t']>=1000)&(raw['t']<=20000)
                for t,s in zip(raw['t'][keep],raw['snapshots'][keep]):
                    rows.extend(observe((s+1)/2,dict(id=path.name,composition=c,sweep=int(t))))
            print('Measured',cohort,path.name,flush=True)
    fits=analyse(rows);output.mkdir(parents=True)
    write_csv(output/'observations.csv',rows);write_csv(output/'fits.csv',fits)
    (output/'report.html').write_text(render(fits,cohort))
    result=dict(cohort=cohort,status='complete',sources=sources(),input_sha256=input_hashes,
        campaign_manifest_sha256=sha(campaign/'manifest.json'),freeze_sha256=sha(freeze) if freeze else None,
        observations=len(rows),fit_rows=len(fits),independent_replica_count=len(input_hashes),
        max_identity_error=max(r['identity_error'] for r in fits if np.isfinite(r['identity_error'])),
        outputs={name:sha(output/name) for name in ('observations.csv','fits.csv','report.html')})
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(output/'report.html')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('campaign',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cohort',choices=('development','fresh'),required=True);p.add_argument('--freeze',type=Path)
    a=p.parse_args();run(a.campaign,a.output,a.cohort,a.freeze)
