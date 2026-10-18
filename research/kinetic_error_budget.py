"""A deterministic processing-error budget for a fixed log-log OLS fit.

This is elementary linear-regression error propagation, not a new growth law
or an experimental uncertainty model. Ratios compare processed and native
measurements of the same saved data. A native measurement is not ground truth.
"""

from __future__ import annotations

import numpy as np


def log_time_weights(times) -> np.ndarray:
    t = np.asarray(times, dtype=float)
    if (t.ndim != 1 or t.size < 2 or not np.all(np.isfinite(t))
            or np.any(t <= 0) or np.any(np.diff(t) <= 0)):
        raise ValueError("Need at least two finite, positive, strictly increasing times")
    x = np.log(t)
    centred = x - x.mean()
    denominator = float(centred @ centred)
    if not np.isfinite(denominator) or denominator <= 0:
        raise ValueError("Log-time grid is numerically degenerate")
    return centred / denominator


def ratio_envelope_bound(times, lower: float, upper: float) -> float:
    """Sharp worst-case absolute slope shift for lower <= q_i <= upper.

    For equal-weight OLS with an intercept, delta alpha = sum_i w_i log q_i.
    The upper bound is attained by assigning upper to positive weights and
    lower to negative weights (the reverse attains its negative). This box
    need not describe a physically realisable image-processing trajectory.
    """
    if (not np.isfinite(lower) or not np.isfinite(upper)
            or not 0 < lower <= upper):
        raise ValueError("Need positive finite ordered ratio limits")
    weights = log_time_weights(times)
    positive_mass = float(np.sum(np.abs(weights)) / 2)
    return positive_mass * float(np.log(upper) - np.log(lower))


def static_tolerance_bound(times, relative_tolerance: float) -> float:
    """Bound slope error if EVERY retained ratio is in [1-epsilon,1+epsilon]."""
    if (isinstance(relative_tolerance, (bool, np.bool_))
            or not np.isfinite(relative_tolerance) or not 0 <= relative_tolerance < 1):
        raise ValueError("Static relative tolerance must be in [0,1)")
    weights = log_time_weights(times)
    positive_mass = float(np.sum(np.abs(weights)) / 2)
    # log1p avoids loss of precision for very small tolerances.
    return positive_mass * float(np.log1p(relative_tolerance) - np.log1p(-relative_tolerance))


def required_static_tolerance(times, exponent_tolerance: float) -> float:
    """Sufficient common per-time relative tolerance for a fixed slope budget.

    epsilon <= tanh(delta_alpha_budget / (2 * sum_{w>0} w)). This is a
    sufficient bound, not a necessary criterion or a resolution selector.
    """
    if (isinstance(exponent_tolerance, (bool, np.bool_))
            or not np.isfinite(exponent_tolerance) or exponent_tolerance < 0):
        raise ValueError("Exponent tolerance must be finite and non-negative")
    positive_mass = float(np.sum(np.abs(log_time_weights(times))) / 2)
    return float(np.tanh(exponent_tolerance / (2 * positive_mass)))


def paired_budget(times, native, processed) -> dict:
    """Known-data accounting for two positive length series, no missing-data selection."""
    weights = log_time_weights(times)
    native, processed = np.asarray(native, dtype=float), np.asarray(processed, dtype=float)
    if (native.shape != weights.shape or processed.shape != weights.shape
            or not np.all(np.isfinite(native) & (native > 0))
            or not np.all(np.isfinite(processed) & (processed > 0))):
        raise ValueError("Positive resolved native/processed series must share the entire time grid")
    log_ratio = np.log(processed) - np.log(native)
    ratio = processed / native
    if not np.all(np.isfinite(ratio) & (ratio > 0)):
        raise ValueError("Processed/native ratio is outside the finite floating-point range")
    alpha_native = float(weights @ np.log(native))
    alpha_processed = float(weights @ np.log(processed))
    delta = alpha_processed - alpha_native
    ratio_slope = float(weights @ log_ratio)
    bound = ratio_envelope_bound(times, float(ratio.min()), float(ratio.max()))
    slack = 1e-12 * max(1., abs(delta), bound)
    if abs(delta - ratio_slope) > slack or abs(delta) > bound + slack:
        raise ArithmeticError("Regression accounting or ratio-envelope bound failed")
    return dict(native_alpha=alpha_native, processed_alpha=alpha_processed,
                delta=delta, log_ratio_slope=ratio_slope,
                identity_error=abs(delta - ratio_slope),
                ratio_min=float(ratio.min()), ratio_max=float(ratio.max()),
                max_relative_length_change=float(np.max(np.abs(ratio - 1))),
                observed_ratio_envelope_bound=bound)
