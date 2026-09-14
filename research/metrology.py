"""Explicit alternative observables for saved Model B snapshots.

These are definitions to compare, not interchangeable physical particle radii.
Do not apply Model B's connected-correlation convention to Model A here.
"""
import numpy as np


def first_crossing(correlation, level):
    c = np.asarray(correlation, dtype=float)
    if c.ndim != 1 or len(c) < 2 or not np.all(np.isfinite(c)):
        return float('nan')
    for r in range(len(c)-1):
        if c[r] >= level > c[r+1]:
            return float(r + (c[r]-level)/(c[r]-c[r+1]))
    return float('nan')


def positive_lobe_integral(correlation):
    """Trapezoidal area from r=0 to the interpolated first zero.

    No zero within the measured range means unresolved, not a truncated length.
    """
    c = np.asarray(correlation, dtype=float)
    if c.ndim != 1 or len(c) < 2 or not np.all(np.isfinite(c)) or c[0] <= 0:
        return float('nan')
    hits = np.flatnonzero(c <= 0)
    if not len(hits):
        return float('nan')
    i = int(hits[0])
    zero = (i-1) + c[i-1]/(c[i-1]-c[i])
    # The final partial interval is a triangle with height c[i-1].
    area = np.sum((c[:i-1]+c[1:i])/2) if i > 1 else 0.
    return float(area + .5*c[i-1]*(zero-(i-1)))


def spectrum(field):
    """S(q)=|FFT(field-mean)|²/N, q in cycles/site on the full periodic grid.

    Parseval: sum(S)/N = variance(field). The zero mode is set to zero.
    """
    x = np.asarray(field,dtype=float)
    if x.ndim != 2 or min(x.shape) < 4 or not np.all(np.isfinite(x)):
        raise ValueError('Need a finite 2D field with at least four sites per axis.')
    power = abs(np.fft.fft2(x-x.mean()))**2/x.size
    power[0,0] = 0.
    fy, fx = np.meshgrid(np.fft.fftfreq(x.shape[0]),np.fft.fftfreq(x.shape[1]),indexing='ij')
    return np.hypot(fx,fy),power


def inverse_first_moment(field):
    """ell_S = sum S / sum |q|S, including every nonzero Fourier mode.

    No radial rebinning or adjustable high-q cutoff. Short-wavelength thermal
    fluctuations and sharp interfaces can bias the moment; this is a diagnostic.
    A sinusoidal field with period p has ell_S=p exactly up to FFT roundoff.
    """
    q,power = spectrum(field)
    denominator = float(np.sum(q*power))
    return float(power.sum()/denominator) if denominator > 0 else float('nan')


def snapshot_measures(lattice, correlations):
    cx,cy = np.asarray(correlations)
    x = np.asarray(lattice)
    rho = sum(np.count_nonzero(x != np.roll(x,1,axis)) for axis in (0,1))/(2*x.size)
    return dict(threshold_05=np.mean([first_crossing(cx,.5),first_crossing(cy,.5)]),
        positive_lobe=np.mean([positive_lobe_integral(cx),positive_lobe_integral(cy)]),
        spectral_moment=inverse_first_moment(x),
        inverse_interface_proxy=1/rho if rho > 0 else float('nan'))
