"""Finite-image foreground chords for an exploratory observation comparison.

These are lengths of complete horizontal/vertical runs of foreground pixels,
not radii and not a uniquely correct domain size. Each run is counted once,
not once per starting pixel. Runs touching an image edge are censored rather
than wrapped or assigned their truncated length. This can introduce selection
bias as domains approach the field of view; the censored counts must therefore
accompany the length, and this measurement is not a finite-size correction.

This module does not change simulation dynamics. Its optional majority pass
is observation-only and can change the observed species fraction. Neither the
chord convention nor that pass claims an exact reproduction of a literature
measurement protocol.
"""

from __future__ import annotations

import numpy as np

from research.reference_measurements import majority_filter_once


def _binary_field(field: np.ndarray) -> np.ndarray:
    """Validate a finite 2D 0/1 mask without changing the caller's array."""
    mask = np.asarray(field)
    if (
        mask.ndim != 2
        or min(mask.shape) < 4
        or mask.dtype.kind not in "buif"
        or not np.all(np.isfinite(mask))
        or not np.all((mask == 0) | (mask == 1))
    ):
        raise ValueError("Need a finite 2D binary 0/1 mask with at least four pixels per axis")
    return mask.astype(np.int8, copy=False)


def _complete_runs(lines: np.ndarray) -> tuple[np.ndarray, int]:
    """Return complete foreground lengths and the number of truncated runs.

    Zero padding identifies runs, but never declares a border pixel to be a
    measured interface: border-touching runs are explicitly removed below.
    A line filled with foreground counts as one censored run, not two.
    """
    changes = np.diff(np.pad(lines, ((0, 0), (1, 1)), constant_values=0), axis=1)
    _, starts = np.nonzero(changes == 1)
    _, stops = np.nonzero(changes == -1)
    censored = (starts == 0) | (stops == lines.shape[1])
    return (stops - starts)[~censored], int(np.count_nonzero(censored))


def foreground_chords(field: np.ndarray, spacing: float = 1.0) -> dict[str, float | int | str]:
    """Measure number-weighted complete foreground chords in a finite image.

    ``x`` scans along columns (axis 1); ``y`` scans along rows (axis 0).
    ``spacing`` is the positive physical distance per pixel, identical along
    both axes. The pooled ``chord`` averages every retained x/y run with equal
    weight. It is resolved only if each axis supplies at least one complete
    foreground run. An axis mean may remain finite when the pooled result is
    unresolved. This function never wraps edges or changes ``field``.

    ``censored_fraction`` is a *run-count* fraction, not a pixel or phase
    fraction. It is NaN for an image with no foreground runs. No correction
    for censored lengths is attempted, and foreground/background chord means
    need not agree, especially away from equal species fractions.
    """
    mask = _binary_field(field)
    step = np.asarray(spacing)
    if step.ndim != 0 or step.dtype.kind not in "uif" or not np.isfinite(step) or step <= 0:
        raise ValueError("spacing must be one finite positive real number")
    pixel_size = float(step)
    x, censored_x = _complete_runs(mask)
    y, censored_y = _complete_runs(mask.T)
    count_x, count_y = len(x), len(y)
    complete = count_x + count_y
    censored = censored_x + censored_y
    total = complete + censored
    if count_x and count_y:
        status = "resolved"
        chord = pixel_size * float((x.sum() + y.sum()) / complete)
    else:
        missing = "both" if not count_x and not count_y else ("x" if not count_x else "y")
        status = "unresolved_no_complete_chords_" + missing
        chord = float("nan")
    return {
        "chord": chord,
        "chord_x": pixel_size * float(x.mean()) if count_x else float("nan"),
        "chord_y": pixel_size * float(y.mean()) if count_y else float("nan"),
        "complete_chords": complete,
        "complete_x": count_x,
        "complete_y": count_y,
        "censored_foreground_runs": censored,
        "censored_x": censored_x,
        "censored_y": censored_y,
        "censored_fraction": censored / total if total else float("nan"),
        "status": status,
    }


def majority_observation(field: np.ndarray) -> np.ndarray:
    """Apply one simultaneous periodic five-site majority pass to a saved mask.

    Unlike chord measurement, this observation filter uses the simulation's
    periodic neighbours. The returned mask must not be fed back into the
    dynamics: the operation can change composition and morphology. It keeps
    the image dimensions and pixel spacing unchanged.
    """
    mask = _binary_field(field)
    filtered = majority_filter_once(mask * 2 - 1)
    return ((filtered + 1) // 2).astype(np.uint8)
