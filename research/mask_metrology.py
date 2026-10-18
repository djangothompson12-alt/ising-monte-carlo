"""Finite binary-mask lengths with exact checks near the half-height level.

This opt-in kernel leaves the frozen image studies unchanged. FFTs calculate
the finite covariance efficiently. At a lag within 1e-12 of one half, binary
pair counts recompute its value using integer arithmetic, so roundoff cannot
choose the wrong descending crossing. The threshold is a numerical trigger,
not an estimate of image uncertainty or a resolution criterion.
"""

from __future__ import annotations

import numpy as np

from research.imaging import finite_correlations
from research.metrology import first_crossing


def binary_correlations(mask: np.ndarray) -> tuple[np.ndarray, int]:
    if mask.ndim != 2 or mask.dtype != bool or min(mask.shape) < 4:
        raise ValueError("Need a 2D Boolean mask with at least four pixels per axis")
    correlations = finite_correlations(mask.astype(float))
    total = int(mask.size)
    count = int(np.count_nonzero(mask))
    if count in (0, total):
        return correlations, 0
    refined = 0
    for direction, axis in enumerate((1, 0)):
        candidates = np.flatnonzero(np.abs(correlations[direction] - 0.5) <= 1e-12)
        for lag in candidates:
            left_slices, right_slices = [slice(None)] * 2, [slice(None)] * 2
            left_slices[axis] = slice(0, mask.shape[axis] - int(lag))
            right_slices[axis] = slice(int(lag), None)
            left, right = mask[tuple(left_slices)], mask[tuple(right_slices)]
            pairs = int(left.size)
            both = int(np.count_nonzero(left & right))
            marginal_sum = int(np.count_nonzero(left)) + int(np.count_nonzero(right))
            numerator = total * total * both - total * count * marginal_sum + pairs * count * count
            denominator = pairs * count * (total - count)
            correlations[direction, lag] = numerator / denominator
            refined += 1
    return correlations, refined


def binary_image_length(mask: np.ndarray, pixel_size: float = 1.0) -> dict:
    if not np.isfinite(pixel_size) or pixel_size <= 0:
        raise ValueError("Pixel size must be finite and positive")
    correlations, refined = binary_correlations(mask)
    lengths = np.array([first_crossing(values, 0.5) for values in correlations]) * pixel_size
    return dict(length=float(np.mean(lengths)), length_x=float(lengths[0]),
                length_y=float(lengths[1]), resolved=bool(np.all(np.isfinite(lengths))),
                exact_half_height_checks=refined)
