# COSMIC SHIFT — Hackathon starter

A working *prototype scaffold* for browsing local FITS cutouts with sky coordinates and blinking through epochs. **Not yet a validated SPHEREx integration.**

## Run backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
mkdir -p data
# Place legitimate, WCS-calibrated 2D FITS files into backend/data/
uvicorn app.main:app --reload --port 8000
```
Backend docs: http://localhost:8000/docs

## Run frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:3000

## Current endpoints
- `GET /health` — status
- `GET /epochs` — list local FITS files
- `GET /cutout/{id}.png?ra=133.79513&dec=-7.24515&fov=5` — WCS cutout preview
- `GET /difference.png` — explicitly returns 501 until scientifically correct alignment implemented

## Important limitations
- No SPHEREx archive API has been verified or wired up.
- Local FITS images are sorted by filename, not observation date; use filenames with sortable dates until metadata indexing is added.
- Image display uses per-frame percentile scaling, so it is **not valid for photometric comparison**.
- Multi-epoch frames are not reprojected to a common WCS; use the blink feature as a UI demonstration, not a discovery claim.
- No PSF matching, uncertainty propagation, masks, or moving-object validation yet.
- Current loader supports simple 2D FITS HDUs with celestial WCS; SPHEREx-specific data models require a separate adapter.
- Do not call a discovery confirmed until independently validated against catalogs and artifacts.

## 48-hour priorities
1. Confirm public SPHEREx release, provenance, access, calibration and time metadata.
2. Implement SPHEREx product adapter and observation index.
3. Align cutouts with `reproject` on a common WCS, mask invalid pixels, PSF match.
4. Implement calibrated difference with uncertainty and candidate scoring.
5. Validate known targets and publish metrics.
6. Deploy and record live demonstration.
