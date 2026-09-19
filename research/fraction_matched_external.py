"""Standalone owner-mask intake for the fraction-matched static audit.

Uses the same operators as the simulation comparison; never fits real kinetics.
"""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import numpy as np
from research.fraction_matched_benchmark import observe
from research.volume_audit import load_box,sha,required_text


def render(plan,rows):
    summaries=[]
    for record in plan['records']:
        for factor in (2,4,8):
            for stage in ('integrated','fixed','matched'):
                group=[r for r in rows if r['id']==record['id'] and r['factor']==factor and r['stage']==stage]
                ratios=np.array([r['length_ratio'] for r in group]); fractional=np.array([r['fraction_error'] for r in group])
                summaries.append(dict(id=record['id'],factor=factor,stage=stage,
                    native_length=group[0]['native_length'],unit=group[0]['unit'],
                    mean_ratio=float(ratios.mean()),tie_min=float(ratios.min()),tie_max=float(ratios.max()),
                    fraction_error=float(fractional.mean()),native_fraction=group[0]['native_fraction'],
                    min_voxels_per_length=min(r['min_voxels_per_directional_length'] for r in group)))
    columns=list(summaries[0])
    def fmt(value):
        return f'{value:.5g}' if isinstance(value,float) and np.isfinite(value) else 'unresolved' if isinstance(value,float) else str(value)
    table='<table><thead><tr>'+''.join('<th>'+escape(c)+'</th>' for c in columns)+'</tr></thead><tbody>'
    for row in summaries:
        table+='<tr data-case="'+escape(row['id'],quote=True)+'">'+''.join('<td>'+escape(fmt(row[c]))+'</td>' for c in columns)+'</tr>'
    table+='</tbody></table>'
    options=''.join('<option>'+escape(r['id'])+'</option>' for r in plan['records'])
    context=''.join('<li><b>'+escape(r['id'])+'</b>: '+escape(r['phase_definition'])+'; '+escape(r['mask_authority'])+'; spacing '+escape(str(r['spacing_zyx']))+' '+escape(r['unit'])+'; ROI '+escape(str(r['roi_zyx']))+'. '+escape(r['roi_reason'])+'</li>' for r in plan['records'])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Known-fraction mask audit</title><style>
body{font:16px/1.6 system-ui;background:#edf2f1;color:#17373d;margin:0}main{max-width:1150px;padding:30px;margin:24px auto;background:white;border-top:6px solid #187e7e}h1{line-height:1.15}.warning{background:#fff1d5;padding:16px}.scroll{overflow:auto;max-height:65vh}table{border-collapse:collapse;font-size:13px}th,td{padding:9px;border-bottom:1px solid #ddd;white-space:nowrap;text-align:left}th{position:sticky;top:0;background:#e5efed}a{color:#176c72}select{padding:8px}</style></head><body><main>
<p>LOCAL RESEARCH PROTOTYPE · SUPPLIED PHASE MASKS</p><h1>Same fraction. Same measured length?</h1>
<p>Compare your reference mask with partial-volume averaging, a fixed 0.5 threshold, and a binary mask constrained to the nearest attainable reference phase fraction. All comparisons use the same selected field.</p>
<p class="warning">This is an oracle control: the reference phase fraction is supplied by the original mask. It does not independently establish true composition or correct segmentation. Matching is limited by the coarse pixel count. Tie ranges are algorithmic sensitivity, not confidence intervals or independent specimens.</p>
<p><b>Source:</b> '''+escape(plan['source'])+'<br/><b>Rights:</b> '+escape(plan['license'])+'''</p>
<h2>Read the result</h2><p>A length ratio of 1 means unchanged measured correlation length. Compare that ratio with the phase-fraction error: making the latter small need not make the former close to 1. “Min voxels per length” below 1 means at least one directional crossing lies below a coarse voxel; interpolation is not recovered spatial information. Missing results remain unresolved.</p>
<p>Show <select id="case"><option value="">All supplied fields</option>'''+options+'''</select> · <a href="observations.csv">Every measurement and tie seed</a> · <a href="manifest.json">Source hashes and declarations</a></p>
<div class="scroll">'''+table+'''</div><h2>Field declarations</h2><ul>'''+context+'''</ul>
<p>No experimental coarsening exponent or property prediction is fitted. Fractions are geometrical volume fractions, not necessarily chemical compositions. No cross-time registration or specimen representativeness is assumed. Ask the data owner whether the length is relevant and what error matters before calling this useful.</p>
<script>document.getElementById('case').addEventListener('change',function(){document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!!this.value&&r.dataset.case!==this.value)});</script></main></body></html>'''


def run(plan_path,output):
    if output.exists(): raise FileExistsError('Choose a new output directory')
    plan=json.loads(plan_path.read_text())
    for name in ('source','license'): required_text(plan,name)
    if not isinstance(plan.get('records'),list) or not plan['records']: raise ValueError('Declare records')
    observations=[]; records=[]; ids=set()
    for r in plan['records']:
        for name in ('id','specimen','path','unit','roi_reason','phase_definition','mask_authority'): required_text(r,name)
        if r['id'] in ids: raise ValueError('Duplicate ID')
        ids.add(r['id'])
        spacing=np.asarray(r['spacing_zyx'],dtype=float)
        if spacing.shape!=(3,) or not np.all(np.isfinite(spacing)&(spacing>0)) or not np.all(spacing==spacing[0]):
            raise ValueError('This prototype requires equal positive z/y/x voxel spacing; do not relabel anisotropic data')
        fg,bg=r['foreground'],r['background']
        if any(isinstance(v,bool) or not isinstance(v,int) for v in (fg,bg)) or fg==bg: raise ValueError('Declare two different integer labels')
        path=plan_path.parent/r['path']; digest=sha(path)
        if r.get('sha256') and digest!=r['sha256']: raise ValueError('Source hash mismatch')
        labels=load_box(path,r['roi_zyx'])
        if any(n%8 for n in labels.shape): raise ValueError('ROI sides must be divisible by eight')
        if not np.all((labels==fg)|(labels==bg)): raise ValueError('ROI contains undeclared labels; no silent replacement')
        observations.extend(observe((labels==fg).astype(float),float(spacing[0]),dict(id=r['id'],specimen=r['specimen'],unit=r['unit'])))
        records.append({**{k:v for k,v in r.items() if k!='path'},'sha256':digest})
    output.mkdir(parents=True)
    with (output/'observations.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(observations[0])); writer.writeheader(); writer.writerows(observations)
    (output/'report.html').write_text(render(plan,observations))
    names=('fraction_matched_external.py','fraction_matched_benchmark.py','fraction_matching.py','volume_metrology.py','volume_audit.py','metrology.py','imaging.py')
    manifest=dict(source=plan['source'],license=plan['license'],records=records,input_plan_sha256=sha(plan_path),
        sources={name:sha(Path(__file__).with_name(name)) for name in names},rows=len(observations),
        outputs={name:sha(output/name) for name in ('observations.csv','report.html')},
        boundary='Static oracle-control audit, not kinetics or independent experimental validation')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return output/'report.html'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('plan',type=Path); p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); print(run(args.plan,args.output))
