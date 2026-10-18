# Key figure from the pre-declared bins (l128_resolution_reanalysis/bin_slopes.csv), matched stage only.
import csv, os, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(f'{HERE}/../l128_resolution_reanalysis/bin_slopes.csv')))
MID = {'[0,1)': .5, '[1,2)': 1.5, '[2,3)': 2.5, '[3,5)': 4.0}
SER = [('c0', '50:50', '#2a78d6', 'o', -0.06), ('c1', '15:85', '#eb6834', 's', 0.06)]
INK, MUTED, GRID = '#1f1f1e', '#6b6b68', '#e6e6e3'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED})
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True, facecolor='#fcfcfb')
for ax, k in zip(axes, ('2', '4')):
    ax.set_facecolor('#fcfcfb')
    ax.axhspan(-.02, .02, color='#ececea', zorder=0); ax.axhline(0, color=MUTED, lw=.8, zorder=1)
    ax.text(4.55, .016, '±0.02 tolerance', color=MUTED, fontsize=7.5, ha='right', va='top')
    for comp, name, col, mk, dx in SER:
        pts = [(MID[r['bin']], float(r['estimate']), float(r['ci_low']), float(r['ci_high'])) for r in rows
               if r['composition'] == comp and r['factor'] == k and r['stage'] == 'matched' and r['bin'] in MID and r['estimate'] != 'nan']
        x, y, lo, hi = map(np.array, zip(*pts)); x = x + dx
        ax.plot(x, y, color=col, lw=2, zorder=3)
        ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt=mk, ms=6, color=col, mec='#fcfcfb', mew=1.5, elinewidth=1.2, capsize=0, zorder=4, label=name)
    ax.set_xticks([.5, 1.5, 2.5, 4.0]); ax.set_xticklabels(['<1', '1–2', '2–3', '3–5'])
    ax.set_xlim(0, 4.6); ax.set_ylim(-.075, .025); ax.grid(axis='y', color=GRID, lw=.6); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.set_title(f'{k}× coarser image', color=INK, fontsize=9.5, loc='left')
    ax.set_xlabel('Native domain size (coarse pixels)')
axes[0].set_ylabel('Exponent error\n(coarse − native)')
axes[0].legend(frameon=False, loc='lower right', fontsize=8.5, title='Species ratio', title_fontsize=8)
fig.text(.01, -.04, 'Fraction-matched images, 16 L=128 trajectories per ratio, 0.65 Tc. Bars: 95% whole-trajectory bootstrap. '
         'Bins pre-declared; missing points\nwere not estimable or not reached by 1M sweeps. Larger sizes occur only at later times.',
         fontsize=7, color=MUTED)
fig.tight_layout(); fig.savefig(f'{HERE}/key_figure_shift_vs_pixels.png', dpi=220, bbox_inches='tight', facecolor='#fcfcfb')
