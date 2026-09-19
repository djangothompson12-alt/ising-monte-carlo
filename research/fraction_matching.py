"""Known-fraction rank control, not a new physical dynamics or segmentation method."""
import numpy as np

TIE_SEEDS=(110,211,312,413,514)


def integrate(field,factor):
    a=np.asarray(field,dtype=float)
    if a.ndim not in (2,3) or not np.all(np.isfinite(a)) or np.any((a<0)|(a>1)):
        raise ValueError('Need a finite 2D/3D indicator or partial-volume field in [0,1]')
    if isinstance(factor,bool) or not isinstance(factor,int) or factor<1 or any(n%factor for n in a.shape):
        raise ValueError('Positive integer factor must divide every axis')
    shape=tuple(v for n in a.shape for v in (n//factor,factor))
    return a.reshape(shape).mean(axis=tuple(range(1,2*a.ndim,2)))


def match_fraction(averaged,fraction,seed):
    a=np.asarray(averaged,dtype=float)
    if a.ndim not in (2,3) or not np.all(np.isfinite(a)) or np.any((a<0)|(a>1)):
        raise ValueError('Need finite partial-volume values in [0,1]')
    if not np.isfinite(fraction) or not 0<=fraction<=1: raise ValueError('Invalid target fraction')
    flat=a.ravel(); k=int(np.floor(flat.size*fraction+.5))
    out=np.zeros(flat.size,dtype=np.uint8); tied=needed=0; cut=float('nan')
    if k==flat.size: out[:]=1
    elif k:
        cut=float(np.partition(flat,flat.size-k)[flat.size-k])
        out[flat>cut]=1
        candidates=np.flatnonzero(flat==cut); tied=len(candidates)
        needed=k-int(out.sum())
        # Same shape + seed produces the same coordinate priority at all times.
        priorities=np.random.default_rng(seed).random(flat.size)
        choice=candidates[np.argsort(priorities[candidates],kind='stable')[:needed]]
        out[choice]=1
    assert int(out.sum())==k
    residual=float(out.mean()-fraction)
    if abs(residual)>.5/flat.size+1e-12: raise ArithmeticError('Count matching exceeded quantization bound')
    return out.reshape(a.shape),dict(target_fraction=float(fraction),matched_fraction=float(out.mean()),
        fraction_residual=residual,quantization_bound=.5/flat.size,cutoff=cut,
        cutoff_ties=tied,ties_selected=needed,tie_seed=int(seed),foreground_count=k)
