"""Regenerate every simulation figure and number in the preprint.

Data: the 32 development (main_065_multisize_v1, L=128) and 16 held-out
(growth_reliability_holdout_v1) Kawasaki trajectories at 0.65 Tc. Each is fitted
over 1,000-20,000 sweeps. Images at resolution k come from
research.imaging.observe(factor=k): k x k block averaging, then a threshold at 0.

Outputs go to paper/figures and paper/results. Run from the repository root:
    python paper/make_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from research.imaging import block_average, image_length, observe

OUT = Path('paper')
SETS = {'development': sorted(Path('research/runs/main_065_multisize_v1').glob('c*_L128_rep*.npz')),
        'holdout': sorted(Path('research/runs/growth_reliability_holdout_v1').glob('c*_L128_rep*.npz'))}
FACTORS = (1, 2, 4, 8)
WINDOW = (1000, 20000)
COMP = {'c0': '50:50', 'c1': '15:85'}

plt.rcParams.update({'font.family': 'serif', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'figure.dpi': 200})


def slope(t, L):
    return float(np.polyfit(np.log(t), np.log(L), 1)[0])


def analyse(path):
    d = np.load(path)
    t = d['t']
    idx = np.flatnonzero((t >= WINDOW[0]) & (t <= WINDOW[1]))
    rec = dict(file=path.name, set=path.parent.name, composition=COMP[path.name[:2]],
               n_points=len(idx))
    for k in FACTORS:
        L, Lavg = [], []
        for i in idx:
            s = d['snapshots'][i].astype(float)
            L.append(image_length(observe(s, factor=k) if k > 1 else s, pixel_size=k)['length'])
            if k > 1:
                Lavg.append(image_length(block_average(s, k), pixel_size=k)['length'])
        L = np.array(L)
        rec[f'n_{k}'] = slope(t[idx], L) if np.all(np.isfinite(L)) else None
        rec[f'median_px_per_domain_{k}'] = float(np.nanmedian(L) / k)
        rec[f'min_px_per_domain_{k}'] = float(np.nanmin(L) / k)
        if k > 1:
            rec[f'n_avg_only_{k}'] = slope(t[idx], np.array(Lavg)) if np.all(np.isfinite(Lavg)) else None
    return rec


def main():
    (OUT / 'figures').mkdir(parents=True, exist_ok=True)
    (OUT / 'results').mkdir(parents=True, exist_ok=True)
    recs = [analyse(p) for s in SETS.values() for p in s]
    (OUT / 'results' / 'per_trajectory.json').write_text(json.dumps(recs, indent=1))

    # Summary table: error by factor, set and composition.
    rows = []
    for setname in ('main_065_multisize_v1', 'growth_reliability_holdout_v1'):
        for comp in COMP.values():
            g = [r for r in recs if r['set'] == setname and r['composition'] == comp]
            for k in FACTORS[1:]:
                e = np.array([r[f'n_{k}'] - r['n_1'] for r in g if r[f'n_{k}'] is not None])
                a = np.array([r[f'n_avg_only_{k}'] - r['n_1'] for r in g if r[f'n_avg_only_{k}'] is not None])
                rows.append(dict(set=setname, composition=comp, factor=k, n=len(g), resolved=len(e),
                                 native_exponent_median=float(np.median([r['n_1'] for r in g])),
                                 median_px_per_domain=float(np.median([r[f'median_px_per_domain_{k}'] for r in g])),
                                 error_median=float(np.median(e)) if len(e) else None,
                                 error_min=float(e.min()) if len(e) else None,
                                 error_max=float(e.max()) if len(e) else None,
                                 averaging_only_error_median=float(np.median(a)) if len(a) else None))
    (OUT / 'results' / 'summary.json').write_text(json.dumps(rows, indent=1))
    with open(OUT / 'results' / 'table_errors.tex', 'w') as f:
        for r in rows:
            set_label = 'Dev.' if r['set'].startswith('main') else 'Held-out'
            err = (f"${r['error_median']:+.3f}$ & $[{r['error_min']:+.3f},\\,{r['error_max']:+.3f}]$"
                   if r['error_median'] is not None else 'unresolved & ')
            avg = f"${r['averaging_only_error_median']:+.3f}$" if r['averaging_only_error_median'] is not None else '--'
            f.write(f"{set_label} & {r['composition']} & {r['factor']} & "
                    f"{r['median_px_per_domain']:.2f} & {err} & {avg} \\\\\n")

    # Figure 1: one snapshot at full resolution and after 2x and 4x.
    d = np.load(SETS['development'][0])
    s = d['snapshots'][int(np.flatnonzero(d['t'] == 10600)[0])].astype(float)
    fig, ax = plt.subplots(1, 3, figsize=(6.3, 2.6))
    for a, k in zip(ax, (1, 2, 4)):
        img = s if k == 1 else observe(s, factor=k)
        L = image_length(img, pixel_size=k)['length'] / k
        a.imshow(img, cmap='gray', interpolation='nearest')
        a.set_title(f'{"Full resolution" if k == 1 else f"{k}x coarser"}\n{L:.1f} px per domain', fontsize=8)
        a.axis('off')
    fig.tight_layout()
    fig.savefig(OUT / 'figures' / 'fig1_coarsening.pdf')
    plt.close(fig)

    # Figure 2: exponent error against pixels per domain, every trajectory.
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    for comp, marker in (('50:50', 'o'), ('15:85', 's')):
        for setname, fill in (('main_065_multisize_v1', True), ('growth_reliability_holdout_v1', False)):
            g = [r for r in recs if r['composition'] == comp and r['set'] == setname]
            x = [r[f'median_px_per_domain_{k}'] for r in g for k in FACTORS[1:] if r[f'n_{k}'] is not None]
            y = [r[f'n_{k}'] - r['n_1'] for r in g for k in FACTORS[1:] if r[f'n_{k}'] is not None]
            colour = 'C0' if comp == '50:50' else 'C3'
            ax.scatter(x, y, s=14, marker=marker, facecolors=colour if fill else 'none',
                       edgecolors=colour, linewidths=.8,
                       label=f'{comp}, {"development" if fill else "held-out"}')
    ax.axhline(0, color='k', lw=.6)
    ax.axhspan(-.01, .01, color='0.9', zorder=0)
    ax.set_xscale('log')
    ticks = [.4, .5, .7, 1, 1.5]
    ax.set_xticks(ticks, [f'{v:g}' for v in ticks])
    ax.minorticks_off()
    ax.set_xlabel('Median pixels per domain over the fit window')
    ax.set_ylabel('Exponent error  $n_k - n_1$')
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / 'figures' / 'fig2_error_vs_pixels.pdf')
    plt.close(fig)

    # Figure 3: the 2x warning against the true error, held-out set only.
    g = [r for r in recs if r['set'] == 'growth_reliability_holdout_v1']
    pts = [(r[f'n_{2 * k}'] - r[f'n_{k}'], r[f'n_{k}'] - r['n_1'], k) for r in g for k in (1, 2, 4)
           if r[f'n_{2 * k}'] is not None and r[f'n_{k}'] is not None]
    w, b, k = map(np.array, zip(*pts))
    stats = dict(cases=len(pts), biased=int(np.sum(np.abs(b) > .01)),
                 flagged_biased=int(np.sum((np.abs(b) > .01) & (np.abs(w) > .01))),
                 unbiased=int(np.sum(np.abs(b) <= .01)),
                 flagged_unbiased=int(np.sum((np.abs(b) <= .01) & (np.abs(w) > .01))),
                 correlation_k_gt_1=float(np.corrcoef(w[k > 1], b[k > 1])[0, 1]))
    (OUT / 'results' / 'screen_validation.json').write_text(json.dumps(stats, indent=1))
    fig, ax = plt.subplots(figsize=(3.4, 3.2))
    names = {1: 'full resolution', 2: '2x coarser', 4: '4x coarser'}
    for kk, c in ((1, '0.5'), (2, 'C0'), (4, 'C3')):
        m = k == kk
        ax.scatter(w[m], b[m], s=14, color=c, label=names[kk])
    lim = min(w.min(), b.min()) * 1.1
    ax.plot([lim, 0], [lim, 0], color='k', lw=.5, ls=':')
    ax.axvline(-.01, color='k', lw=.5)
    ax.axhline(-.01, color='k', lw=.5)
    ax.set_xlabel('Warning: change after a further 2x')
    ax.set_ylabel('True exponent error')
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / 'figures' / 'fig3_screen.pdf')
    plt.close(fig)
    print(json.dumps(stats))
    for r in rows:
        print(r['set'][:4], r['composition'], r['factor'], round(r['median_px_per_domain'], 2),
              r['error_median'] and round(r['error_median'], 4),
              r['averaging_only_error_median'] and round(r['averaging_only_error_median'], 4))


if __name__ == '__main__':
    main()
