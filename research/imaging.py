"""Finite-window image metrology. This never advances or edits an Ising lattice.

Image centring is a measurement convention, not the Model A/B engine convention.
No opposite image edges are paired. Pixel spacing must be propagated explicitly.
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from research.metrology import first_crossing


def validate_image(field):
    x=np.asarray(field,dtype=float)
    if x.ndim!=2 or min(x.shape)<4 or not np.all(np.isfinite(x)):
        raise ValueError('Need a finite 2D image, at least 4 pixels per axis.')
    return x


def finite_correlations(field):
    """C_a(r)=sum_valid z_i*z_(i+r) / N_pairs(r) / mean(z²).

    z=image-image.mean(). Zero padding gives linear, not circular, correlation.
    The local mean is estimated: pair-count normalisation is not a claim of an
    unbiased covariance estimator. Return horizontal then vertical axes.
    """
    x=validate_image(field)
    z=x-x.mean()
    variance=np.mean(z*z)
    rmax=min(x.shape)//2
    if variance<=np.finfo(float).eps:
        return np.full((2,rmax+1),np.nan)
    result=[]
    for axis in (1,0):
        n=x.shape[axis]
        f=np.fft.rfft(z,n=2*n,axis=axis)
        corr=np.fft.irfft(abs(f)**2,n=2*n,axis=axis)
        sums=np.sum(corr,axis=1-axis)[:rmax+1]
        pairs=x.shape[1-axis]*(n-np.arange(rmax+1))
        result.append(sums/pairs/variance)
    return np.asarray(result)


def image_length(field,pixel_size=1.):
    if not np.isfinite(pixel_size) or pixel_size<=0:
        raise ValueError('Pixel size must be finite and positive.')
    c=finite_correlations(field)
    lengths=np.array([first_crossing(v,.5) for v in c])*pixel_size
    return dict(length=float(np.mean(lengths)),length_x=float(lengths[0]),
                length_y=float(lengths[1]),resolved=bool(np.all(np.isfinite(lengths))))


def block_average(field,factor):
    x=validate_image(field)
    if not isinstance(factor,(int,np.integer)) or factor<1 or any(n%factor for n in x.shape):
        raise ValueError('Positive integer factor must divide both image dimensions.')
    h,w=x.shape
    if min(h,w)//factor<4:
        raise ValueError('Reduction leaves fewer than four pixels per axis.')
    return x.reshape(h//factor,factor,w//factor,factor).mean(axis=(1,3))


def observe(field,*,factor=1,sigma=0.,threshold=0.):
    """Reflect-edge blur, block pixel integration, then binary segmentation.

    Input -1/+1 convention, output -1/+1; exact threshold ties go to +1.
    That deterministic tie convention can change apparent phase fraction.
    """
    x=validate_image(field)
    if not np.isfinite(sigma) or sigma<0 or not np.isfinite(threshold):
        raise ValueError('Invalid blur or threshold.')
    gray=gaussian_filter(x,sigma,mode='reflect') if sigma else x.copy()
    gray=block_average(gray,factor)
    return np.where(gray>=threshold,1.,-1.)


def corner_crops(field,width):
    x=validate_image(field)
    if not isinstance(width,int) or width<4 or width>min(x.shape):
        raise ValueError('Crop width must be an integer inside the image.')
    h,w=x.shape
    origins=list(dict.fromkeys(((0,0),(0,w-width),(h-width,0),(h-width,w-width))))
    return [(origin,x[origin[0]:origin[0]+width,origin[1]:origin[1]+width].copy()) for origin in origins]
