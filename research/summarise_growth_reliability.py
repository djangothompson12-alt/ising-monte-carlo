"""Make a compact review brief from completed, hash-checked analyses."""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research.volume_audit import sha


def read(path):
    with path.open() as f:return list(csv.DictReader(f))


def load(folder):
    m=json.loads((folder/'manifest.json').read_text())
    for name,digest in m['outputs'].items():
        if sha(folder/name)!=digest:raise ValueError('Analysis outputs changed')
    return read(folder/'fits.csv'),read(folder/'observations.csv'),m


def run(development,fresh,external,output):
    if output.exists():raise FileExistsError('Choose a new summary directory')
    cohorts={};provenance={}
    for name,path in [('development',development),('fresh',fresh)]:
        fits,observations,manifest=load(path);cohorts[name]=(fits,observations)
        provenance[name]=sha(path/'manifest.json')
        if manifest['cohort']!=name:raise ValueError('Cohort label mismatch')
    real_manifest=json.loads((external/'manifest.json').read_text())
    for name,digest in real_manifest['outputs'].items():
        if sha(external/name)!=digest:raise ValueError('External output changed')
    output.mkdir(parents=True)
    primary=[];screens=[];origin_ranges=[]
    for cohort,(fits,observations) in cohorts.items():
        for r in fits:
            if r['factor']=='4' and r['origin']=='0' and r['stage']=='matched':primary.append(dict(cohort=cohort,**r))
        for rule in ('directional_02_adaptation','observed_three_pixel_screen'):
            selected=[r for r in fits if r['origin']=='0' and r['observable']=='half']
            passed=[r for r in selected if r[rule]=='pass']
            screens.append(dict(cohort=cohort,screen=rule,cases=len(selected),passes=len(passed),
                pass_outside=sum(r['tolerance_label']=='outside' for r in passed),
                flagged_within=sum(r[rule]=='flag' and r['tolerance_label']=='within' for r in selected),
                unknown=sum(r[rule]=='unknown' for r in selected)))
        for c in ('0.5','0.15'):
            for observable in ('half','lobe'):
                selected=[r for r in fits if r['factor']=='4' and r['stage']=='matched' and r['composition']==c and r['observable']==observable]
                deltas=[float(r['delta']) for r in selected]
                origin_ranges.append(dict(cohort=cohort,composition=c,observable=observable,
                    minimum=min(deltas),maximum=max(deltas),all_outside=all(r['tolerance_label']=='outside' for r in selected)))
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,c in zip(axes,('0.5','0.15')):
        for cohort,(fits,observations) in cohorts.items():
            selected=[r for r in observations if r['composition']==c and r['factor']=='4' and r['origin']=='0']
            times=sorted(set(int(r['sweep']) for r in selected))
            ratios=[]
            for t in times:
                native=[float(r['half']) for r in selected if int(r['sweep'])==t and r['stage']=='native']
                matched=[float(r['half']) for r in selected if int(r['sweep'])==t and r['stage']=='matched']
                # Exactly five entries per trajectory, so this is equal-weight tie/replica averaging.
                ratios.append(np.mean(matched)/np.mean(native))
            ax.plot(times,ratios,'o-',ms=3,label=cohort)
        ax.axhline(1,color='grey',ls=':');ax.set(xscale='log',xlabel='Monte Carlo sweeps',ylabel='Matched / native mean half-height length',title='Composition '+c);ax.legend()
    fig.suptitle('Time-dependent length distortion | factor 4, origin zero')
    fig.savefig(output/'length_ratio.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained',sharey=True)
    for ax,c in zip(axes,('0.5','0.15')):
        for cohort,offset in [('development',-.12),('fresh',.12)]:
            fits=cohorts[cohort][0]
            for observable,color in [('half','#257d8c'),('lobe','#a6602a')]:
                selected=[r for r in fits if r['composition']==c and r['factor']=='4' and r['stage']=='matched' and r['observable']==observable]
                xs=[int(r['origin'])+offset for r in selected];ys=[float(r['delta']) for r in selected]
                ax.plot(xs,ys,'o-' if cohort=='fresh' else 's--',color=color,label=observable+' / '+cohort)
                for x,r in zip(xs,selected):ax.vlines(x,float(r['low']),float(r['high']),color=color,alpha=.5)
        ax.axhspan(-.02,.02,color='grey',alpha=.12);ax.axhline(0,color='grey',ls=':')
        ax.set(xticks=range(4),xlabel='Declared origin index',title='Composition '+c);ax.legend(fontsize=7)
    axes[0].set_ylabel('Fraction-matched minus native exponent')
    fig.suptitle('Second observable and grid-origin sensitivity | factor 4')
    fig.savefig(output/'origin_observable.png',dpi=170);plt.close(fig)
    def table(rows,columns):
        def fmt(value):
            try:return f'{float(value):.5g}'
            except (ValueError,TypeError):return str(value)
        return '<div class="scroll"><table><tr>'+''.join('<th>'+escape(k)+'</th>' for k in columns)+'</tr>'+''.join('<tr>'+''.join('<td>'+escape(fmt(r[k]))+'</td>' for k in columns)+'</tr>' for r in rows)+'</table></div>'
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Independent measurement check — review brief</title><style>body{background:#edf2f1;color:#17373d;font:16px/1.6 system-ui;margin:0}main{max-width:1000px;margin:24px auto;padding:32px;background:white;border-top:6px solid #187e7e}h1{line-height:1.15}.warning{padding:16px;background:#fff1d5}img{width:100%;height:auto}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px}th,td{padding:8px;border-bottom:1px solid #ddd;white-space:nowrap}</style></head><body><main>
<p>AI-ASSISTED WORKING BRIEF · FOR STUDENT CHECKING AND TECHNICAL CRITICISM</p>
<h1>Independent checks of a growth measurement</h1>
<p>Question: after reducing the resolution of conserved Kawasaki images, is matching the original composition enough to preserve a finite-window growth estimate? Can fixed resolution warnings identify reliable estimates?</p>
<p>Design: 32 previously analysed development trajectories and 16 fresh, independently seeded L=128 trajectories (eight per composition). The new batch ran to 20,000 sweeps, with the protocol, numerical tolerance and analysis-source hashes fixed before generation. This is a short-window measurement test, not an asymptotic growth-law or finite-size-saturation experiment.</p>
<h2>Results that can be checked</h2>'''+table(primary,['cohort','composition','observable','trajectories','delta','low','high','first_sweep','last_sweep'])+'''
<p>Intervals use 1,000 paired whole-trajectory bootstrap draws. Half-height is primary; positive-lobe integral is a second definition. Neither is a particle radius or a known true exponent.</p><img src="length_ratio.png" alt="Length distortion through time"><p>The changing length ratio accounts algebraically for the exponent shift. That identity is a numerical check, not a novel theory or independent causal explanation.</p><img src="origin_observable.png" alt="Origin and observable sensitivity">
<h2>Do the fixed screens have useful coverage?</h2>'''+table(screens,['cohort','screen','cases','passes','pass_outside','flagged_within','unknown'])+'''
<p class="warning">Zero passes means no useful acceptance coverage, not perfect prediction. Cases share trajectories. The three-pixel screen is a chosen heuristic. The directional .02 screen adapts only part of <a href="https://arxiv.org/abs/1712.03183">Ledesma-Alonso et al. (2018)</a>; it omits the full set of descriptors and cannot refute their published method. No new diagnostic is validated here.</p>
<h2>Materials link and its boundary</h2><p>The companion applies two length definitions to fixed public 3D Al-Ge masks. It tests static measurement sensitivity, not whether the 2D model predicts real ageing. Native masks are assumed references; sparse phases, sub-voxel lengths and unverified representativeness limit interpretation.</p>
<h2>Specific criticism requested</h2><ol><li>Does this dynamic, paired benchmark add a useful increment beyond existing image-resolution studies?</li><li>What faithful multi-descriptor comparison and more realistic observation model are needed before claiming a useful diagnostic?</li><li>Is there an owner-defined imaging decision for which this static tool would be worth testing?</li></ol>
<p>Current verdict: reproducible internal evidence, with new-seed replication and a negative screening result. Novelty, publication suitability, outside usefulness and student mastery are not established. No endorsement is implied.</p><p><a href="summary.json">Exact results and provenance</a></p></main></body></html>'''
    (output/'review_brief.html').write_text(html)
    result=dict(primary=primary,screens=screens,origin_ranges=origin_ranges,input_manifests=provenance,
        external_manifest_sha256=sha(external/'manifest.json'),summary_source_sha256=sha(Path(__file__)),
        outputs={p.name:sha(p) for p in output.iterdir() if p.is_file()})
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('development','fresh','external'):p.add_argument(name,type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.development,a.fresh,a.external,a.output)
