"""Verify the new control's archived tables and render its fixed comparison."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research.volume_audit import sha


def read(path):
    with path.open() as stream: return list(csv.DictReader(stream))


def run(source,output):
    if output.exists(): raise FileExistsError('Choose new summary output')
    manifest=json.loads((source/'manifest.json').read_text())
    for name,digest in manifest['outputs'].items():
        if sha(source/name)!=digest: raise ValueError('Benchmark output changed')
    sim=read(source/'simulation_observations.csv'); real=read(source/'external_observations.csv'); fits=read(source/'simulation_fits.csv')
    if (len(sim),len(real),len(fits))!=(57600,96,36): raise ValueError('Incomplete table inventory')
    unique={(r['id'],r['sweep'],r['factor'],r['stage'],r['tie_seed']) for r in sim}
    if len(unique)!=len(sim): raise ValueError('Duplicate observation rows')
    for r in sim+real:
        err=abs(float(r['fraction_error']))
        if r['stage'] in ('native','integrated') and err>1e-12: raise ValueError('Mean preservation failed')
        if r['stage']=='matched' and err>float(r['quantization_bound'])+1e-12: raise ValueError('Count constraint failed')
    # Compare old native/fixed fits only when both analyses retained identical ranges.
    old=read(Path('research/runs/main_065_multisize_v1/conservation_aware_holdout_v2/paired_fits.csv'))
    for r in fits:
        if r['factor']!='4' or r['stage']!='fixed': continue
        reference=next(x for x in old if x['composition']==r['composition'] and x['nominal_t_max']==r['nominal_t_max'] and x['comparison']=='segmented-minus-native')
        if all(r[k]==reference[k] for k in ('actual_t_min','actual_t_max','retained_points')):
            np.testing.assert_allclose(float(r['delta_alpha']),float(reference['delta_alpha']),atol=1e-12)
    output.mkdir(parents=True)
    fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained',sharey=True)
    for ax,c in zip(axes,['0.5','0.15']):
        for stage,offset,color in [('integrated',-.12,'#278a8a'),('fixed',0,'#b66828'),('matched',.12,'#69529c')]:
            selected=[r for r in fits if r['composition']==c and r['stage']==stage and r['nominal_t_max']=='20000']
            for j,r in enumerate(selected):
                if np.isfinite(float(r['delta_alpha'])):
                    ax.vlines(j+offset,float(r['low']),float(r['high']),color=color)
                    ax.plot(j+offset,float(r['delta_alpha']),'o',color=color,label=stage if j==0 else None)
        ax.axhline(0,color='grey',ls=':'); ax.set(xticks=range(3),xticklabels=['2x','4x','8x'],xlabel='Voxel / pixel averaging factor',title='Simulation c = '+c)
        ax.grid(axis='y',alpha=.2); ax.legend(fontsize=8)
    axes[0].set_ylabel('Effective exponent minus native exponent')
    fig.suptitle('Fraction matching is a control, not a guarantee of recovered kinetics',fontsize=12)
    fig.savefig(output/'simulation_control.png',dpi=180); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
    summary=[]
    ids=list(dict.fromkeys(r['id'] for r in real))
    for index,name in enumerate(ids):
        for stage,offset,color in [('fixed',-.08,'#b66828'),('matched',.08,'#69529c')]:
            group=[r for r in real if r['id']==name and r['stage']==stage and r['factor']=='4']
            ratio=np.array([float(r['length_ratio']) for r in group]); err=np.array([float(r['fraction_error']) for r in group])
            axes[0].plot(index+offset,ratio.mean(),'o',color=color,label=stage if index==0 else None)
            axes[0].vlines(index+offset,ratio.min(),ratio.max(),color=color)
            axes[1].plot(index+offset,100*err.mean(),'o',color=color,label=stage if index==0 else None)
            summary.append(dict(scan=name,stage=stage,factor=4,length_ratio_mean=float(ratio.mean()),tie_min=float(ratio.min()),tie_max=float(ratio.max()),fraction_error=float(err.mean())))
    for ax in axes:
        ax.set(xticks=range(4),xticklabels=['15 min','105 min','195 min','315 min'],xlabel='Scan identifier, not a kinetic fit'); ax.legend(fontsize=8); ax.grid(axis='y',alpha=.2)
    axes[0].axhline(1,color='grey',ls=':'); axes[0].set_ylabel('Static length / native length')
    axes[1].axhline(0,color='grey',ls=':'); axes[1].set_ylabel('Phase volume fraction error (percentage points)')
    fig.suptitle('Real Al-Ge masks at 4x reduction | ranges are tie choices, not specimen CIs',fontsize=11)
    fig.savefig(output/'external_control.png',dpi=180); plt.close(fig)
    result=dict(status='passed',simulation_rows=len(sim),external_rows=len(real),fit_rows=len(fits),
        primary=[r for r in fits if r['factor']=='4' and r['nominal_t_max']=='20000'],external_factor4=summary,
        input_manifest_sha256=sha(source/'manifest.json'),summary_source_sha256=sha(Path(__file__)),
        figures_sha256={p.name:sha(p) for p in output.glob('*.png')})
    (output/'verification_and_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('source',type=Path); p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); run(args.source,args.output)
