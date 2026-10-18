# POST-HOC, not in PROTOCOL.md: the declared ratio of ensemble means is undefined when one
# trajectory has an unresolved length (no 0.5 crossing). This drops only those trajectory-checkpoints
# (nanmean) to show what the declared-but-not-estimable c0 [2,3) bins would read. Not a primary result.
import numpy as np, sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import reanalyse as R; os.chdir(R.OUT)
rng = np.random.default_rng(R.SEED)
for comp in ('c0',):
    d = np.load(f'lengths_{comp}.npz'); t = d['t']; nat = d['native']
    idx = [rng.integers(0, nat.shape[0], nat.shape[0]) for _ in range(R.NBOOT)]
    for k in (2, 4):
        for s in R.STAGES:
            p = d[f'f{k}_{s}']
            def sl(nn, pp):
                n = nn.mean(0)/k; D = np.log(np.nanmean(pp, 0)/nn.mean(0)); lt = np.log(t); o = []
                for lo, hi in R.BINS:
                    m = (n >= lo) & (n < hi)
                    if m.sum() >= 5 and t[m].max()/t[m].min() >= 2:
                        X = lt[m]-lt[m].mean(); o.append(X @ D[m]/(X @ X))
                    else: o.append(np.nan)
                return o
            e = sl(nat, p); b = np.array([sl(nat[i], p[i]) for i in idx])
            for j, (lo, hi) in enumerate(R.BINS):
                if np.isfinite(e[j]) and np.isnan(np.nanmean(p, 0)).sum() == 0 and np.isnan(p).any():
                    c = b[:, j][np.isfinite(b[:, j])]
                    print(f'{comp} f{k} {s:10s} [{lo},{hi}) {e[j]:+.4f} [{np.percentile(c,2.5):+.4f},{np.percentile(c,97.5):+.4f}] {R.label(np.percentile(c,2.5),np.percentile(c,97.5))}')
