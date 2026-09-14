"""Controlled image observation study; requires a NEW output directory.

python -m research.imaging_benchmark RUN_FOLDER --output NEW_FOLDER
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import scipy
from research.analyse_campaign import plt
from research.compare_estimators import paired_slopes
from research.imaging import image_length,observe,corner_crops

TRANSFORMS={
    'bin2':dict(factor=2), 'bin4':dict(factor=4),
    'blur1':dict(sigma=1.), 'blur2':dict(sigma=2.),
    'blur1_threshold_minus02':dict(sigma=1.,threshold=-.2),
    'blur1_threshold_plus02':dict(sigma=1.,threshold=.2)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys())
        writer.writeheader();writer.writerows(rows)


def observations(snapshot):
    """Yield (condition, crop identifier, image, spacing in original sites)."""
    yield 'full','full',snapshot,1
    for label,options in TRANSFORMS.items():
        yield label,'full',observe(snapshot,**options),options.get('factor',1)
    if snapshot.shape==(128,128):
        for width in (96,64,32):
            for (y,x),crop in corner_crops(snapshot,width):
                yield f'crop{width}',f'{y}:{x}',crop,1


def benchmark(folder,output):
    paths=sorted(folder.glob('*.npz'))
    if not paths: raise ValueError('No completed replicas.')
    if output.exists(): raise FileExistsError('Use a new output directory.')
    campaign=json.loads((folder/'manifest.json').read_text())
    plan=campaign['identity']['plan']
    output.mkdir(parents=True)
    source=Path(__file__).parent
    provenance=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        input_manifest_sha256=sha(folder/'manifest.json'),
        input_files={p.name:sha(p) for p in paths},
        sources={p.name:sha(p) for p in (Path(__file__),source/'imaging.py',
            source/'metrology.py',source/'compare_estimators.py',source/'analyse_campaign.py',source/'IMAGING_PROTOCOL.md')},
        versions=dict(numpy=np.__version__,scipy=scipy.__version__),
        role='fresh-seed repeat' if plan['seed']==20260913 else 'exploratory existing trajectories',
        planned_replicas=plan['replicas']*len(plan['sizes'])*len(plan['concentrations']),
        completed_replicas=len(paths),reference='full finite-window image, NOT true particle radius',
        transforms=TRANSFORMS)
    (output/'manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
    rows=[];groups={};examples={}
    for path in paths:
        with np.load(path,allow_pickle=False) as data:
            config=json.loads(str(data['config'])); c,L=config['concentration'],config['L']
            t=data['t'].copy(); snapshots=data['snapshots']; lengths=data['lengths']
            if snapshots.shape!=(len(t),L,L) or lengths.shape!=(len(t),2):
                raise ValueError(f'Invalid shapes: {path}')
            if not np.all(snapshots.sum(axis=(1,2))==data['magnetization']):
                raise ValueError(f'Conservation mismatch: {path}')
            per_condition={}
            for k,snapshot in enumerate(snapshots):
                current={}
                for condition,crop_id,img,spacing in observations(snapshot):
                    measured=image_length(img,spacing)
                    current.setdefault(condition,[]).append(measured['length'])
                    rows.append(dict(file=path.name,seed=config['seed'],c=c,L=L,t=int(t[k]),
                        condition=condition,crop_id=crop_id,pixel_size_sites=spacing,
                        width_sites=img.shape[1]*spacing,phase_fraction=float(np.mean(img>0)),**measured))
                current['periodic_engine']=[float(np.mean(lengths[k]))]
                for label,values in current.items():
                    per_condition.setdefault(label,[]).append(float(np.mean(values)))
            key=(c,L)
            if key in groups and not np.array_equal(groups[key]['t'],t):
                raise ValueError('Inconsistent times within group.')
            group=groups.setdefault(key,dict(t=t,conditions={}))
            for label,values in per_condition.items():
                group['conditions'].setdefault(label,[]).append(values)
            if L==128 and c not in examples: examples[c]=snapshots[-1].copy()
        print(f'Measured {path.name}',flush=True)
    write_csv(output/'observations.csv',rows)
    fits=[]
    for (c,L),group in sorted(groups.items()):
        t=group['t']; ref=np.asarray(group['conditions']['full']); meanref=ref.mean(axis=0)
        for label,replicas in group['conditions'].items():
            values=np.asarray(replicas)
            if values.shape!=ref.shape: raise ValueError('Unpaired replicas.')
            shared=np.all(np.isfinite(values)&(values>0)&np.isfinite(ref)&(ref>0),axis=0)
            for lower,upper in sorted(set(((100,20000),(1000,20000),(1000,plan['max_sweeps'])))):
                mask=shared&(t>=lower)&(t<=upper)
                alpha,lo,hi,delta,dlo,dhi=paired_slopes(t,values,ref,mask)
                fits.append(dict(c=c,L=L,n=len(ref),condition=label,t_min=lower,t_max=upper,
                    points=int(mask.sum()),used_t_min=int(t[mask][0]) if mask.any() else None,
                    used_t_max=int(t[mask][-1]) if mask.any() else None,
                    alpha=alpha,low=lo,high=hi,delta_vs_full=delta,delta_low=dlo,delta_high=dhi,
                    unresolved_fraction=float(np.mean(~np.isfinite(values))),
                    matched_last_time=int(t[mask][-1]) if mask.any() else None,
                    matched_last_length_ratio=float(values[:,mask][:,-1].mean()/ref[:,mask][:,-1].mean()) if mask.any() else float('nan')))
        if L==128:
            fig,axes=plt.subplots(1,3,figsize=(14,4.2),layout='constrained')
            for panel,labels in zip(axes,[['crop96','crop64','crop32'],['bin2','bin4','blur1','blur2'],
                    ['blur1','blur1_threshold_minus02','blur1_threshold_plus02','periodic_engine']]):
                for label in labels:
                    y=np.mean(group['conditions'][label],axis=0)
                    panel.plot(t,y/meanref,label=label)
                panel.axhline(1,color='black',ls=':');panel.set(xscale='log',xlabel='Sweeps',ylabel='Length / full-image reference')
                panel.legend(fontsize=7);panel.grid(alpha=.2)
            for ax,title in zip(axes,['Observation window','Synthetic blur / binning','Segmentation / boundary convention']):ax.set_title(title)
            fig.suptitle(f'c={c}, L=128, n={len(ref)}; no changing replica subset; gaps are unresolved')
            fig.savefig(output/f'observation_ratios_c{c}.png',dpi=170);plt.close(fig)
    # Actual finite systems versus a small window on the largest one.
    for c in sorted({key[0] for key in groups}):
        if (c,128) not in groups:continue
        fig,ax=plt.subplots(figsize=(7,4.6),layout='constrained')
        for L in (32,64,96,128):
            if (c,L) in groups:
                g=groups[c,L];a=np.asarray(g['conditions']['full'])
                ax.plot(g['t'],a.mean(axis=0),label=f'actual L={L}, full image')
        g=groups[c,128]
        for width in (32,64):
            ax.plot(g['t'],np.mean(g['conditions'][f'crop{width}'],axis=0),'--',label=f'{width} crop of L=128')
        ax.set(xscale='log',yscale='log',xlabel='Sweeps',ylabel='Finite-window threshold length (sites)',title=f'Physical box vs observation window; c={c}')
        ax.legend(fontsize=8);ax.grid(alpha=.2)
        fig.savefig(output/f'box_vs_window_c{c}.png',dpi=170);plt.close(fig)
        fig,axes=plt.subplots(1,4,figsize=(10,3),layout='constrained')
        snap=examples[c]
        for ax,img,title in zip(axes,[snap,observe(snap,factor=4),observe(snap,sigma=2),corner_crops(snap,32)[0][1]],['Original','4x bin + threshold','Blur sigma=2 + threshold','32-site corner crop']):
            ax.imshow(img,cmap='gray',vmin=-1,vmax=1,interpolation='nearest');ax.set_title(title,fontsize=9);ax.set_axis_off()
        fig.suptitle(f'Illustrative final checkpoint c={c}; panels have different fields/pixel sizes')
        fig.savefig(output/f'operators_c{c}.png',dpi=170);plt.close(fig)
    write_csv(output/'paired_fits.csv',fits)
    report=['# Controlled observation results','',f'{provenance["role"]}; {len(paths)} / {provenance["planned_replicas"]} replicas.',
        'Full-image covariance is a reference, not a true radius. No result is corrected toward 1/3.',
        'Each comparison uses its own common resolved mask; compare actual times, not just nominal labels.',
        'All crops within a replica are averaged only if every crop resolves. Bootstrap units are whole replicas.',
        'These transforms model observation sensitivity, not a calibrated instrument. Independent repeat is only four replicas/composition.',
        '', '## Primary window, L=128', '',
        '| c | condition | alpha | delta vs full [95% paired interval] | retained points | actual times |',
        '|---|---|---|---|---|---|']
    for r in fits:
        if r['L']==128 and r['t_min']==1000 and r['t_max']==20000:
            report.append(f'| {r["c"]} | {r["condition"]} | {r["alpha"]:.3f} | {r["delta_vs_full"]:.3f} [{r["delta_low"]:.3f}, {r["delta_high"]:.3f}] | {r["points"]} | {r["used_t_min"]}–{r["used_t_max"]} |')
    report+=['','All sizes/windows, missingness and ratios are in paired_fits.csv; raw individual crops are in observations.csv.',
        'The box/window figure is descriptive: independently simulated sizes are not paired statistical controls.',
        'Do not interpret agreement of estimators as proof of accuracy. No experimental images are included here.']
    (output/'REPORT.md').write_text('\n'.join(report)+'\n')
    print(output/'REPORT.md',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();benchmark(args.folder,args.output)
