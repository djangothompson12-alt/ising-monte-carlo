"""Three fixed reviewer figures; no refitting or selection of favourable rows."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def rows(path):
    with path.open() as f: return list(csv.DictReader(f))


def build(analysis, volumes, output):
    if output.exists(): raise FileExistsError('Choose a new figure directory')
    output.mkdir(parents=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fits=rows(analysis/'paired_fits.csv')
    colors=['#167a83','#ad5725']
    fig,axes=plt.subplots(1,2,figsize=(9,3.3),layout='constrained',sharex=True)
    names=['integrated-minus-native','segmented-minus-integrated','segmented-minus-native']
    labels=['Averaging - native','Segmentation - averaging','Combined - native']
    for ax,c,color in zip(axes,[.5,.15],colors):
        for i,name in enumerate(names):
            r=next(r for r in fits if float(r['composition'])==c and r['comparison']==name and int(r['nominal_t_max'])==20000)
            ax.plot([float(r['delta_low']),float(r['delta_high'])],[i,i],color=color,lw=2)
            ax.plot(float(r['delta_alpha']),i,'o',color=color)
        ax.axvline(0,color='grey',ls=':',lw=1)
        ax.set(yticks=range(3),yticklabels=labels,title=f'c = {c:.2f}; 16 trajectories',xlabel='Difference in effective exponent')
        ax.invert_yaxis(); ax.grid(axis='x',alpha=.15)
    fig.suptitle('Paired processing-stage differences | actual window 1,091-17,913 sweeps',fontsize=11)
    fig.savefig(output/'figure1_stage_differences.png',dpi=200); plt.close(fig)

    obs=rows(analysis/'per_checkpoint.csv')
    fig,axes=plt.subplots(1,2,figsize=(9,3.3),layout='constrained',sharey=True)
    for ax,c,color in zip(axes,[.5,.15],colors):
        selected=[r for r in obs if float(r['composition'])==c]
        times=np.array(sorted(set(int(r['sweep']) for r in selected)))
        files=sorted(set(r['file'] for r in selected))
        lookup={(r['file'],int(r['sweep'])):r for r in selected}
        shift=np.array([[100*float(lookup[f,int(t)]['segmented_fraction_shift']) for t in times] for f in files])
        samples=np.random.default_rng(912).integers(len(files),size=(500,len(files)))
        boot=shift[samples].mean(axis=1); lo,hi=np.percentile(boot,[2.5,97.5],axis=0)
        ax.fill_between(times,lo,hi,color=color,alpha=.18)
        ax.plot(times,shift.mean(axis=0),color=color,label='Binary segmentation')
        ax.axhline(0,color='#333333',ls='--',label='Mean-preserving averaging')
        ax.axvspan(1091,17913,color='grey',alpha=.08)
        ax.set(xscale='log',xlabel='Time (sweeps)',title=f'c = {c:.2f}'); ax.grid(alpha=.15)
    axes[0].set_ylabel('Apparent +1 fraction change\n(percentage points)')
    axes[1].legend(fontsize=8,loc='lower right')
    fig.suptitle('Conservation diagnostic | pointwise 95% paired-trajectory bootstrap bands',fontsize=11)
    fig.savefig(output/'figure2_apparent_fraction.png',dpi=200); plt.close(fig)

    real=rows(volumes/'measurements.csv'); ids=[f'AlGe_{t}min' for t in (15,105,195,315)]
    fig,axes=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
    for stage,offset,color,label in [('integrated',-.08,colors[0],'4x averaging'),('segmented',.08,colors[1],'4x + segmentation')]:
        values=[float(next(r for r in real if r['id']==name and float(r['crop_fraction'])==1 and r['stage']==stage and int(r['factor'])==4)['half_height_ratio_to_same_crop']) for name in ids]
        axes[0].plot(np.arange(4)+offset,values,'o',color=color,label=label)
    for fraction,offset,color,label in [(.75,-.08,colors[0],'3/4 width per axis'),(.5,.08,colors[1],'1/2 width per axis')]:
        values=np.array([float(next(r for r in real if r['id']==name and float(r['crop_fraction'])==fraction and r['stage']=='native')['half_height_ratio_to_full_box']) for name in ids])
        valid=np.isfinite(values); axes[1].plot((np.arange(4)+offset)[valid],values[valid],'o',color=color,label=label)
    for i in (0,1): axes[1].text(i,.80,'Both crops:\nno Ge',ha='center',fontsize=8,color='#555555')
    for ax in axes:
        ax.set(xticks=range(4),xticklabels=['15 min','105 min','195 min','315 min'],xlabel='Scan identifier (not a kinetic comparison)',xlim=(-.5,3.5))
        ax.axhline(1,color='grey',ls=':',lw=1); ax.grid(axis='y',alpha=.15); ax.legend(fontsize=8)
    axes[0].set(title='Same full field; coarser voxels',ylabel='Length / native full-box length',ylim=(.95,2.2))
    axes[1].set(title='Native voxels; smaller fields',ylabel='Length / native full-box length',ylim=(.6,1.05))
    fig.suptitle('Real Al-Ge masks | static paired comparisons; no independent-specimen intervals',fontsize=11)
    fig.savefig(output/'figure3_real_volume_sensitivity.png',dpi=200); plt.close(fig)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'builder_sha256':sha(Path(__file__)),'inputs':{str(p):sha(p) for p in [analysis/'paired_fits.csv',analysis/'per_checkpoint.csv',volumes/'measurements.csv']},
              'outputs':{p.name:sha(p) for p in output.glob('*.png')},
              'figure2_intervals':'Pointwise, 500 complete-trajectory resamples; not simultaneous bands',
              'real_data_attribution':'Jonas Fell (2023), Mendeley Data v1, doi:10.17632/hj9njz3rxp.1, CC BY 4.0; derived crop and resolution measurements.'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('analysis',type=Path)
    p.add_argument('volumes',type=Path); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); build(a.analysis,a.volumes,a.output)
