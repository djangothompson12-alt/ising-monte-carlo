"""Plot raw growth, local exponents and a candidate z=3 finite-size collapse.

Confidence intervals resample entire replicas; time points are not independent
replicates. No parameters are adjusted to make the collapse look successful.
"""
from __future__ import annotations
import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import warnings
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def fit_slope(t, length, mask, min_span=5):
    selected = mask & np.isfinite(length) & (length > 0) & (t > 0)
    if selected.sum() < 4 or t[selected][-1] / t[selected][0] < min_span:
        return float('nan')
    return float(np.polyfit(np.log(t[selected]), np.log(length[selected]), 1)[0])


def bootstrap_slope(t, trajectories, mask, seed=17, draws=500):
    if len(trajectories) < 2:
        return (float('nan'),) * 3
    mean = np.mean(trajectories, axis=0)
    alpha = fit_slope(t, mean, mask)
    rng = np.random.default_rng(seed)
    values = [fit_slope(t, np.mean(trajectories[rng.integers(len(trajectories), size=len(trajectories))], axis=0), mask)
              for _ in range(draws)]
    values = np.asarray(values)
    if np.isfinite(values).sum() < draws * .9:
        return alpha, float('nan'), float('nan')
    lo, hi = np.nanpercentile(values, [2.5, 97.5])
    return alpha, float(lo), float(hi)


def analyse(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    plan = manifest['identity']['plan']
    output = folder / 'analysis'
    output.mkdir(exist_ok=True)
    inputs = sorted(folder.glob('*.npz'))
    (output / 'analysis_manifest.json').write_text(json.dumps(dict(
        analysed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        campaign_manifest_sha256=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
        numpy=np.__version__, matplotlib=matplotlib.__version__,
        raw_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}),indent=2)+'\n')
    rows, means = [], []
    for ci, c in enumerate(plan['concentrations']):
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), layout='constrained')
        for L in plan['sizes']:
            # Freeze the input inventory: more replicas may finish during analysis.
            paths = [p for p in inputs if p.name.startswith(f'c{ci}_L{L}_rep')]
            if not paths:
                continue
            trajectories = []
            for path in paths:
                with np.load(path, allow_pickle=False) as data:
                    t = data['t']
                    trajectories.append(np.mean(data['lengths'], axis=1))
            trajectories = np.asarray(trajectories)
            # No nanmean: a missing replica must not silently change the ensemble.
            mean = np.mean(trajectories, axis=0)
            se = np.std(trajectories, axis=0, ddof=1) / np.sqrt(len(paths)) if len(paths) > 1 else np.full(len(t), np.nan)
            for j, sweep in enumerate(t):
                means.append(dict(c=c, L=L, t=int(sweep), n=len(paths), length=mean[j], standard_error=se[j]))
            label = f'L={L}, n={len(paths)}'
            axes[0].plot(t, mean, label=label)
            axes[0].fill_between(t, mean-se, mean+se, alpha=.1)
            local = [fit_slope(t, mean, (t >= t[max(0,j-4)]) & (t <= t[min(len(t)-1,j+4)]), min_span=2) for j in range(len(t))]
            axes[1].plot(t, local, label=label)
            axes[2].plot(t / float(L)**3, mean / L, label=label)
            # Prospective, shared time windows; include 2-sweep window only as legacy sensitivity.
            for t_min in (2, 100, 1000):
                for t_max in sorted(set((min(20000, plan['max_sweeps']), plan['max_sweeps']))):
                    mask = (t >= t_min) & (t <= t_max) & (mean / L < .15)
                    alpha, lo, hi = bootstrap_slope(t, trajectories, mask)
                    rows.append(dict(c=c, L=L, n=len(paths), t_min=t_min, t_max=t_max,
                        n_points=int(mask.sum()), alpha=alpha, bootstrap_low=lo, bootstrap_high=hi,
                        max_length_over_L=float(np.nanmax(mean / L))))
        axes[0].set(xscale='log', yscale='log', xlabel='Time (sweeps)', ylabel='Correlation length (sites)', title='Growth; bands = replica SE')
        axes[1].set(xscale='log', xlabel='Time (sweeps)', ylabel='Local log–log slope', title='Moving 9-point fit')
        axes[1].axhline(1/3, color='black', ls=':', label='1/3 reference')
        axes[2].set(xscale='log', yscale='log', xlabel=r'$t/L^3$', ylabel=r'$\ell/L$', title='Candidate z=3 collapse (not fitted)')
        for ax in axes:
            ax.grid(alpha=.2)
            ax.legend(fontsize=7)
        fig.suptitle(f'Model B, c={c}: finite-size / finite-time diagnostics')
        fig.savefig(output / f'growth_c{ci}.png', dpi=180)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(6.4, 4.4), layout='constrained')
        for lower in (2, 100, 1000):
            selected = [r for r in rows if r['c'] == c and r['t_min'] == lower and r['t_max'] == plan['max_sweeps']]
            xs = np.array([r['L'] for r in selected])
            ys = np.array([r['alpha'] for r in selected])
            ax.plot(xs, ys, 'o-', label=f't ≥ {lower}')
            # Draw intervals directly; percentile intervals need not contain the point estimate.
            ax.vlines(xs, [r['bootstrap_low'] for r in selected], [r['bootstrap_high'] for r in selected], alpha=.5)
        ax.axhline(1/3, color='black', ls=':')
        ax.set(xlabel='Lattice size L', ylabel='Fitted effective exponent', title=f'c={c}; fit-window sensitivity; ℓ/L < 0.15')
        ax.legend()
        ax.grid(alpha=.2)
        fig.savefig(output / f'exponent_vs_size_c{ci}.png', dpi=180)
        plt.close(fig)
    for filename, records in [('exponents.csv', rows), ('ensemble_lengths.csv', means)]:
        if records:
            with (output / filename).open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
    text = ['# Campaign analysis', '', f'Analysed {len(inputs)} completed replicas.', '',
        'The z=3 panel is a proposed scaling test. A visually plausible overlap does not establish the growth law.',
        'Replica bootstrap intervals are exploratory with four or fewer replicas. Fit-window spread is a separate uncertainty.',
        'The same trajectories contribute to multiple time windows; those fits are correlated.',
        'Compare sizes at matching times. A drift with time shared by large sizes supports finite-time corrections;',
        'a size-dependent deviation at matching times supports finite-size effects. Neither outcome is assumed.', '',
        '| c | L | replicas | time window | alpha | 95% replica bootstrap |', '|---|---|---|---|---|---|']
    for r in rows:
        text.append(f'| {r["c"]} | {r["L"]} | {r["n"]} | {r["t_min"]}–{r["t_max"]} | {r["alpha"]:.3f} | {r["bootstrap_low"]:.3f}–{r["bootstrap_high"]:.3f} |')
    (output / 'REPORT.md').write_text('\n'.join(text) + '\n')
    print(output / 'REPORT.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    analyse(parser.parse_args().folder)
