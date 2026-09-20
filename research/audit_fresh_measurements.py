"""Separate arithmetic and direct-pair checks of the frozen fresh-run analysis.

Imports no production measurement, fitting or bootstrap functions. This is
internal AI-assisted verification, not independent human review. Exact
bootstrap enumeration removes resampling Monte Carlo error, not small-sample
uncertainty or uncertainty in measurement/model choices.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (110, 211, 312, 413, 514)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def direct_measures(field, spacing=1):
    z = np.asarray(field, dtype=float)
    z = z-z.mean()
    variance = float((z*z).mean())
    metrics = {key: [] for key in ('half', 'lobe', 'near')}
    for axis in (1, 0):
        values = []
        for r in range(min(z.shape)//2+1):
            a, b = [slice(None)]*2, [slice(None)]*2
            a[axis], b[axis] = slice(0, z.shape[axis]-r), slice(r, None)
            values.append(float((z[tuple(a)]*z[tuple(b)]).mean()/variance) if variance else np.nan)
        c = np.asarray(values)
        def cross(level):
            hits = np.flatnonzero((c[:-1] >= level) & (c[1:] < level))
            if not len(hits) or not np.all(np.isfinite(c)): return np.nan
            k = int(hits[0])
            return k+(c[k]-level)/(c[k]-c[k+1])
        metrics['half'].append(cross(.5))
        metrics['near'].append(cross(.02))
        hits = np.flatnonzero(c <= 0)
        area = np.nan
        if len(hits) and np.all(np.isfinite(c)) and c[0] > 0:
            k = int(hits[0])
            end = k-1+c[k-1]/(c[k-1]-c[k])
            xs = np.r_[np.arange(k), end]
            ys = np.r_[c[:k], 0.]
            area = float(np.sum(np.diff(xs)*(ys[1:]+ys[:-1])/2))
        metrics['lobe'].append(area)
    return dict(half=float(np.mean(metrics['half'])*spacing),
                lobe=float(np.mean(metrics['lobe'])*spacing),
                min_half_pixels=float(np.min(metrics['half'])),
                near_zero_min=float(np.min(metrics['near'])*spacing))


def ols(times, values):
    times, values = np.asarray(times), np.asarray(values)
    if len(times)<4 or times[0]<=0 or times[-1]/times[0]<5 or np.any(np.diff(times)<=0): return np.nan
    if not np.all(np.isfinite(values)&(values>0)): return np.nan
    design = np.column_stack((np.ones(len(times)), np.log(times)))
    return float(np.linalg.lstsq(design, np.log(values), rcond=None)[0][1])


def delta(times, native, observed):
    return ols(times, observed.mean(axis=0))-ols(times, native.mean(axis=0))


def sampled_interval(times, native, observed):
    rng = np.random.default_rng(912)
    draws = []
    for _ in range(1000):
        ix = rng.integers(len(native), size=len(native))
        draws.append(delta(times, native[ix], observed[ix]))
    return np.percentile(draws, [2.5, 97.5])


def bootstrap_counts(n):
    """All count vectors and multinomial probabilities for n draws from n rows."""
    if isinstance(n, bool) or not isinstance(n, int) or not 2 <= n <= 8:
        raise ValueError('Bounded enumeration supports 2 to 8 replicas')
    def compositions(total, slots):
        if slots == 1:
            yield (total,)
        else:
            for first in range(total+1):
                for rest in compositions(total-first, slots-1): yield (first,)+rest
    counts = np.asarray(list(compositions(n, n)), dtype=int)
    weights = np.array([math.factorial(n)/math.prod(math.factorial(int(x)) for x in row)/n**n for row in counts])
    if len(counts)!=math.comb(2*n-1,n-1) or not np.all(counts.sum(axis=1)==n): raise AssertionError('Enumeration failed')
    if abs(weights.sum()-1)>1e-12: raise AssertionError('Probabilities do not normalize')
    return counts, weights


def weighted_quantile(values, weights, probabilities=(.025,.975)):
    """Inverse discrete CDF (no interpolation between discrete support points)."""
    values, weights = np.asarray(values), np.asarray(weights)
    if values.ndim!=1 or values.shape!=weights.shape or not len(values): raise ValueError('Matching vectors required')
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(weights)&(weights>=0)) or weights.sum()<=0: raise ValueError('Invalid distribution')
    if any(not 0<=p<=1 for p in probabilities): raise ValueError('Invalid quantile')
    ix = np.argsort(values, kind='stable')
    cdf = np.cumsum(weights[ix])/weights.sum()
    return [float(values[ix[min(np.searchsorted(cdf,p,side='left'),len(ix)-1)]]) for p in probabilities]


def exact_interval(times, native, observed):
    counts, weights = bootstrap_counts(len(native))
    a, b = counts@native/len(native), counts@observed/len(native)
    design = np.column_stack((np.ones(len(times)), np.log(times)))
    # OLS linearity permits solving every weighted-resample log ratio together.
    slopes = np.linalg.lstsq(design, np.log(b/a).T, rcond=None)[0][1]
    low, high = weighted_quantile(slopes, weights)
    return dict(low=low, high=high, count_vectors=len(counts), probability_sum=float(weights.sum()),
                ordered_resamples=len(native)**len(native))


def label(low, high):
    if not np.isfinite(low) or not np.isfinite(high): return 'unresolved'
    if low>=-.02 and high<=.02: return 'within'
    if low>.02 or high<-.02: return 'outside'
    return 'uncertain'


def close(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=1e-10, equal_nan=True)


def run(campaign, analysis, output):
    if output.exists(): raise FileExistsError('Choose a new audit directory')
    manifest = json.loads((analysis/'manifest.json').read_text())
    if manifest['cohort']!='fresh' or manifest['independent_replica_count']!=16: raise ValueError('Expected complete 16-run fresh cohort')
    for name,h in manifest['sources'].items():
        if digest(ROOT/name)!=h: raise ValueError('Frozen source changed: '+name)
    for name,h in manifest['outputs'].items():
        if digest(analysis/name)!=h: raise ValueError('Analysis changed: '+name)
    if digest(campaign/'manifest.json')!=manifest['campaign_manifest_sha256']: raise ValueError('Campaign manifest changed')
    for name,h in manifest['input_sha256'].items():
        if digest(campaign/name)!=h: raise ValueError('Raw trajectory changed: '+name)
    rows = read_rows(analysis/'observations.csv')
    lookup = {(r['id'],int(r['sweep']),int(r['factor']),int(r['origin']),r['stage'],int(r['tie_seed'])):r for r in rows}
    if len(lookup)!=len(rows) or len(rows)!=manifest['observations']: raise ValueError('Duplicate/missing observations')
    errors = {k:0. for k in ('half','lobe','min_half_pixels','near_zero_min')}
    checks = unresolved = 0
    discrepancies, direct_lookup, cache = [], {}, {}
    for name in sorted(manifest['input_sha256']):
        with np.load(campaign/name, allow_pickle=False) as raw:
            eligible = np.flatnonzero((raw['t']>=1000)&(raw['t']<=20000))
            for k in eligible:
                base = (raw['snapshots'][k].astype(float)+1)/2
                for factor in (2,4,8):
                    for origin,(dy,dx) in enumerate(((0,0),(factor//2,0),(0,factor//2),(factor//2,factor//2))):
                        image = base[np.ix_((np.arange(128)+dy)%128,(np.arange(128)+dx)%128)]
                        gray = np.array([[image[y:y+factor,x:x+factor].mean() for x in range(0,128,factor)] for y in range(0,128,factor)])
                        versions = [('native',-1,image),('integrated',-1,gray),('fixed',-1,(gray>=.5).astype(float))]
                        for seed in SEEDS:
                            priority = np.random.default_rng(seed).random(gray.size)
                            order = np.lexsort((priority,-gray.ravel()))
                            a = np.zeros(gray.size)
                            a[order[:math.floor(gray.size*base.mean()+.5)]]=1
                            versions.append(('matched',seed,a.reshape(gray.shape)))
                        for stage,seed,a in versions:
                            old = lookup[name,int(raw['t'][k]),factor,origin,stage,seed]
                            spacing = 1 if stage=='native' else factor
                            cache_key = (a.shape, spacing, a.tobytes())
                            if cache_key not in cache:
                                cache[cache_key] = direct_measures(a,spacing)
                            calculated = cache[cache_key]
                            direct_lookup[name,int(raw['t'][k]),factor,origin,stage,seed] = calculated
                            if stage=='native':
                                near=calculated['near_zero_min']
                                native_cap=max(1.,2.**math.floor(math.log2(128/math.ceil(384/near)))) if np.isfinite(near) and near>0 else np.nan
                            close(native_cap,float(old['native_allowed_factor']))
                            close(float(a.mean()-base.mean()),float(old['fraction_error']))
                            for metric,value in calculated.items():
                                try:
                                    close(value,float(old[metric]))
                                except AssertionError:
                                    discrepancies.append(dict(id=name,sweep=int(raw['t'][k]),factor=factor,
                                        origin=origin,stage=stage,tie=seed,metric=metric,
                                        direct=float(value) if np.isfinite(value) else None,
                                        stored=float(old[metric]) if np.isfinite(float(old[metric])) else None))
                                if np.isfinite(value) and np.isfinite(float(old[metric])): errors[metric]=max(errors[metric],abs(value-float(old[metric])))
                                else: unresolved+=1
                            checks+=1
        print('Direct-pair check:',name,flush=True)
        cache.clear()
    fits = read_rows(analysis/'fits.csv')
    fit_checks, sensitivity, corrected_fit_checks = [], [], []
    seen = set()
    for old in fits:
        c,factor,origin = float(old['composition']),int(old['factor']),int(old['origin'])
        observable,stage = old['observable'],old['stage']
        key=(c,factor,origin,observable,stage)
        if key in seen: raise ValueError('Duplicate fit')
        seen.add(key)
        group=[r for r in rows if float(r['composition'])==c and int(r['factor'])==factor and int(r['origin'])==origin]
        names=sorted({r['id'] for r in group});times=np.array(sorted({int(r['sweep']) for r in group}))
        if len(names)!=8: raise ValueError('Expected eight trajectories per composition')
        def array(s,seed,metric):
            return np.array([[float(lookup[name,int(t),factor,origin,s,seed][metric]) for t in times] for name in names])
        arrays={s:array(s,-1,observable) for s in ('native','integrated','fixed')}
        ties=np.array([array('matched',s,observable) for s in SEEDS])
        arrays['matched']=ties.mean(axis=0)
        all_values=np.concatenate([a[None,:,:] for a in arrays.values()]+[ties],axis=0)
        keep=np.all(np.isfinite(all_values)&(all_values>0),axis=(0,1))
        t=times[keep];a=arrays['native'][:,keep];b=arrays[stage][:,keep]
        assert int(old['retained_points'])==len(t) and int(old['available_points'])==len(times)
        assert int(old['trajectories'])==8
        if len(t): assert int(old['first_sweep'])==t[0] and int(old['last_sweep'])==t[-1]
        alpha0,alpha=ols(t,a.mean(axis=0)),ols(t,b.mean(axis=0))
        shift=alpha-alpha0
        low,high=sampled_interval(t,a,b) if np.isfinite(shift) else (np.nan,np.nan)
        actual=[alpha0,alpha,shift,low,high]
        expected=[float(old[k]) for k in ('native_alpha','alpha','delta','low','high')]
        close(actual,expected)
        assert label(low,high)==old['tolerance_label']
        if np.isfinite(shift):
            ratio=b.mean(axis=0)/a.mean(axis=0)
            close([ratio[0],ratio[-1],ols(t,ratio)],[float(old[k]) for k in ('ratio_first','ratio_last','ratio_slope')])
        caps=array('native',-1,'native_allowed_factor')[:,keep]
        minimum=np.array([array(stage,s,'min_half_pixels') for s in SEEDS]) if stage=='matched' else array(stage,-1,'min_half_pixels')[None,:,:]
        minimum=minimum[:,:,keep]
        valid=np.isfinite(shift)
        cap_label='unknown' if not valid or not np.all(np.isfinite(caps)) else 'pass' if np.all(caps>=factor) else 'flag'
        pixel_label='unknown' if not valid or not np.all(np.isfinite(minimum)) else 'pass' if np.all(minimum>=3) else 'flag'
        assert old['directional_02_adaptation']==cap_label and old['observed_three_pixel_screen']==pixel_label
        fit_checks.append(dict(composition=c,factor=factor,origin=origin,observable=observable,stage=stage,
                              delta=shift,low=float(low),high=float(high),max_error=float(np.nanmax(np.abs(np.array(actual)-expected)))))
        def direct_array(s,seed):
            return np.array([[direct_lookup[name,int(t),factor,origin,s,seed][observable] for t in times] for name in names])
        direct_arrays={s:direct_array(s,-1) for s in ('native','integrated','fixed')}
        direct_ties=np.array([direct_array('matched',s) for s in SEEDS])
        direct_arrays['matched']=direct_ties.mean(axis=0)
        direct_values=np.concatenate([a[None,:,:] for a in direct_arrays.values()]+[direct_ties],axis=0)
        direct_keep=np.all(np.isfinite(direct_values)&(direct_values>0),axis=(0,1))
        dt=times[direct_keep];da=direct_arrays['native'][:,direct_keep];db=direct_arrays[stage][:,direct_keep]
        ds=delta(dt,da,db)
        dl,dh=sampled_interval(dt,da,db) if np.isfinite(ds) else (np.nan,np.nan)
        corrected_fit_checks.append(dict(composition=c,factor=factor,origin=origin,observable=observable,stage=stage,
            delta=ds,low=float(dl),high=float(dh),original_delta=shift,delta_change=ds-shift,
            retained_points=len(dt),original_retained_points=len(t),label=label(dl,dh),original_label=old['tolerance_label']))
        if factor==4 and origin==0 and stage=='matched':
            exact=exact_interval(t,a,b)
            loo=[delta(t,np.delete(a,i,axis=0),np.delete(b,i,axis=0)) for i in range(8)]
            sensitivity.append(dict(composition=c,observable=observable,delta=shift,
                original_low=float(low),original_high=float(high),exact_percentile=exact,
                exact_label=label(exact['low'],exact['high']),leave_one_out_min=min(loo),leave_one_out_max=max(loo),
                direct_delta=ds,direct_exact_percentile=exact_interval(dt,da,db)))
    if len(seen)!=144: raise ValueError('Expected all 144 fit rows')
    report=dict(status='discrepancies_found' if discrepancies else 'passed',scope=__doc__,direct_fields_checked=checks,direct_scalar_checks=checks*4,
        unresolved_scalar_checks=unresolved,max_direct_errors=errors,fit_rows_checked=len(fits),
        max_fit_error=max(r['max_error'] for r in fit_checks),primary_sensitivity=sensitivity,all_fit_checks=fit_checks,
        direct_discrepancies=discrepancies,direct_recomputed_fits=corrected_fit_checks,
        sampling='Every retained checkpoint in all 16 trajectories; every factor, origin, stage and tie',
        analysis_manifest_sha256=digest(analysis/'manifest.json'),audit_source_sha256=digest(Path(__file__)),
        frozen_sources_unchanged=True,limitations=['Checks cover the 36,864 retained observations, not excluded time points.',
        'Exact bootstrap is conditional on eight empirical trajectories and fixed measurement choices.',
        'No confidence-interval coverage guarantee, new physics, novelty or external validation follows.'])
    output.mkdir(parents=True)
    (output/'verification.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('all_fit_checks','direct_discrepancies','direct_recomputed_fits')},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('campaign',type=Path);p.add_argument('analysis',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.campaign,a.analysis,a.output)
