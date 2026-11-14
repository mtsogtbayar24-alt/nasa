# COSMIC SHIFT — NASA Space Apps challenge-provided resources

These URLs were provided in the challenge resources text by the team. **Not independently opened or verified in this environment.** Access and policies must be checked manually at each site.

## Priority A: required for the SPHEREx MVP

1. **NASA/IPAC SPHEREx archive** — https://irsa.ipac.caltech.edu/Missions/spherex.html
   - Identify public release, product type, filter/detector metadata, access method, observation time, FITS structures, calibration, variance, flags, and use terms.
   - Deliverable: one real file with its documented source URL and a reproducible retrieval instruction.
2. **SPHEREx tutorial notebooks** — https://caltech-ipac.github.io/irsa-tutorials/spherex/
   - Follow documented Python access examples, recording exact endpoint, parameters, and notebook version. **Do not invent endpoint URLs**.
   - Deliverable: one successful notebook query and a verified FITS read.
3. **WiseView** — http://byw.tools/wiseview
   - Examine coordinate input, blink animation, epochs, field-of-view, image exports, and onboarding. This is UX inspiration, not permission to reuse code or imagery.
   - Deliverable: annotated UI design comparison.
4. **Gaia DR3** — https://archive.stsci.edu/missions-and-data/gaia
   - Obtain reference catalog coordinates/proper motions, noting observation epochs, provenance, and catalog license.
   - Deliverable: documented comparison source or postpone as P1.

## Priority B: scientifically useful but non-blocking

5. **CSA NEOSSat explainer** — https://www.asc-csa.gc.ca/eng/satellites/neossat/
6. **Canadian Astronomy Data Centre** — https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/
7. **NEOSSat Python data tutorial** — https://github.com/asc-csa/NEOSSAT_Tutorial
8. **NEOSSat dataset** — https://data.asc-csa.gc.ca/dataset/neossat

CSA resources can support a later cross-mission demonstration, but should **not** distract the team from a real SPHEREx multi-epoch MVP. They are separate missions and must be correctly labeled.

## First 4 hours: actual research outcomes to capture

| Task | Owner | Evidence / GO criterion |
|---|---|---|
| A1. Review NASA/IPAC archive and data-use rules | Data engineer | Documented public product and use conditions |
| A2. Run official Python example | Data engineer | Exact notebook URL + successful query/file |
| A3. Inspect downloaded FITS | Science engineer | `python scripts/inspect_fits.py path/to/file.fits` output |
| A4. Establish same-field multi-epoch same-band pair | Science + lead | Two observation IDs, dates, wavelengths, and WCS |
| A5. Examine WiseView user journey | Frontend | Screenshots/notes, original design decisions |
| A6. Assess Gaia DR3 catalog crossmatch | Science | Catalog field mapping and proper-motion considerations |

## SPHEREx integration gate

Record at minimum:

```text
Release name and version:
Official product documentation URL:
Public download or query URL (not invented):
Observation A ID / date / band:
Observation B ID / date / band:
Relevant HDU indexes and shapes:
WCS projection and units:
Data units and calibration status:
Exposure / sensitivity / PSF information:
Uncertainty and contamination flags:
Data use conditions / attribution:
Confirmed by / checked on:
```

**If the two epochs are absent, do not imply they exist.** We can demo a clearly synthetic comparison while pursuing actual public WISE or SPHEREx data with citation and provenance.

## Ethical presentation

NASA does not endorse this non-U.S.-Government project. Observe all external site-specific data use conditions. Clearly distinguish official mission data, partner archive data, and our synthetic demo fixtures. Never claim a new discovery based solely on the MVP residual detector.
