"""Opt-in numerical boundary refinement for future finite-image analyses.

Frozen historical analyses are deliberately unchanged. Near a decision level,
recompute the covariance from valid pixel pairs rather than deciding from FFT
roundoff. The tolerance selects points to recompute; it does NOT snap their
values to a threshold. This is a numerical check, not a noise-removal filter.
"""
import numpy as np

from research.imaging import finite_correlations, validate_image
from research.growth_reliability import correlation_measures


def refined_correlations(field, tolerance=1e-12):
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Tolerance must be finite and nonnegative')
    x = validate_image(field)
    c = finite_correlations(x)
    z = x-x.mean()
    variance = np.mean(z*z)
    if variance <= np.finfo(float).eps:
        return c
    for direction, axis in enumerate((1, 0)):
        candidate = np.any(np.abs(c[direction, :, None]-np.array([0., .02, .5])) <= tolerance, axis=1)
        for lag in np.flatnonzero(candidate):
            left, right = [slice(None)]*2, [slice(None)]*2
            left[axis] = slice(0, x.shape[axis]-lag)
            right[axis] = slice(lag, None)
            c[direction, lag] = np.mean(z[tuple(left)]*z[tuple(right)])/variance
    return c


def refined_measures(field, spacing=1., tolerance=1e-12):
    return correlation_measures(refined_correlations(field, tolerance), spacing)
