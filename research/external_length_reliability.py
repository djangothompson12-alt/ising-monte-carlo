"""Static 3D companion with two lengths and explicit resolution warnings.

No kinetic diagnostic, no 3D reproduction of the 2D literature criterion.
"""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import numpy as np
from research.fraction_matching import integrate,match_fraction,TIE_SEEDS
from research.growth_reliability import correlation_measures
from research.volume_metrology import axis_correlations
from research.volume_audit import load_box,sha,required_text


def measure(field,spacing): return correlation_measures(axis_correlations(field),spacing)


def render(plan,rows):
    columns=('id','factor','stage','half','lobe','half_ratio','lobe_ratio','fraction_error','min_half_pixels','three_pixel_warning')
    def fmt(value):
        if isinstance(value,float):return f'{value:.5g}' if np.isfinite(value) else 'unresolved'
        return str(value)
    summaries=[]
    for case in dict.fromkeys(r['id'] for r in rows):
        for factor in (2,4,8):
            for stage in ('native','integrated','fixed','matched'):
                group=[r for r in rows if r['id']==case and r['factor']==factor and r['stage']==stage]
                out=dict(id=case,factor=factor,stage=stage)
                for key in ('half','lobe','half_ratio','lobe_ratio','fraction_error'):
                    out[key]=float(np.mean([r[key] for r in group]))
                out['min_half_pixels']=float(np.min([r['min_half_pixels'] for r in group]))
                out['three_pixel_warning']='unknown' if not np.isfinite(out['min_half_pixels']) else 'flag' if out['min_half_pixels']<3 else 'no flag'
                summaries.append(out)
    table='<div class="scroll"><table><tr>'+''.join('<th>'+escape(c)+'</th>' for c in columns)+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(fmt(r[c]))+'</td>' for c in columns)+'</tr>' for r in summaries)+'</table></div>'
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>External length reliability</title><style>body{font:16px/1.55 system-ui;background:#edf2f1;color:#17373d;margin:0}main{max-width:1150px;margin:24px auto;padding:30px;background:white;border-top:6px solid #187e7e}.scroll{overflow:auto;max-height:70vh}th,td{padding:9px;border-bottom:1px solid #ddd;white-space:nowrap}table{border-collapse:collapse;font-size:13px}th{background:#e5efed}.warning{padding:16px;background:#fff1d5}</style></head><body><main><p>STATIC REAL-MASK AUDIT · LOCAL PROTOTYPE</p><h1>Does the conclusion depend on the length definition?</h1>
<p class="warning">A supplied segmentation is a reference, not independent physical truth. This report cannot validate an ageing exponent. The three-pixel screen is a deliberately conservative heuristic; no flag does not establish accuracy. Our simulation test found it can reject cases with small exponent differences.</p>
<p>Source: '''+escape(plan['source'])+'<br>Rights: '+escape(plan['license'])+'''</p><p>Half = mean directional correlation half-height; lobe = mean directional area up to the first zero. Lengths use each record's declared physical unit; ratios use the corresponding native measure. They are distinct observables, not particle radii. Missing zero crossings remain unresolved.</p>'''+table+'''
<p>Matched entries average five tie orderings, not independent specimens. The download retains every tie outcome. No experimental edges are wrapped, no boxes moved, and no kinetic fit is performed. Below one voxel, a crossing is interpolated at an inadequately resolved scale.</p>
<p><a href="observations.csv">Every measurement</a> · <a href="manifest.json">Calibration, region declarations and provenance</a></p></main></body></html>'''


def run(plan_path,output):
    if output.exists():raise FileExistsError('Choose a new output folder')
    plan=json.loads(plan_path.read_text())
    for key in ('source','license'):required_text(plan,key)
    if not isinstance(plan.get('records'),list) or not plan['records']:raise ValueError('Records required')
    records=[];rows=[];ids=set()
    for record in plan['records']:
        for key in ('id','path','specimen','unit','roi_reason','phase_definition','mask_authority'):required_text(record,key)
        if record['id'] in ids:raise ValueError('Duplicate id')
        ids.add(record['id'])
        spacing=np.asarray(record['spacing_zyx'],dtype=float)
        if spacing.shape!=(3,) or not np.all(np.isfinite(spacing)&(spacing>0)) or not np.all(spacing==spacing[0]):
            raise ValueError('Equal positive voxel spacings required')
        fg,bg=record['foreground'],record['background']
        if any(isinstance(v,bool) or not isinstance(v,int) for v in (fg,bg)) or fg==bg:raise ValueError('Two integer labels required')
        path=plan_path.parent/record['path'];digest=sha(path)
        if record.get('sha256') and record['sha256']!=digest:raise ValueError('Source changed')
        labels=load_box(path,record['roi_zyx'])
        if any(n%8 for n in labels.shape) or not np.all((labels==fg)|(labels==bg)):raise ValueError('Invalid box or labels')
        field=(labels==fg).astype(float);native=measure(field,float(spacing[0]))
        for factor in (2,4,8):
            grey=integrate(field,factor)
            versions=[('native',-1,field),('integrated',-1,grey),('fixed',-1,grey>=.5)]
            versions += [('matched',s,match_fraction(grey,float(field.mean()),s)[0]) for s in TIE_SEEDS]
            for stage,seed,a in versions:
                m=native if stage=='native' else measure(a,float(spacing[0])*factor)
                ratios={key+'_ratio':m[key]/native[key] if np.isfinite(native[key]) and native[key]>0 else np.nan for key in ('half','lobe')}
                rows.append(dict(id=record['id'],unit=record['unit'],factor=factor,stage=stage,tie_seed=seed,
                    native_fraction=float(field.mean()),fraction_error=float(a.mean()-field.mean()),**m,**ratios))
        records.append({**{k:v for k,v in record.items() if k!='path'},'sha256':digest})
        print('Measured',record['id'],flush=True)
    output.mkdir(parents=True)
    with (output/'observations.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (output/'report.html').write_text(render(plan,rows))
    source_names=('external_length_reliability.py','growth_reliability.py','volume_metrology.py','metrology.py','fraction_matching.py','volume_audit.py')
    manifest=dict(source=plan['source'],license=plan['license'],records=records,input_plan_sha256=sha(plan_path),
        source_sha256={name:sha(Path(__file__).with_name(name)) for name in source_names},
        outputs={name:sha(output/name) for name in ('observations.csv','report.html')},rows=len(rows),
        boundary='Static sensitivity only; no validated kinetic reliability claim or outside adoption')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(output/'report.html')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.plan,a.output)
