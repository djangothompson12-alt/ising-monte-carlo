"""Paired comparison of Model B size estimators on a frozen raw-data inventory.

Run: python -m research.compare_estimators RUN_FOLDER --output NEW_FOLDER
This secondary analysis is exploratory; it was designed after seeing the pilot.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from research.analyse_campaign import fit_slope, plt
from research.metrology import snapshot_measures

MEASURES = ('threshold_05','positive_lobe','spectral_moment','inverse_interface_proxy')


def paired_slopes(t, values, reference, mask, draws=500):
    """Resample whole replicas with identical indices for both estimators."""
    if len(values)<2:
        return (float('nan'),)*6
    estimate = fit_slope(t,np.mean(values,axis=0),mask)
    difference = estimate-fit_slope(t,np.mean(reference,axis=0),mask)
    rng=np.random.default_rng(912)
    slopes,differences=[],[]
    for _ in range(draws):
        ix=rng.integers(len(values),size=len(values))
        a=fit_slope(t,np.mean(values[ix],axis=0),mask)
        b=fit_slope(t,np.mean(reference[ix],axis=0),mask)
        slopes.append(a)
        differences.append(a-b)
    if np.isfinite(slopes).sum()<.9*draws or np.isfinite(differences).sum()<.9*draws:
        return estimate,float('nan'),float('nan'),difference,float('nan'),float('nan')
    lo,hi=np.nanpercentile(slopes,[2.5,97.5])
    dlo,dhi=np.nanpercentile(differences,[2.5,97.5])
    return estimate,float(lo),float(hi),difference,float(dlo),float(dhi)


def compare(folder,output):
    paths=sorted(folder.glob('*.npz'))
    if not paths:
        raise ValueError('No completed raw replicas found.')
    if output.exists():
        raise FileExistsError('Use a new output directory to preserve earlier analyses.')
    manifest=json.loads((folder/'manifest.json').read_text())
    plan=manifest['identity']['plan']
    groups={}
    raw_rows=[]
    for path in paths:
        with np.load(path,allow_pickle=False) as d:
            config=json.loads(str(d['config']))
            c,L=config['concentration'],config['L']
            t=d['t'].copy()
            if (d['snapshots'].shape != (len(t),L,L)
                    or d['correlations'].shape[:2] != (len(t),2)
                    or d['lengths'].shape != (len(t),2)):
                raise ValueError(f'Inconsistent checkpoint arrays in {path.name}')
            measures=[snapshot_measures(snap,corr) for snap,corr in zip(d['snapshots'],d['correlations'])]
            values=np.array([[m[name] for name in MEASURES] for m in measures])
            # Independently recomputed baseline must reproduce the archived engine result.
            np.testing.assert_allclose(values[:,0],np.mean(d['lengths'],axis=1),equal_nan=True,atol=1e-12)
            magnetizations=d['snapshots'].sum(axis=(1,2))
            if (not np.all(magnetizations == d['magnetization'])
                    or not np.all(magnetizations == magnetizations[0])):
                raise ValueError(f'Conservation failed in {path.name}')
            if (c,L) in groups and not np.array_equal(t,groups[(c,L)]['t']):
                raise ValueError('Checkpoints differ within a group.')
            groups.setdefault((c,L),dict(t=t,replicas=[]))['replicas'].append(values)
            for time,m in zip(t,measures):
                raw_rows.append(dict(file=path.name,c=c,L=L,t=int(time),**m))
    output.mkdir(parents=True)
    provenance=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        exploratory=True,source_files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),Path(__file__).with_name('metrology.py'),Path(__file__).with_name('analyse_campaign.py'))},
        input_manifest_sha256=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
        input_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        package_versions=dict(numpy=np.__version__),
        completed_replicas=len(paths),planned_replicas=plan['replicas']*len(plan['sizes'])*len(plan['concentrations']))
    (output/'manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
    fits=[]
    for (c,L),group in sorted(groups.items()):
        values=np.stack(group['replicas']) # replica, time, measure
        t=group['t']
        mean=np.mean(values,axis=0)
        shared=np.all(np.isfinite(values)&(values>0),axis=(0,2)) & (mean[:,0]/L<.15)
        fig,axes=plt.subplots(1,2,figsize=(10.5,4.3),layout='constrained')
        reference_index=int(np.argmin(abs(t-100)))
        for j,name in enumerate(MEASURES):
            if np.isfinite(mean[reference_index,j]) and mean[reference_index,j]>0:
                axes[0].plot(t,mean[:,j]/mean[reference_index,j],label=name)
            local=[fit_slope(t,mean[:,j],(t>=t[max(0,k-4)])&(t<=t[min(len(t)-1,k+4)]),min_span=2) for k in range(len(t))]
            axes[1].plot(t,local,label=name)
            for lower in (100,1000):
                for upper in sorted(set((min(20000,plan['max_sweeps']),plan['max_sweeps']))):
                    mask=shared&(t>=lower)&(t<=upper)
                    alpha,lo,hi,delta,dlo,dhi=paired_slopes(t,values[:,:,j],values[:,:,0],mask)
                    fits.append(dict(c=c,L=L,n=len(values),estimator=name,t_min=lower,t_max=upper,
                        points=int(mask.sum()),used_t_min=int(t[mask].min()) if mask.any() else None,
                        used_t_max=int(t[mask].max()) if mask.any() else None,
                        alpha=alpha,low=lo,high=hi,delta_vs_threshold=delta,
                        delta_low=dlo,delta_high=dhi,unresolved_values=int(np.count_nonzero(~np.isfinite(values[:,:,j])))))
        axes[0].set(xscale='log',yscale='log',xlabel='Time (sweeps)',ylabel=f'Measure / measure at t={t[reference_index]}',title='Growth relative to fixed early checkpoint')
        axes[1].set(xscale='log',xlabel='Time (sweeps)',ylabel='Local log–log slope',title='No estimator is forced to follow 1/3')
        axes[1].axhline(1/3,ls=':',color='black')
        for ax in axes:
            ax.legend(fontsize=7)
            ax.grid(alpha=.2)
        fig.suptitle(f'Model B: c={c}, L={L}, {len(values)} paired replicas')
        fig.savefig(output/f'estimators_c{c}_L{L}.png',dpi=180)
        plt.close(fig)
    for name,rows in [('per_replica_measures.csv',raw_rows),('paired_fits.csv',fits)]:
        with (output/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    report=['# Exploratory estimator comparison','',f'Frozen inventory: {len(paths)} completed replicas of {provenance["planned_replicas"]} planned.',
        'This analysis was specified after the pilot. It is not a preregistered confirmation.',
        'All fits within a c,L,time-window group use the same resolved checkpoints and whole-replica bootstrap draws.',
        'The CSV records the actual retained time range and point count. The nominal window below may lose checkpoints when any estimator is unresolved; this can change the threshold-only slope relative to the primary analysis.',
        'The inverse interface fraction is a proxy, not a calibrated domain radius. The full-spectrum first moment is sensitive to thermal/high-frequency power.',
        'Neither estimator agreement nor disagreement proves an asymptotic growth law. NaN indicates an unresolved or insufficient fit.',
        '', '| c | L | n | estimator | window | alpha [95% bootstrap] | difference from threshold [95% paired bootstrap] |',
        '|---|---|---|---|---|---|---|']
    for r in fits:
        report.append(f'| {r["c"]} | {r["L"]} | {r["n"]} | {r["estimator"]} | {r["t_min"]}–{r["t_max"]} | {r["alpha"]:.3f} [{r["low"]:.3f}, {r["high"]:.3f}] | {r["delta_vs_threshold"]:.3f} [{r["delta_low"]:.3f}, {r["delta_high"]:.3f}] |')
    (output/'REPORT.md').write_text('\n'.join(report)+'\n')
    print(output/'REPORT.md')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    compare(args.folder,args.output)
