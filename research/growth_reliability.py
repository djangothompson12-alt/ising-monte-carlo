"""Observation-only diagnostics; no dynamics and no claim of a new theorem.

The decimation algebra follows Ledesma-Alonso et al. PRE 97, 023304,
Eq. 34. Our directional-covariance-only length is an explicit adaptation,
NOT their minimum across all descriptors/phases.
"""
import numpy as np
from research.imaging import finite_correlations
from research.metrology import first_crossing, positive_lobe_integral


def decimation_limit(shape, characteristic_length):
    """Eq. 34 rounding, with 'no further reduction' for a negative step.

    Length is in original pixels. NaN means unresolved, not an infinite limit.
    The caller must disclose which descriptors provided the input length.
    """
    if len(shape)!=2 or any(int(n)!=n or n<4 for n in shape):
        raise ValueError('Two image dimensions of at least four required')
    if not np.isfinite(characteristic_length) or characteristic_length<=0:
        return float('nan')
    reduced=np.ceil(3*np.asarray(shape,dtype=float)/characteristic_length)
    steps=int(np.floor(np.min(np.log2(np.asarray(shape)/reduced))))
    return float(2**max(0,steps))


def correlation_measures(correlations, spacing=1.):
    if not np.isfinite(spacing) or spacing<=0: raise ValueError('Positive spacing required')
    half=np.array([first_crossing(c,.5) for c in correlations])
    lobe=np.array([positive_lobe_integral(c) for c in correlations])
    # First interpolated entrance from above into the +/- .02 band.
    near=np.array([first_crossing(c,.02) for c in correlations])
    return dict(half=float(half.mean()*spacing),lobe=float(lobe.mean()*spacing),
        min_half_pixels=float(half.min()),near_zero_min=float(near.min()*spacing))


def measures(field,spacing=1.):
    return correlation_measures(finite_correlations(field),spacing)


def log_slope(times, values):
    t=np.asarray(times,dtype=float); a=np.asarray(values,dtype=float)
    if t.ndim!=1 or a.shape!=t.shape or len(t)<4 or np.any(np.diff(t)<=0):
        return float('nan')
    if t[0]<=0 or t[-1]/t[0]<5 or not np.all(np.isfinite(a)&(a>0)):
        return float('nan')
    x=np.log(t); x-=x.mean()
    return float(x@np.log(a)/(x@x))


def paired_fit(times,native,treatment,draws=1000,seed=912):
    """Whole paired replicas; ratio of ensemble means, NOT mean of ratios.

    Slope(log treatment/native) equals slope(log treatment)-slope(log native)
    on identical times/weights. This identity explains the accounting but
    cannot independently predict bias or identify a physical cause.
    """
    a=np.asarray(native,dtype=float);b=np.asarray(treatment,dtype=float)
    if a.shape!=b.shape or a.ndim!=2 or a.shape[1]!=len(times) or a.shape[0]<2:
        raise ValueError('Matching replica-by-time arrays required')
    if not np.all(np.isfinite(a)&(a>0)&np.isfinite(b)&(b>0)):
        raise ValueError('Unresolved observations must be masked explicitly')
    ref=a.mean(axis=0);obs=b.mean(axis=0);ratio=obs/ref
    alpha0=log_slope(times,ref);alpha=log_slope(times,obs)
    ratio_slope=log_slope(times,ratio)
    if not np.isfinite(alpha):
        return dict(native_alpha=alpha0,alpha=alpha,delta=np.nan,ratio_slope=np.nan,
            identity_error=np.nan,low=np.nan,high=np.nan,ratio_first=np.nan,ratio_last=np.nan)
    delta=alpha-alpha0
    if abs(delta-ratio_slope)>1e-12: raise AssertionError('Log-slope identity failed')
    rng=np.random.default_rng(seed)
    ix=rng.integers(len(a),size=(draws,len(a)))
    x=np.log(times);x-=x.mean();weights=x/(x@x)
    bootstrap=np.log(b[ix].mean(axis=1)/a[ix].mean(axis=1))@weights
    low,high=np.percentile(bootstrap,[2.5,97.5])
    return dict(native_alpha=alpha0,alpha=alpha,delta=delta,ratio_slope=ratio_slope,
        identity_error=abs(delta-ratio_slope),low=float(low),high=float(high),
        ratio_first=float(ratio[0]),ratio_last=float(ratio[-1]))


def tolerance_label(low,high,tolerance=.02):
    """Within, outside or uncertain relative to declared numerical tolerance."""
    if not np.isfinite(low) or not np.isfinite(high): return 'unresolved'
    if low>=-tolerance and high<=tolerance: return 'within'
    if low>tolerance or high<-tolerance: return 'outside'
    return 'uncertain'
