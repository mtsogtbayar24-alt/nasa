# 48-hour hackathon: ownership, milestones and go/no-go gates

## North-star demo

A judge enters RA/Dec, selects a matched spectral band, sees ≥2 images from **the same real public astronomy dataset** blink on a consistent WCS grid, sees a difference image and an unverified candidate with provenance. SPHEREx-specific data is the preferred mission target, but we must never pass off other data as SPHEREx.

## Team roles for 3–5 members

- **Lead / integration (A):** technical PM, API contract, repo/branches, deployment and demo continuity.
- **Frontend / UX (B):** coordinate form, dark sky viewer, timeline, band control, responsive mobile, error messages.
- **Astronomy / data (C):** inspect real SPHEREx release, FITS metadata, WCS, calibration units, release provenance.
- **Science / detection (D):** image registration validation, difference quality, masks, candidates, reference tests.
- **Product / pitch (E):** benchmark scenarios, screenshots, README, 3-minute pitch, citations and video.

If **3 people:** A handles deployment/pitch, B handles UX/demo, C handles astronomy + detection. If **4 people:** A also handles pitch, B frontend, C ingestion, D science.

## Hour-by-hour first day (24 hours)

| Time | A · Lead | B · Frontend | C · Astronomy | D · Science | E · Pitch | Gate |
|---|---|---|---|---|---|---|
| H00–H02 | Create repo, CI, env | Run Next UI | Identify archive products | Examine scientific assumptions | Identify judge rubric | Backend + UI boot |
| H02–H04 | Agree API schema | Connect epochs + PNG | Download one legitimate FITS or document blocker | Test synthetic controls | Collect citations | **GO/NO-GO: SPHEREx source** |
| H04–H08 | Integrate PRs | Timeline and loading/error | Parse FITS HDUs, WCS | WCS alignment checks | Plan 3-minute story | First real cutout or WISE fallback |
| H08–H12 | Lock minimal end-to-end | Blink/play/share | Time/band/provenance indexing | Positive/negative difference | First demo recording | **P0 blink complete** |
| H12–H16 | QA, code review | Difference UI + controls | Matched-band coverage | Residual threshold + masks | Science explanations | Candidate signal demo |
| H16–H20 | CI + caching + hosting | Polish responsive UI | Detector / quality metadata | Known target tests | Pitch deck slides | No unverified claims |
| H20–H24 | P0 freeze and backup | Fix accessibility | Archive adapter robust | Baseline metrics and failures | Record demo + README | P0 first-day release |

## Second day checkpoints

- **H24–H30:** Validate at least one real target or document non-detection and choose a visually honest alternative; assess optional source catalog overlay.
- **H30–H36:** Add only bounded improvements: quality flags, spectrum if data permits; otherwise fix precision, latency, accessibility.
- **H36–H40:** Deploy live frontend/backend; prepare fully offline fallback demo using clearly labeled synthetic data.
- **H40–H44:** Pin dependency versions; README, architecture, dataset references and reproducibility.
- **H44–H48:** Freeze code, rehearse 3-minute pitch twice, final smoke tests, submit.

## Non-negotiable gates

- **H04 source gate:** No verified public SPHEREx epoch pair → use clearly labeled WISE or synthetic fallback; keep archive adapter independent.
- **H12 scientific gate:** Same band, same units, image WCS alignment validated. Otherwise difference view remains illustrative only.
- **H24 demo gate:** Search + blink + diff must work without manual file editing at presentation time.
- **H40 delivery gate:** Freeze, record backup video, do not begin risky feature development.

## Success metrics (measure, don't invent)

1. `N_real_epoch_pairs`: number of documented real image pairs with provenance and compatible bands.
2. `AlignmentError`: astrometric error estimated on known stationary sources in pixels/arcsec.
3. `MedianCutoutLatency`: time to first displayed cutout at one coordinate and FOV.
4. `Recall & FalsePositive`: only on annotated or injection-recovery benchmark with truth labels.
5. `FirstDiscoveryTime`: time a first-time participant takes to identify an obvious injected change.

Do **not** report scores until they are actually measured.

## Suggested Git commands

```bash
git checkout -b feat/fits
# make small change + test
python -m pytest -q

git add backend/ docs/
git commit -m "feat(fits): add observation metadata adapter"
git push -u origin feat/fits
# Open pull request -> CI green -> one reviewer -> merge main
```
