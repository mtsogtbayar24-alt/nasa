# Day 1 research log — evidence-first data integration

Status as of 2026-11-14: **NOT LIVE-VERIFIED.** Web search/network verification was unavailable while creating this package. Treat the following as research tasks, not claims about current archives or releases.

## Mission / astronomy sources to verify manually

1. NASA mission overview: https://science.nasa.gov/mission/spherex/
2. NASA IPAC/IRSA data archive: https://irsa.ipac.caltech.edu/
3. Astropy FITS and WCS documentation: https://docs.astropy.org/
4. WCS reprojection background: https://reproject.readthedocs.io/
5. Source extraction: https://photutils.readthedocs.io/
6. Aladin Lite: https://aladin.cds.unistra.fr/AladinLite/
7. Backup WISE time-domain: https://unwise.me/

## Source gate: answer with URLs + observed results

- [ ] What is the **actual public SPHEREx release ID and date**?
- [ ] Which product level is usable (map, spectral cube, exposure, coadd), with documentation link?
- [ ] Can products be accessed from a stable public URL or documented query endpoint?
- [ ] Which FITS HDUs contain 2D celestial image, WCS, observation time, detector/band, calibration units?
- [ ] Which HDUs contain uncertainty maps, bad-pixel flags, contamination flags, PSF information?
- [ ] For any selected RA/Dec, do at least two epochs overlap in the **same band**?
- [ ] How do we identify related observations from six detector arrays and 102 bands?
- [ ] What is the image pixel scale and PSF? Which targets can physically show measurable motion?
- [ ] Are there public data redistribution constraints and acknowledgment requirements?

## Mandatory notebook evidence

Document **a URL and exact observation ID** for each source. Do not insert hypothetical URLs or manually invented detection values.

```text
SOURCE RELEASE:
PUBLIC DOCUMENTATION URL:
QUERY URL / DATASET ID:
OBSERVATION 1 + DATE:
OBSERVATION 2 + DATE:
RA / DEC / FIELD OF VIEW:
COMPATIBLE WAVELENGTHS:
FITS EXTENSION / WCS INFO:
UNITS / QUALITY FLAGS:
LOCAL CHECKSUMS:
KNOWN LIMITATIONS:
```

## Test objects (test case, not promised detection)

- Barnard's Star — proper motion: assess whether displacement > astrometric error at available epochs.
- Epsilon Indi B — faint brown dwarf companion region: check near-IR sensitivity and blending.
- WISE 0855 — very cold faint moving dwarf: RA ≈ 133.79513°, Dec ≈ −7.24515° (J2000-like target reference; check epoch/proper-motion propagation).
- RW Aurigae — irregular young variable star: compare calibrated flux under similar bandpass.
- R Draconis — variable star: require enough epochs and photometric consistency for a light curve.

**Important:** Coordinates of high proper-motion targets change with epoch; test against authoritative catalog astrometry, not static labels alone.
