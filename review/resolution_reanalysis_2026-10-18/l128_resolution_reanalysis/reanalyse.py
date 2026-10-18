# Pre-declared re-analysis (see PROTOCOL.md beside this file). Read-only on the repo archives.
# Run from the repo root:  python3 review/resolution_reanalysis_2026-10-18/l128_resolution_reanalysis/reanalyse.py
import csv, glob, hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.getcwd())
from research.imaging import image_length
from research.fraction_matching import integrate, match_fraction, TIE_SEEDS

OUT = os.path.dirname(os.path.abspath(__file__))
RUNS = 'research/runs/main_065_multisize_v1'
FACTORS = (2, 4); STAGES = ('integrated', 'fixed', 'matched')
BINS = [(0, 1), (1, 2), (2, 3), (3, 5), (5, np.inf)]
TOL = 0.02; NBOOT = 2000; SEED = 20261018

def L(field, spacing): return image_length(field, spacing)['length']

def measure(comp):
    files = sorted(glob.glob(f'{RUNS}/{comp}_L128_rep*.npz'))
    rows = []
    for f in files:
        d = np.load(f); m = d['t'] >= 1000; t = d['t'][m]
        ind = (d['snapshots'][m] > 0).astype(float)
        nat, proc = [], {(k, s): [] for k in FACTORS for s in STAGES}
        for x in ind:
            nat.append(L(x, 1.))
            for k in FACTORS:
                b = integrate(x, k)
                proc[k, 'integrated'].append(L(b, k))
                proc[k, 'fixed'].append(L((b >= .5).astype(float), k))
                proc[k, 'matched'].append(np.mean([L(match_fraction(b, x.mean(), s)[0].astype(float), k) for s in TIE_SEEDS]))
        rows.append((os.path.basename(f), t, np.array(nat), {key: np.array(v) for key, v in proc.items()}))
    t = rows[0][1]; assert all(np.array_equal(r[1], t) for r in rows)
    nat = np.array([r[2] for r in rows]); proc = {key: np.array([r[3][key] for r in rows]) for key in rows[0][3]}
    return [r[0] for r in rows], t, nat, proc

def bin_slopes(t, nat, p, k):
    n = nat.mean(0) / k; D = np.log(p.mean(0) / nat.mean(0)); lt = np.log(t); out = []
    for lo, hi in BINS:
        s = (n >= lo) & (n < hi)
        if s.sum() >= 5 and t[s].max() / t[s].min() >= 2:
            X = lt[s] - lt[s].mean(); out.append(float(X @ D[s] / (X @ X)))
        else: out.append(np.nan)
    return out, n

def label(lo, hi):
    if not np.isfinite(lo): return 'not estimable'
    if -TOL <= lo and hi <= TOL: return 'PRESERVED'
    if hi < -TOL or lo > TOL: return 'BIASED'
    return 'UNDECIDED'

def main():
    rng = np.random.default_rng(SEED); result = {}; table = []
    for comp in ('c0', 'c1'):
        names, t, nat, proc = measure(comp)
        np.savez_compressed(f'{OUT}/lengths_{comp}.npz', t=t, native=nat, names=names,
                            **{f'f{k}_{s}': v for (k, s), v in proc.items()})
        idx = [rng.integers(0, len(names), len(names)) for _ in range(NBOOT)]
        for k in FACTORS:
            for s in STAGES:
                est, n = bin_slopes(t, nat, proc[k, s], k)
                boot = np.array([bin_slopes(t, nat[i], proc[k, s][i], k)[0] for i in idx])
                for b, (lo, hi) in enumerate(BINS):
                    col = boot[:, b]; ok = np.isfinite(col)
                    ci = (np.percentile(col[ok], 2.5), np.percentile(col[ok], 97.5)) if np.isfinite(est[b]) and ok.mean() > .5 else (np.nan, np.nan)
                    sel = (n >= lo) & (n < hi)
                    table.append(dict(composition=comp, factor=k, stage=s, bin=f'[{lo},{hi})',
                        checkpoints=int(sel.sum()), t_min=int(t[sel].min()) if sel.any() else '', t_max=int(t[sel].max()) if sel.any() else '',
                        estimate=est[b], ci_low=ci[0], ci_high=ci[1], boot_estimable_frac=float(ok.mean()),
                        verdict=label(*ci) if np.isfinite(est[b]) else 'not estimable'))
        nb = [nat.mean(0)]
        result[comp] = dict(native_length_first_last=[float(nb[0][0]), float(nb[0][-1])], t_first_last=[int(t[0]), int(t[-1])],
                            max_native_over_box=float(nat.mean(0).max() / 128))
    for comp in ('c0', 'c1'):
        for k in FACTORS:
            for s in STAGES:
                r = [x for x in table if x['composition'] == comp and x['factor'] == k and x['stage'] == s and x['verdict'] != 'not estimable']
                if len(r) < 2: v = 'Inconclusive'
                elif r[-1]['verdict'] == 'BIASED': v = 'No success regime in this data'
                elif r[-1]['verdict'] == 'PRESERVED' and r[0]['bin'] in ('[0,1)', '[1,2)') and r[0]['verdict'] == 'BIASED': v = 'Success regime found'
                else: v = 'Inconclusive'
                result[comp][f'f{k}_{s}'] = v
    result['study_level_primary'] = 'success regime found' if all(result[c]['f4_matched'] == 'Success regime found' for c in ('c0', 'c1')) else 'not established'
    result['protocol_sha256'] = hashlib.sha256(open(f'{OUT}/PROTOCOL.md', 'rb').read()).hexdigest()
    with open(f'{OUT}/bin_slopes.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    json.dump(result, open(f'{OUT}/verdicts.json', 'w'), indent=1)
    for x in table:
        print('{composition} f{factor} {stage:10s} {bin:9s} n={checkpoints:2d} t={t_min}-{t_max} {estimate:+.4f} [{ci_low:+.4f},{ci_high:+.4f}] {verdict}'.format(**x))
    print(json.dumps(result, indent=1))

if __name__ == '__main__': main()
