"""Reference observables used when reproducing older 2D Kawasaki studies.

This module is intentionally separate from the Model B engine and from the
primary analysis.  A single majority-spin pass is an *observation* operation:
it can change a saved image and does not conserve composition, so it must
never be fed back into Kawasaki dynamics or silently replace raw snapshots.

The implementation supports a faithful, declared comparison with studies that
measure post-processed chord lengths and first-zero raw correlations. It does
not claim that this processing is universally correct or suitable for the
off-critical compositions in the main study.
"""

from __future__ import annotations

import numpy as np

from research.metrology import first_crossing, inverse_first_moment


def _binary_lattice(lattice: np.ndarray) -> np.ndarray:
    spins = np.asarray(lattice)
    if spins.ndim != 2 or min(spins.shape) < 4 or not np.all(np.isin(spins, (-1, 1))):
        raise ValueError("Need a 2D +/-1 lattice with at least four sites per axis")
    return spins.astype(np.int8, copy=False)


def majority_filter_once(lattice: np.ndarray) -> np.ndarray:
    """Return one non-mutating 5-site majority-spin pass under periodic edges.

    Each output spin is the majority among itself and its four nearest
    neighbours. Five values prevent ties. This mirrors the one-pass filter
    used as thermal-noise post-processing in the selected reference work;
    repeated passes are intentionally not provided because they change domain
    morphology further and need a separately justified protocol.
    """
    spins = _binary_lattice(lattice)
    neighbourhood = spins.astype(np.int16)
    for axis in (0, 1):
        neighbourhood += np.roll(spins, 1, axis=axis)
        neighbourhood += np.roll(spins, -1, axis=axis)
    return np.where(neighbourhood > 0, 1, -1).astype(np.int8)


def raw_axis_correlations(lattice: np.ndarray, r_max: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Return uncentred periodic raw correlations along x and y axes.

    This is deliberately raw, rather than Model B's connected correlation,
    because the reference definition is intended only for a symmetric
    benchmark after its declared image filter. It should not replace the
    connected off-critical analysis in ``model_b.kawasaki_engine``.
    """
    spins = _binary_lattice(lattice).astype(float)
    L = spins.shape[0]
    if r_max is None:
        r_max = L // 2
    if not isinstance(r_max, (int, np.integer)) or not 0 <= r_max <= L // 2:
        raise ValueError("r_max must be an integer in [0, L/2]")
    autocorr = np.fft.ifft2(np.abs(np.fft.fft2(spins)) ** 2).real / spins.size
    return autocorr[0, : r_max + 1], autocorr[: r_max + 1, 0]


def periodic_chord_lengths(lattice: np.ndarray, axis: int) -> np.ndarray:
    """Return every finite same-spin chord length along one periodic axis.

    Uniform lines have no interfaces and therefore no finite chord length;
    they are omitted rather than fabricated as an ``L``-site chord.
    """
    spins = _binary_lattice(lattice)
    if axis not in (0, 1):
        raise ValueError("axis must be 0 or 1")
    lines = np.moveaxis(spins, axis, -1).reshape(-1, spins.shape[axis])
    lengths: list[int] = []
    for line in lines:
        change = np.flatnonzero(line != np.roll(line, 1))
        if not len(change):
            continue
        start = int(change[0])
        rotated = np.roll(line, -start)
        boundaries = np.flatnonzero(rotated[1:] != rotated[:-1]) + 1
        edges = np.r_[0, boundaries, len(rotated)]
        lengths.extend(np.diff(edges).tolist())
    return np.asarray(lengths, dtype=float)


def reference_measurements(lattice: np.ndarray) -> dict[str, float]:
    """Return declared post-processing diagnostics for a symmetric benchmark.

    ``mean_chord_length`` is the mean of all resolved horizontal and vertical
    chords. ``first_zero_correlation`` averages raw-axis first zeros.
    ``spectral_moment`` is included only as a diagnostic; it retains the full
    spectrum definition used elsewhere in the repository.
    """
    filtered = majority_filter_once(lattice)
    x_chords = periodic_chord_lengths(filtered, axis=1)
    y_chords = periodic_chord_lengths(filtered, axis=0)
    chords = np.r_[x_chords, y_chords]
    cx, cy = raw_axis_correlations(filtered)
    zeros = np.asarray([first_crossing(cx, 0.0), first_crossing(cy, 0.0)])
    return dict(
        mean_chord_length=float(np.mean(chords)) if len(chords) else float("nan"),
        first_zero_correlation=float(np.mean(zeros)) if np.all(np.isfinite(zeros)) else float("nan"),
        spectral_moment=inverse_first_moment(filtered),
    )
