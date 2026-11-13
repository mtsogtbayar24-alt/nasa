from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from astropy.io import fits
from astropy.wcs import WCS
from astropy.nddata import Cutout2D
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np
from PIL import Image
from io import BytesIO
from pathlib import Path
import os

app = FastAPI(title='COSMIC SHIFT API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://localhost:3000').split(','), allow_methods=['GET'], allow_headers=['*'])
DATA = Path(os.getenv('FITS_DIR', './data')).resolve()

def fits_files():
    if not DATA.exists(): return []
    return sorted(p for p in DATA.glob('*.fits') if p.is_file())

def extract(path, ra, dec, fov):
    with fits.open(path, memmap=False) as hdul:
        for hdu in hdul:
            if hdu.data is None or hdu.data.ndim != 2: continue
            try:
                wcs = WCS(hdu.header).celestial
                if not wcs.has_celestial: continue
                position = SkyCoord(ra*u.deg, dec*u.deg, frame='icrs')
                cut = Cutout2D(np.asarray(hdu.data, dtype=float), position, (fov*u.arcmin, fov*u.arcmin), wcs=wcs, mode='partial', fill_value=np.nan)
                return cut.data, {'date_obs':hdu.header.get('DATE-OBS',hdul[0].header.get('DATE-OBS')),'bunit':hdu.header.get('BUNIT'),'filename':path.name}
            except (ValueError, TypeError, KeyError): continue
    raise ValueError('No usable 2D celestial WCS image / coordinate not covered')

def png(arr):
    finite = np.isfinite(arr)
    if not finite.any(): raise ValueError('No valid pixels in cutout')
    lo, hi = np.nanpercentile(arr[finite], [2, 98])
    scaled = np.clip((arr-lo)/max(hi-lo,1e-12),0,1)
    scaled = np.nan_to_num(np.arcsinh(8*scaled)/np.arcsinh(8))
    buf=BytesIO(); Image.fromarray(np.uint8(scaled*255),mode='L').save(buf,format='PNG')
    return buf.getvalue()

@app.get('/health')
def health(): return {'status':'ok','source':'local FITS files','count':len(fits_files())}

@app.get('/epochs')
def epochs(): return [{'id':i,'filename':p.name} for i,p in enumerate(fits_files())]

@app.get('/cutout/{epoch_id}.png')
def cutout(epoch_id:int, ra:float=Query(ge=0,lt=360), dec:float=Query(ge=-90,le=90), fov:float=Query(default=5,gt=0,le=60)):
    files=fits_files()
    if epoch_id<0 or epoch_id>=len(files): raise HTTPException(404,'Epoch not found')
    try:
        arr,meta=extract(files[epoch_id],ra,dec,fov)
        return Response(content=png(arr),media_type='image/png',headers={'X-Observation-Date':str(meta['date_obs'] or 'unknown')})
    except Exception as exc: raise HTTPException(422,str(exc)) from exc

@app.get('/difference.png')
def difference(a:int,b:int,ra:float=Query(ge=0,lt=360),dec:float=Query(ge=-90,le=90),fov:float=Query(default=5,gt=0,le=60)):
    # IMPORTANT: only valid when source images already share pixel grid, WCS and photometric calibration.
    # Production must reproject, PSF-match and normalize before subtraction.
    raise HTTPException(501,'Scientific difference requires WCS reprojection and PSF/photometric matching; not implemented')
