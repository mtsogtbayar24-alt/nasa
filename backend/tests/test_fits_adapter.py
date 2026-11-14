"""Real FITS ingestion test runs when Astropy is installed (e.g. in CI)."""
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app import main

astropy = pytest.importorskip('astropy')
from astropy.io import fits
from astropy.wcs import WCS


def test_real_wcs_fits_file(tmp_path, monkeypatch):
    w=WCS(naxis=2)
    w.wcs.ctype=['RA---TAN','DEC--TAN']
    w.wcs.crpix=[64.5,64.5]
    w.wcs.cdelt=[-3/3600,-3/3600]
    w.wcs.crval=[133.79513,-7.24515]
    image=np.ones((128,128),dtype=np.float32)
    image[64,64]=120.0
    hdu=fits.PrimaryHDU(image,header=w.to_header())
    hdu.header['DATE-OBS']='2025-05-20T00:00:00'
    hdu.header['TELESCOP']='TEST-TELESCOPE'
    hdu.header['BUNIT']='adu'
    hdu.header['FILTER']='TEST-BAND'
    hdu.header['OBJECT']='TEST-FIELD'
    hdu.writeto(tmp_path/'test.fits')
    monkeypatch.setattr(main,'DATA_DIR',tmp_path)
    client=TestClient(main.app)
    epochs=client.get('/epochs?ra=133.79513&dec=-7.24515&fov=2').json()
    assert len(epochs)==1
    assert epochs[0]['source']=='TEST-TELESCOPE'
    assert epochs[0]['kind']=='fits'
    resp=client.get(f"/cutout/{epochs[0]['id']}.png?ra=133.79513&dec=-7.24515&fov=2")
    assert resp.status_code==200
    assert resp.content[:8]==b'\x89PNG\r\n\x1a\n'
