"""COSMIC SHIFT API v0.2 — self-contained synthetic demo + local real-FITS adapter."""
import os
import numpy as np
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from . import science

DATA_DIR = Path(os.getenv('FITS_DIR', str(Path(__file__).resolve().parents[1] / 'data'))).resolve()
app = FastAPI(title='COSMIC SHIFT API', version='0.2.0', description='Exploratory multi-epoch sky viewer; not a validated SPHEREx archive client.')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','), allow_methods=['GET'], allow_headers=['*'])

RA = Query(ge=0, lt=360)
DEC = Query(ge=-90, le=90)
FOV = Query(default=5, gt=0, le=20)


def all_epochs():
    return science.list_epochs(DATA_DIR)


def get_epoch(epoch_id: str):
    epoch = next((e for e in all_epochs() if e.id == epoch_id), None)
    if epoch is None:
        raise HTTPException(404, 'Epoch not found; check /epochs for available IDs')
    return epoch


def eligible(ra: float, dec: float, fov: float, band: str | None = None):
    return [e for e in all_epochs() if science.covered(e, ra, dec, fov) and (band is None or e.band == band)]


def pair(a: str, b: str):
    ea, eb = get_epoch(a), get_epoch(b)
    if ea.id == eb.id:
        raise HTTPException(422, 'Choose two different observations')
    if ea.band != eb.band or ea.bunit != eb.bunit:
        raise HTTPException(422, 'Compare only matching bands and matching physical units')
    if ea.kind != eb.kind or ea.target != eb.target:
        raise HTTPException(422, 'Do not compare unrelated target fields or dataset types')
    return ea, eb


def extract(e, ra, dec, fov):
    try:
        arr = science.aligned_image(e, ra, dec, fov)
        if not np.isfinite(arr).any():
            raise ValueError('Outside observation coverage')
        return arr
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get('/health')
def health():
    epochs = all_epochs()
    return {'status':'ok', 'version':'0.2.0', 'astropy_available':science.HAS_ASTROPY,
            'image_count':len(epochs), 'synthetic_count':sum(x.kind=='demo' for x in epochs),
            'real_fits_count':sum(x.kind=='fits' for x in epochs),
            'archive_connected':False}


@app.get('/targets')
def targets():
    return [
        {'name':'WISE 0855 field (synthetic)', 'ra':133.79513,'dec':-7.24515, 'fov':5, 'synthetic':True},
        {'name':'RW Aurigae field (synthetic)', 'ra':76.956,'dec':30.402, 'fov':5, 'synthetic':True},
    ]


@app.get('/epochs')
def epochs(ra: float | None = Query(None, ge=0, lt=360),
           dec: float | None = Query(None, ge=-90, le=90),
           fov: float = FOV, band: str | None = None):
    if (ra is None) != (dec is None):
        raise HTTPException(422, 'RA and Dec must be supplied together')
    items = all_epochs() if ra is None else eligible(ra, dec, fov, band)
    return [e.public() for e in items if band is None or e.band == band]


@app.get('/cutout/{epoch_id}.png')
def cutout(epoch_id: str, ra: float = RA, dec: float = DEC, fov: float = FOV):
    e = get_epoch(epoch_id)
    arr = extract(e, ra, dec, fov)
    peer_epochs = [x for x in eligible(ra, dec, fov, e.band) if x.target == e.target and x.kind == e.kind]
    try:
        lo, hi = science.shared_limits([extract(x, ra, dec, fov) for x in peer_epochs])
        data = science.image_png(arr, lo, hi)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(data, media_type='image/png', headers={
        'X-Data-Provenance':e.source, 'X-Observation-Date':e.date_obs,
        'X-Science-Status':'exploratory-not-validated', 'Cache-Control':'public, max-age=300'})


@app.get('/difference.png')
def difference(a: str, b: str, ra: float = RA, dec: float = DEC, fov: float = FOV):
    ea, eb = pair(a,b)
    try:
        diff = science.registered_difference(extract(ea,ra,dec,fov),extract(eb,ra,dec,fov))
        data = science.difference_png(diff)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(data, media_type='image/png', headers={
        'X-Science-Status':'exploratory-background-subtracted-only',
        'X-Data-Provenance':ea.source, 'Cache-Control':'public, max-age=300'})


@app.get('/candidates')
def candidates(a: str, b: str, ra: float = RA, dec: float = DEC, fov: float = FOV):
    ea, eb = pair(a,b)
    try:
        diff = science.registered_difference(extract(ea,ra,dec,fov),extract(eb,ra,dec,fov))
        found = science.find_candidates(diff,ra,dec,fov)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {
        'a':ea.public(), 'b':eb.public(), 'candidates':found,
        'warning':'Heuristic residuals, not statistically calibrated discoveries. PSF, photometric zeropoint, artifact masks and uncertainties have NOT been validated.',
        'data_provenance':ea.source,
        'method':'TAN-WCS coregistration; median-sky subtraction; >6 robust-MAD connected components',
    }
