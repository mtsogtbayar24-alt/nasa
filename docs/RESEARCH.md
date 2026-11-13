# Day 1 — Research and validation checklist

## Authoritative references
- https://science.nasa.gov/mission/spherex/
- https://irsa.ipac.caltech.edu/
- https://docs.astropy.org/
- https://reproject.readthedocs.io/
- https://photutils.readthedocs.io/
- https://aladin.cds.unistra.fr/AladinLite/

## Archive gate (first 4 hours)
- [ ] Identify public SPHEREx data release and product types (not assumed).
- [ ] Verify legal public access, URLs, and machine-readable query route.
- [ ] Download one legitimate file and inspect FITS HDUs.
- [ ] Verify WCS, DATE-OBS/MJD, wavelength, calibration units, quality masks.
- [ ] Find 2+ epochs overlapping same sky region and compatible bands.
- [ ] Record pixel scale, PSF, sensitivity, and target visibility.
- [ ] If unavailable, use clearly labeled WISE demo data while keeping SPHEREx adapter open.

## Science gates
- [ ] Co-register epochs to reference WCS.
- [ ] Match PSF and normalize photometric scale before subtracting.
- [ ] Preserve NaNs and contamination masks.
- [ ] Propagate uncertainties and quantify residual significance.
- [ ] Test Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae, R Draconis.
- [ ] Document non-detections and limitations without inventing results.

## Competition deliverables
- Public site, source repo, README, architecture, 3-min demo, validation metrics, data provenance.
