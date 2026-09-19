"""Designed image controls, not simulated kinetics or a new imaging theory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from research.fraction_matching import integrate, match_fraction, TIE_SEEDS
from research.growth_reliability import measures, log_slope
from research.imaging import finite_correlations

WIDTHS = (4, 8, 16, 32, 64)
FACTORS = (2, 4, 8)
ORIGINS = ((0, 0), (1, 1), (2, 2), (3, 3))


def checkerboard(size, width):
    if not isinstance(size, int) or not isinstance(width, int) or width < 2 or size % (2*width):
        raise ValueError('Even whole periods must tile the square')
    y, x = np.indices((size, size))
    return ((x//width + y//width) % 2).astype(np.uint8)


def balanced_defects(field, fraction=.01, seed=0):
    """Flip equal counts from each phase; no thermal interpretation."""
    a = np.asarray(field)
    if a.ndim != 2 or not np.all((a == 0) | (a == 1)) or not 0 <= fraction <= 1:
        raise ValueError('Binary image and fraction in [0,1] required')
    out = a.copy().ravel()
    groups = [np.flatnonzero(out == phase) for phase in (0, 1)]
    count = int(np.floor(fraction * min(map(len, groups))))
    rng = np.random.default_rng(seed)
    for phase, group in enumerate(groups):
        out[rng.choice(group, count, replace=False)] = 1-phase
    assert out.sum() == a.sum()
    return out.reshape(a.shape)


def direct_correlations(field, periodic=False):
    """Independent real-space reference; no FFT and no opposite edges if finite."""
    z = np.asarray(field, dtype=float)
    z = z-z.mean()
    variance = np.mean(z*z)
    rmax = min(z.shape)//2
    if variance == 0:
        return np.full((2, rmax+1), np.nan)
    result = []
    for axis in (1, 0):
        row = []
        for r in range(rmax+1):
            if periodic:
                product = z*np.roll(z, -r, axis=axis)
            else:
                left, right = [slice(None)]*2, [slice(None)]*2
                if r:
                    left[axis], right[axis] = slice(None, -r), slice(r, None)
                product = z[tuple(left)]*z[tuple(right)]
            row.append(float(product.mean()/variance))
        result.append(row)
    return np.asarray(result)


def sequential_binary(field, factor):
    """Repeated factor-two integration and thresholding, not one large block."""
    if not isinstance(factor, int) or factor < 1 or factor & (factor-1):
        raise ValueError('Power-of-two factor required')
    out = np.asarray(field).copy()
    while factor > 1:
        out = (integrate(out, 2) >= .5).astype(np.uint8)
        factor //= 2
    return out


def clean_json(obj):
    if isinstance(obj, dict): return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [clean_json(v) for v in obj]
    if isinstance(obj, (float, np.floating)) and not np.isfinite(obj): return None
    if isinstance(obj, np.generic): return obj.item()
    return obj


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output):
    output = Path(output)
    if output.exists(): raise FileExistsError('Use a new output directory')
    observations, fits, checks = [], [], []
    for width in WIDTHS:
        field = checkerboard(256, width)
        finite = direct_correlations(field)
        periodic = direct_correlations(field, periodic=True)
        analytic = 1-2*np.arange(width+1)/width
        fft_error = float(np.max(np.abs(finite-finite_correlations(field))))
        analytic_error = float(np.max(np.abs(periodic[:, :width+1]-analytic)))
        if max(fft_error, analytic_error) > 1e-12: raise AssertionError('Reference failed')
        checks.append(dict(width=width, fft_error=fft_error, analytic_error=analytic_error))
    for variant in ('clean', 'paired_defects'):
        for factor in FACTORS:
            for origin in ORIGINS:
                history = {name: [] for name in ('native', 'integrated', 'fixed', 'matched')}
                for width in WIDTHS:
                    a = checkerboard(256, width)
                    if variant == 'paired_defects':
                        a = balanced_defects(a, seed=20260920+width)
                    a = np.roll(a, origin, axis=(0, 1))
                    gray = integrate(a, factor)
                    fields = dict(native=[a], integrated=[gray], fixed=[gray >= .5],
                                  matched=[match_fraction(gray, .5, seed)[0] for seed in TIE_SEEDS])
                    for stage, images in fields.items():
                        lengths = [measures(b, 1 if stage == 'native' else factor) for b in images]
                        # A single unresolved tie keeps the mean unresolved (no nanmean).
                        row = dict(variant=variant, factor=factor, origin=list(origin), width=width,
                                   artificial_time=width**3, stage=stage,
                                   analytic_periodic_clean_length=width/4,
                                   fraction_mean=float(np.mean([b.mean() for b in images])),
                                   fraction_max_error=float(max(abs(b.mean()-.5) for b in images)),
                                   half=float(np.mean([m['half'] for m in lengths])),
                                   lobe=float(np.mean([m['lobe'] for m in lengths])),
                                   tie_half=[m['half'] for m in lengths] if stage == 'matched' else [],
                                   tie_lobe=[m['lobe'] for m in lengths] if stage == 'matched' else [])
                        observations.append(row); history[stage].append(row)
                times = np.array(WIDTHS, dtype=float)**3
                for observable in ('half', 'lobe'):
                    native = log_slope(times, [r[observable] for r in history['native']])
                    for stage, rows in history.items():
                        alpha = log_slope(times, [r[observable] for r in rows])
                        fits.append(dict(variant=variant, factor=factor, origin=list(origin),
                                         observable=observable, stage=stage, native_alpha=native,
                                         alpha=alpha, delta=alpha-native,
                                         resolved_all_widths=bool(np.isfinite(alpha))))
    output.mkdir(parents=True)
    alias = checkerboard(256, 4)
    gray = integrate(alias, 8)
    matched = match_fraction(gray, .5, TIE_SEEDS[0])[0]
    alias_record = dict(integrated_min=float(gray.min()), integrated_max=float(gray.max()),
                        integrated_variance=float(gray.var()), matched_fraction=float(matched.mean()),
                        matched_half=measures(matched, 8)['half'])
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.8), layout='constrained')
    for ax, field, title in zip(axes, (alias[:64, :64], gray[:8, :8], matched[:8, :8]),
            ('Known boundaries', 'Block averaging: no contrast', 'Forced 50:50: invented pattern')):
        ax.imshow(field, cmap='gray', vmin=0, vmax=1, interpolation='nearest', extent=(0,64,64,0))
        ax.set_title(title, fontsize=10); ax.set_xlabel('Native-pixel coordinate')
    axes[0].set_ylabel('Native-pixel coordinate')
    fig.suptitle('Designed aliasing example — not an alloy micrograph', fontsize=12)
    fig.savefig(output/'aliasing.png', dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10.2,4.2), layout='constrained')
    for ax, observable in zip(axes, ('half','lobe')):
        for stage, marker in (('native','o'),('integrated','s'),('fixed','^'),('matched','x')):
            subset = [r for r in observations if r['variant']=='clean' and r['factor']==4
                      and r['origin']==[1,1] and r['stage']==stage]
            ax.plot(WIDTHS, [r[observable]/(r['width']/4) for r in subset], marker=marker, label=stage)
        ax.axhline(1, color='black', linestyle=':', linewidth=1)
        ax.set(xscale='log', xlabel='Square width (native pixels)',
               ylabel='Measured / analytic periodic length', title=observable.replace('half','Half-height').replace('lobe','Positive-lobe integral'))
        ax.set_xticks(WIDTHS, labels=[str(w) for w in WIDTHS])
        ax.minorticks_off()
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Finite-image measurement: clean checkerboards, factor 4, shift (1,1)',fontsize=11)
    fig.savefig(output/'length_controls.png',dpi=170); plt.close(fig)
    report = dict(observations=observations, fits=fits, direct_checks=checks, aliasing=alias_record,
                  caveat='Artificial scale series; no MCS, no experimental data, no novelty claim. Unresolved fits retained.')
    (output/'results.json').write_text(json.dumps(clean_json(report), indent=2, allow_nan=False)+'\n')
    body = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Controlled image checks</title>
<style>body{font:17px/1.6 system-ui;max-width:960px;margin:40px auto;padding:0 20px;color:#18232c}img{width:100%}h1{line-height:1.2}.note{background:#fff2cf;padding:16px}a{color:#145a85}</style>
<h1>Does preserving composition preserve structure?</h1><p>Controlled images, 20 September 2026. AI-assisted analysis for student review.</p>
<p class="note">These are designed checkerboards, not new Kawasaki runs or experimental alloy images. Their growth is prescribed, not discovered. The known formula applies to periodic measurements; the deployed image tool has finite boundaries.</p>
<h2>A useful failure case</h2><p>A factor-eight block contains equal amounts of both phases when squares are four pixels wide. Every block therefore becomes 0.5. A binary mask forced to be half-filled has the right fraction but cannot recover the erased boundaries. Its pattern reflects the declared tie-breaking rule.</p>
<img src="aliasing.png" alt="Native checkerboard, uniform averaged field and arbitrary half-filled coarse mask"><p>Matching is exact over the whole mask; these panels show the same 64-by-64-native-pixel region, whose local fraction may differ.</p>
<h2>A test with known lengths</h2><p>Five square widths, three reduction factors, four translations, clean and paired-defect variants, and two length definitions are retained. The analytic periodic length is one-quarter of the square width. Assigning t = width cubed produces a one-third slope by construction; this is not physical time. All fits use all five widths. Missing lengths remain unresolved.</p>
<img src="length_controls.png" alt="Finite-image lengths relative to known periodic lengths">
<p>Results distinguish the finite native baseline from the ideal periodic formula. These controls expose measurement behaviour but do not identify the unique cause of the Kawasaki result. Translations move both the grid and measurement boundary. The balanced defects are not a thermal model.</p>
<p><a href="results.json">All observations, fits and direct checks</a> · <a href="manifest.json">Reproducibility record</a></p></html>'''
    (output/'report.html').write_text(body)
    sources = [Path('research/geometry_controls.py'), Path('research/GEOMETRY_CONTROL_PROTOCOL_2026-09-20.md'),
               Path('research/fraction_matching.py'), Path('research/growth_reliability.py'),
               Path('research/imaging.py'), Path('research/metrology.py')]
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256={str(p):sha(p) for p in sources},
                    output_sha256={p.name:sha(p) for p in sorted(output.iterdir())},
                    numpy_version=np.__version__, observations=len(observations), fits=len(fits))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return dict(output=str(output), observations=len(observations), fits=len(fits), aliasing=alias_record)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    print(json.dumps(run(parser.parse_args().output),indent=2))
