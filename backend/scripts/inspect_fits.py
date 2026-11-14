"""Inspect a user-supplied FITS product locally. No network calls or NASA claims.

Usage: python scripts/inspect_fits.py /path/to/file.fits
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def inspect(path: Path) -> dict:
    from astropy.io import fits
    from astropy.wcs import WCS

    result = {'file': path.name, 'hdus': []}
    with fits.open(path, memmap=True) as hdul:
        primary = hdul[0].header
        result['primary'] = {k: str(primary[k]) for k in (
            'TELESCOP', 'INSTRUME', 'DATE-OBS', 'DATE-END', 'MJD-OBS',
            'BUNIT', 'ORIGIN', 'OBSID', 'OBJECT') if k in primary}
        for i, hdu in enumerate(hdul):
            h = hdu.header
            shape = list(hdu.data.shape) if hdu.data is not None else None
            item = {'index': i, 'name': hdu.name, 'shape': shape,
                    'metadata': {k: str(h[k]) for k in (
                        'EXTNAME', 'DATE-OBS', 'MJD-OBS', 'BUNIT', 'FILTER',
                        'BAND', 'DETECTOR', 'WAVELEN', 'CTYPE1', 'CTYPE2',
                        'CUNIT1', 'CUNIT2', 'CRVAL1', 'CRVAL2', 'QUALITY') if k in h}}
            try:
                wcs = WCS(h, naxis=2) if shape and len(shape) == 2 else None
                item['celestial_wcs'] = bool(wcs is not None and wcs.has_celestial)
            except Exception as exc:
                item['celestial_wcs'] = False
                item['wcs_error'] = str(exc)
            result['hdus'].append(item)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error(f'File not found: {args.file}')
    print(json.dumps(inspect(args.file), indent=2, ensure_ascii=False))
