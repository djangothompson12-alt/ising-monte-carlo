"""Finite, nonperiodic 3D measurements; axes are always z, y, x."""
from __future__ import annotations

import numpy as np
from research.metrology import first_crossing, positive_lobe_integral


def volume(field):
    x = np.asarray(field)
    if x.ndim != 3 or min(x.shape) < 4 or not np.all(np.isfinite(x)):
        raise ValueError('Need a finite 3D array with at least four voxels per axis')
    return x


def block_mean(field, factor):
    x = volume(field)
    if (isinstance(factor, bool) or not isinstance(factor, (int, np.integer))
            or factor < 1 or any(n % factor for n in x.shape)
            or min(x.shape) // factor < 4):
        raise ValueError('Factor must divide all three dimensions and leave four voxels')
    z, y, w = x.shape
    return x.reshape(z//factor, factor, y//factor, factor,
                     w//factor, factor).mean(axis=(1, 3, 5))


def axis_correlations(field, chunk_lines=1024):
    """Linear FFT sums over actual within-volume pairs, never wrapped edges.

    A local mean is estimated, so dividing by pair counts does not make this
    an unbiased covariance estimator. Chunking bounds FFT temporary memory.
    """
    x = volume(field)
    mean = float(np.mean(x))
    variance = float(np.var(x, dtype=np.float64))
    result = []
    for axis in range(3):
        n = x.shape[axis]
        lags = np.arange(n // 2 + 1)
        if variance <= np.finfo(float).eps:
            result.append(np.full(len(lags), np.nan))
            continue
        lines = np.moveaxis(x, axis, -1).reshape(-1, n)
        sums = np.zeros(len(lags))
        for start in range(0, len(lines), chunk_lines):
            centred = lines[start:start+chunk_lines].astype(float) - mean
            f = np.fft.rfft(centred, n=2*n, axis=1)
            corr = np.fft.irfft(abs(f)**2, n=2*n, axis=1)
            sums += corr[:, :len(lags)].sum(axis=0)
        result.append(sums / (len(lines) * (n-lags)) / variance)
    return result


def chord_summary(field, spacing):
    """Pool complete chords; boundary runs are censored, never joined.

    Each finite chord is counted once; this is number weighting. Dropping
    boundary-touching runs favours short chords in small fields, so counts
    and excluded-run counts are required alongside the statistic.
    """
    x = volume(field)
    if not np.all((x == 0) | (x == 1)):
        raise ValueError('Chord measurement requires a binary 0/1 volume')
    total_length = 0.
    count = censored = 0
    for axis in range(3):
        lines = np.moveaxis(x, axis, -1).reshape(-1, x.shape[axis])
        for line in lines:
            changes = np.flatnonzero(line[1:] != line[:-1]) + 1
            censored += 2 if len(changes) else 1
            lengths = np.diff(changes)
            total_length += float(lengths.sum()) * spacing[axis]
            count += len(lengths)
    return dict(chord_length=total_length/count if count else np.nan,
                complete_chords=count, censored_boundary_runs=censored)


def measure(field, spacing, binary=False):
    x = volume(field)
    spacing = np.asarray(spacing, dtype=float)
    if spacing.shape != (3,) or not np.all(np.isfinite(spacing) & (spacing > 0)):
        raise ValueError('Declare positive finite voxel spacings in z,y,x order')
    correlations = axis_correlations(x)
    half = [first_crossing(c, .5)*s for c, s in zip(correlations, spacing)]
    lobe = [positive_lobe_integral(c)*s for c, s in zip(correlations, spacing)]
    result = dict(mean_value=float(x.mean()),
                  half_height=float(np.mean(half)), positive_lobe=float(np.mean(lobe)),
                  half_height_status='resolved' if np.all(np.isfinite(half)) else 'unresolved',
                  chord_length=np.nan, complete_chords=0, censored_boundary_runs=0)
    for name, h, p in zip(('z', 'y', 'x'), half, lobe):
        result[f'half_height_{name}'] = float(h)
        result[f'positive_lobe_{name}'] = float(p)
    if binary:
        result.update(chord_summary(x, spacing))
    return result
