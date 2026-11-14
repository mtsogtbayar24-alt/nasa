"""Generate obviously synthetic, deterministic FITS-like NPZ test images.

This is a UI/algorithm test, NOT SPHEREx or WISE mission observation data.
The invented motion/flux changes must not be reported as discoveries.
"""
from pathlib import Path
import argparse
import numpy as np


def create_demo(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261114)
    n = 256
    yy,xx = np.mgrid[:n,:n]
    obs_dates = ['2025-05-20T00:00:00','2025-08-20T00:00:00','2025-11-20T00:00:00','2026-02-20T00:00:00']
    fields = [
        ('wise0855',133.79513,-7.24515,'WISE 0855 (illustrative field)'),
        ('rw_aur',76.956,30.402,'RW Aurigae (illustrative field)'),
    ]
    for key, ra, dec, label in fields:
        stars = [(rng.uniform(15,241),rng.uniform(15,241),rng.uniform(14,70)) for _ in range(42)]
        static = np.zeros((n,n),dtype=np.float32)
        for sx,sy,amp in stars:
            static += amp*np.exp(-((xx-sx)**2+(yy-sy)**2)/(2*1.65**2))
        for k,date in enumerate(obs_dates):
            img = np.full((n,n),20.0,dtype=np.float32) + static
            if key == 'wise0855':
                # Deliberately exaggerated motion for a visible demo.
                mx,my = 106+15*k, 118+4*k
                img += 180*np.exp(-((xx-mx)**2+(yy-my)**2)/(2*2.0**2))
            else:
                amp = (120,230,60,190)[k]
                img += amp*np.exp(-((xx-130)**2+(yy-120)**2)/(2*2.0**2))
            img += rng.normal(0,2.0,(n,n)).astype(np.float32)
            # WCS-center offsets emulate small pointing drift; the sky stays fixed.
            drift_ra_arcsec = (0, 1.2, -1.0, 0.8)[k]
            drift_dec_arcsec = (0, -0.7, 0.5, -0.4)[k]
            image_ra = ra + drift_ra_arcsec/(3600*np.cos(np.deg2rad(dec)))
            image_dec = dec + drift_dec_arcsec/3600
            # Shift raw pixel coordinates consistently with pointing metadata.
            from scipy.ndimage import shift
            img = shift(img, shift=(drift_dec_arcsec/3,drift_ra_arcsec/3), order=1, mode='constant', cval=np.nan)
            np.savez_compressed(output/f'{key}_{k+1:02d}.npz', image=img.astype(np.float32),
                                ra_center=image_ra, dec_center=image_dec,
                                pixel_scale_arcsec=3.0, date_obs=date,
                                band='DEMO-IR', target=key, source='SYNTHETIC',
                                bunit='simulated_counts')
    return len(fields)*len(obs_dates)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data'/'demo')
    args=parser.parse_args()
    print(f'Created {create_demo(args.output)} SYNTHETIC example observations in {args.output}')
