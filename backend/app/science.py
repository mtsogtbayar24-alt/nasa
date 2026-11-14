"""Sky-coordinate registration, FITS/NPZ loading and exploratory comparison.

All visualized frames are sampled on one *fixed* TAN WCS pixel grid.
Real FITS data requires Astropy. Synthetic NPZ fixtures are supported without it.
Difference and candidate products are explicitly NOT calibrated discoveries.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import math
import numpy as np
from PIL import Image
from scipy.ndimage import label, map_coordinates
from io import BytesIO

try:
    from astropy.io import fits
    from astropy.wcs import WCS
    HAS_ASTROPY = True
except ImportError:  # Allow self-contained demo when optional astronomy dependency absent.
    fits = None
    WCS = None
    HAS_ASTROPY = False

IMAGE_SIZE = 256


@dataclass(frozen=True)
class Epoch:
    id: str
    path: Path
    date_obs: str
    band: str
    source: str
    target: str
    ra: float
    dec: float
    approximate_width_arcmin: float
    bunit: str
    kind: str

    def public(self) -> dict:
        return {
            "id": self.id, "date_obs": self.date_obs, "band": self.band,
            "source": self.source, "target": self.target,
            "ra": self.ra, "dec": self.dec,
            "bunit": self.bunit, "kind": self.kind,
            "science_validated": False,
        }


def _str(value: object, fallback: str = "unknown") -> str:
    if value is None:
        return fallback
    result = str(value)
    return result if result else fallback


def read_metadata(path: Path, root: Path) -> Epoch:
    suffix = path.name.lower()
    identifier = path.relative_to(root).as_posix().replace('/', '__').replace('.', '_')
    if suffix.endswith('.npz'):
        with np.load(path, allow_pickle=False) as data:
            # NPZ is accepted only as a developer fixture, NEVER as official mission data.
            scale = float(data['pixel_scale_arcsec'])
            height, width = data['image'].shape
            return Epoch(identifier, path, _str(data['date_obs'].item()),
                         _str(data['band'].item()), 'SYNTHETIC',
                         _str(data['target'].item()), float(data['ra_center']),
                         float(data['dec_center']), min(height, width)*scale/60,
                         _str(data['bunit'].item()), 'demo')
    if not HAS_ASTROPY:
        raise RuntimeError('FITS support requires Astropy; pip install -r requirements.txt')
    with fits.open(path, memmap=False) as hdul:
        for hdu in hdul:
            if hdu.data is None or hdu.data.ndim != 2:
                continue
            try:
                w = WCS(hdu.header).celestial
                if not w.has_celestial:
                    continue
                h, width = hdu.data.shape
                ra, dec = w.all_pix2world((width-1)/2, (h-1)/2, 0)
                scale = math.sqrt(abs(np.linalg.det(w.pixel_scale_matrix)))*60
                header = hdul[0].header
                telescope = _str(hdu.header.get('TELESCOP', header.get('TELESCOP')), 'FITS archive')
                return Epoch(identifier, path,
                             _str(hdu.header.get('DATE-OBS', header.get('DATE-OBS'))),
                             _str(hdu.header.get('FILTER', hdu.header.get('BAND', header.get('FILTER')))),
                             telescope, _str(hdu.header.get('OBJECT', header.get('OBJECT'))),
                             float(ra)%360, float(dec), min(h, width)*scale,
                             _str(hdu.header.get('BUNIT', header.get('BUNIT'))), 'fits')
            except Exception:
                continue
    raise ValueError('No 2D celestial WCS image found')


def list_epochs(root: Path) -> list[Epoch]:
    if not root.exists():
        return []
    paths = sorted(p for p in root.rglob('*') if p.is_file() and
                   p.name.lower().endswith(('.npz', '.fits', '.fit', '.fits.gz')))
    epochs = []
    for path in paths:
        try:
            epochs.append(read_metadata(path, root))
        except Exception:
            # A malformed FITS file cannot prevent other observations from loading.
            continue
    return sorted(epochs, key=lambda e: (e.target, e.date_obs, e.id))


def angular_separation_arcmin(ra0: float, dec0: float, ra1: float, dec1: float) -> float:
    # Haversine: stable at RA 0/360 and near celestial poles.
    a = math.radians(dec0)
    b = math.radians(dec1)
    dr = math.radians((ra0-ra1 + 180)%360 - 180)
    h = math.sin((b-a)/2)**2 + math.cos(a)*math.cos(b)*math.sin(dr/2)**2
    return math.degrees(2*math.asin(math.sqrt(max(0, min(1, h)))))*60


def covered(epoch: Epoch, ra: float, dec: float, fov: float) -> bool:
    # Broad bounding-sphere prefilter; exact valid-pixel coverage checked on cutout.
    return angular_separation_arcmin(epoch.ra, epoch.dec, ra, dec) < (epoch.approximate_width_arcmin + fov) / 2


@lru_cache(maxsize=32)
def _load(path: str, modified_ns: int):
    p = Path(path)
    if p.suffix == '.npz':
        with np.load(p, allow_pickle=False) as data:
            return np.asarray(data['image'], dtype=np.float32), None
    if not HAS_ASTROPY:
        raise RuntimeError('Astropy not installed; FITS image unavailable')
    with fits.open(p, memmap=False) as hdul:
        for hdu in hdul:
            if hdu.data is None or hdu.data.ndim != 2:
                continue
            try:
                wcs = WCS(hdu.header).celestial
                if wcs.has_celestial:
                    return np.asarray(hdu.data, dtype=np.float32), wcs
            except Exception:
                continue
    raise ValueError('No celestial WCS image')


def common_world_grid(ra: float, dec: float, fov: float, size: int = IMAGE_SIZE):
    """Equally spaced TAN projection centered at requested ICRS coordinate."""
    yy, xx = np.mgrid[:size, :size]
    pixel_scale_deg = fov / (60*size)
    if HAS_ASTROPY:
        w = WCS(naxis=2)
        w.wcs.ctype = ['RA---TAN', 'DEC--TAN']
        w.wcs.crval = [ra, dec]
        w.wcs.crpix = [(size+1)/2, (size+1)/2]
        w.wcs.cdelt = [-pixel_scale_deg, -pixel_scale_deg]  # North-up image display.
        return w.all_pix2world(xx.astype(float), yy.astype(float), 0)
    # Small-angle approximation ONLY for synthetic demo if Astropy unavailable.
    c = max(abs(math.cos(math.radians(dec))), 1e-5)
    return ((ra-(xx-(size-1)/2)*pixel_scale_deg/c)%360,
            dec-(yy-(size-1)/2)*pixel_scale_deg)


def aligned_image(epoch: Epoch, ra: float, dec: float, fov: float, size: int = IMAGE_SIZE) -> np.ndarray:
    img, wcs = _load(str(epoch.path), epoch.path.stat().st_mtime_ns)
    world_ra, world_dec = common_world_grid(ra, dec, fov, size)
    if epoch.kind == 'demo':
        scale = epoch.approximate_width_arcmin*60 / min(img.shape)
        dra = (world_ra - epoch.ra + 180)%360 - 180
        x = (img.shape[1]-1)/2 - dra*np.cos(np.deg2rad(epoch.dec))*3600/scale
        y = (img.shape[0]-1)/2 - (world_dec - epoch.dec)*3600/scale
    else:
        x, y = wcs.all_world2pix(world_ra, world_dec, 0)
    # Interpolate signal and coverage separately: no NaN spreading at edges.
    mask = np.isfinite(img).astype(float)
    weights = map_coordinates(mask, [y, x], order=1, mode='constant', cval=0.0)
    values = map_coordinates(np.nan_to_num(img, nan=0.0), [y, x],
                             order=1, mode='constant', cval=0.0)
    out = np.full((size, size), np.nan, dtype=np.float32)
    valid = weights >= .999
    out[valid] = values[valid] / weights[valid]
    return out


def image_png(arr: np.ndarray, lo: float | None = None, hi: float | None = None) -> bytes:
    valid = arr[np.isfinite(arr)]
    if not len(valid):
        raise ValueError('No image pixels at this coordinate')
    if lo is None or hi is None:
        lo, hi = np.percentile(valid, [1, 99.7])
    scaled = np.clip((arr-lo)/max(float(hi-lo), 1e-8), 0, 1)
    stretched = np.arcsinh(9*np.nan_to_num(scaled, nan=0))/np.arcsinh(9)
    rgb = np.repeat((stretched*255).astype(np.uint8)[..., None], 3, axis=2)
    rgb[~np.isfinite(arr)] = (14, 22, 37)
    buf = BytesIO()
    Image.fromarray(rgb, 'RGB').save(buf, format='PNG')
    return buf.getvalue()


def shared_limits(arrays: list[np.ndarray]) -> tuple[float, float]:
    # Shared transfer function preserves time-domain brightness changes in blink mode.
    all_valid = np.concatenate([a[np.isfinite(a)] for a in arrays])
    if not len(all_valid):
        raise ValueError('Requested coordinate has no coverage')
    lo, hi = np.percentile(all_valid, [1, 99.7])
    return float(lo), float(hi)


def registered_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if not np.isfinite(a).any() or not np.isfinite(b).any():
        raise ValueError('Insufficient overlapping image coverage')
    # Approximate sky-background subtraction only. Does NOT fix zeropoints/PSF.
    am = np.nanmedian(a)
    bm = np.nanmedian(b)
    return (b-bm)-(a-am)


def difference_png(diff: np.ndarray) -> bytes:
    valid = np.abs(diff[np.isfinite(diff)])
    if not len(valid):
        raise ValueError('No overlapping pixels')
    limit = max(float(np.percentile(valid, 99.6)), 1e-7)
    t = np.clip(np.nan_to_num(diff, nan=0)/limit, -1, 1)
    # Blue = dimmer in B, amber = brighter in B; dark = unchanged.
    magnitude = np.abs(t)[..., None]
    rgb = np.where(t[..., None] >= 0,
                   np.array([251, 171, 73]), np.array([76, 166, 246]))
    rgb = (np.array([13, 23, 42])*(1-magnitude) + rgb*magnitude).astype(np.uint8)
    rgb[~np.isfinite(diff)] = (9, 12, 23)
    buf = BytesIO()
    Image.fromarray(rgb, 'RGB').save(buf, format='PNG')
    return buf.getvalue()


def find_candidates(diff: np.ndarray, ra: float, dec: float, fov: float, limit: int = 16):
    """Heuristic connected components; SNR estimates are NOT detection significance."""
    good = np.isfinite(diff)
    if good.sum() < 200:
        return []
    centered = diff[good] - np.median(diff[good])
    sigma = max(1.4826*np.median(np.abs(centered)), 0.1)
    world_ra, world_dec = common_world_grid(ra, dec, fov)
    candidates = []
    for sign in (-1, 1):
        bright = good & (sign*diff > 6*sigma)
        areas, count = label(bright)
        for idx in range(1, count+1):
            yy, xx = np.where(areas == idx)
            if len(xx) < 3 or len(xx) > 2500:
                continue
            amplitudes = (sign*diff[yy, xx]).astype(float)
            weight = np.maximum(amplitudes, 0.01)
            x, y = float(np.average(xx, weights=weight)), float(np.average(yy, weights=weight))
            xi, yi = np.clip(round(x), 0, IMAGE_SIZE-1), np.clip(round(y), 0, IMAGE_SIZE-1)
            candidates.append({
                'ra': round(float(world_ra[yi, xi]), 7),
                'dec': round(float(world_dec[yi, xi]), 7),
                'x': round(x, 2), 'y': round(y, 2),
                'change': 'brightened' if sign > 0 else 'dimmed',
                'peak_over_local_noise': round(float(np.max(amplitudes)/sigma), 1),
                'pixels': len(xx),
                'status': 'unverified_candidate',
            })
    return sorted(candidates, key=lambda c: c['peak_over_local_noise'], reverse=True)[:limit]
