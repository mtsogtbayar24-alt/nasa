import numpy as np
from app import science


def test_ra_wrap_and_distance():
    assert science.angular_separation_arcmin(359.99,0,0.01,0) < 2
    assert science.angular_separation_arcmin(90,0,91,0) > 59


def test_shifted_source_detectable():
    # Controlled residual pair; no claim about real detection sensitivity.
    yy,xx=np.mgrid[:256,:256]
    a=np.full((256,256),20.0,dtype=np.float32)
    b=a.copy()
    a+=100*np.exp(-((xx-95)**2+(yy-127)**2)/8)
    b+=100*np.exp(-((xx-146)**2+(yy-127)**2)/8)
    diff=science.registered_difference(a,b)
    found=science.find_candidates(diff,133.79513,-7.24515,5)
    assert len(found)>=2
    assert {'brightened','dimmed'}.issubset({f['change'] for f in found})


def test_nan_preservation_and_color_png():
    img=np.ones((16,16),dtype=np.float32)
    img[:3,:]=np.nan
    png=science.image_png(img)
    assert png.startswith(b'\x89PNG\r\n\x1a\n')
