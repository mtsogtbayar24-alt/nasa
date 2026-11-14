'use client';

import { useEffect, useMemo, useState } from 'react';

type Epoch = {
  id: string;
  date_obs: string;
  band: string;
  source: string;
  target: string;
  bunit: string;
  kind: 'demo' | 'fits';
  science_validated: boolean;
};
type Candidate = {
  ra: number; dec: number; x: number; y: number;
  change: string; peak_over_local_noise: number;
  pixels: number; status: string;
};
type CandidateResponse = { candidates: Candidate[]; warning: string; method: string };
type Coordinates = { ra: string; dec: string; fov: string };

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const PRESETS = [
  { label: 'WISE 0855 • motion demo', ra: '133.79513', dec: '-7.24515', fov: '5' },
  { label: 'RW Aurigae • variability demo', ra: '76.956', dec: '30.402', fov: '5' },
];
const DEFAULT = { ra: PRESETS[0].ra, dec: PRESETS[0].dec, fov: PRESETS[0].fov };

function validated(c: Coordinates): boolean {
  if (!c.ra.trim() || !c.dec.trim() || !c.fov.trim()) return false;
  const ra = Number(c.ra), dec = Number(c.dec), fov = Number(c.fov);
  return Number.isFinite(ra) && Number.isFinite(dec) && Number.isFinite(fov)
    && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90 && fov > 0 && fov <= 20;
}
function query(c: Coordinates): string {
  return new URLSearchParams({ra: c.ra, dec: c.dec, fov: c.fov}).toString();
}
function dateLabel(value?: string): string {
  return value ? value.slice(0, 10) : 'Unknown time';
}

export default function Home() {
  const [draft, setDraft] = useState<Coordinates>(DEFAULT);
  const [active, setActive] = useState<Coordinates>(DEFAULT);
  const [allEpochs, setAllEpochs] = useState<Epoch[]>([]);
  const [band, setBand] = useState('');
  const usableBands = useMemo(() => [...new Set(allEpochs.map(e => e.band))], [allEpochs]);
  const selectedBand = usableBands.includes(band) ? band : (usableBands[0] || '');
  const epochs = useMemo(() => allEpochs.filter(e => e.band === selectedBand), [allEpochs, selectedBand]);
  const [index, setIndex] = useState(0);
  const [mode, setMode] = useState<'blink' | 'difference'>('blink');
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [imageError, setImageError] = useState(false);
  const [candidates, setCandidates] = useState<CandidateResponse | null>(null);
  const [candidateLoading, setCandidateLoading] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const incoming = {
      ra: params.get('ra') ?? DEFAULT.ra,
      dec: params.get('dec') ?? DEFAULT.dec,
      fov: params.get('fov') ?? DEFAULT.fov,
    };
    if (validated(incoming)) {setDraft(incoming);setActive(incoming);}
  }, []);

  useEffect(() => {
    let live = true;
    const controller = new AbortController();
    setLoading(true); setError('');setPlaying(false);setIndex(0);setCandidates(null);
    fetch(`${API}/epochs?${query(active)}`, {signal: controller.signal})
      .then(async r => {
        if (!r.ok) throw new Error(`API returned ${r.status}`);
        return await r.json() as Epoch[];
      })
      .then(data => {if(live) setAllEpochs(data);})
      .catch(err => { if(live && err.name !== 'AbortError') setError(`Backend not ready: ${err.message}`); })
      .finally(() => {if(live) setLoading(false);});
    return () => { live = false;controller.abort(); };
  }, [active]);

  useEffect(() => {
    if (!playing || epochs.length < 2 || mode !== 'blink') return;
    const tick = window.setInterval(() => setIndex(i => (i+1)%epochs.length), 900);
    return () => window.clearInterval(tick);
  }, [playing, epochs.length, mode]);

  const current = epochs[Math.min(index, epochs.length-1)];
  const comparison = epochs[Math.max(index, 1)];
  const baseline = epochs[0];
  const canCompare = !!baseline && !!comparison && baseline.id !== comparison.id &&
    baseline.band === comparison.band && baseline.bunit === comparison.bunit && baseline.target === comparison.target;
  const differenceParams = canCompare
    ? `a=${encodeURIComponent(baseline.id)}&b=${encodeURIComponent(comparison.id)}&${query(active)}`
    : '';
  const imageUrl = current
    ? mode === 'blink'
      ? `${API}/cutout/${encodeURIComponent(current.id)}.png?${query(active)}`
      : canCompare ? `${API}/difference.png?${differenceParams}` : ''
    : '';
  const isDemo = current?.kind === 'demo' || epochs.some(e => e.kind === 'demo');

  useEffect(() => {
    if (mode !== 'difference' || !canCompare) { setCandidates(null);return; }
    let live = true;
    const controller = new AbortController();
    setCandidateLoading(true);setSelected(null);
    fetch(`${API}/candidates?${differenceParams}`, {signal:controller.signal})
      .then(async r => {if(!r.ok) throw Error(`Candidate API ${r.status}`);return await r.json() as CandidateResponse;})
      .then(data => {if(live)setCandidates(data);})
      .catch(() => {if(live)setCandidates(null);})
      .finally(() => {if(live)setCandidateLoading(false);});
    return () => {live=false;controller.abort();};
  }, [mode, differenceParams, canCompare]);

  function search(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if(!validated(draft)) return;
    setActive({...draft});
    window.history.replaceState(null, '', `${window.location.pathname}?${query(draft)}`);
  }
  function preset(p: Coordinates) {
    const coords={ra:p.ra,dec:p.dec,fov:p.fov};
    setDraft(coords);setActive(coords);
    window.history.replaceState(null, '', `${window.location.pathname}?${query(coords)}`);
  }
  async function share() {
    const url=`${window.location.origin}${window.location.pathname}?${query(active)}`;
    try { await navigator.clipboard.writeText(url);setCopied(true);window.setTimeout(()=>setCopied(false),2000); }
    catch { setError(`Shareable URL: ${url}`); }
  }
  function changeMode(next: 'blink'|'difference') {
    setMode(next);setPlaying(false);setImageError(false);
    if(next === 'difference' && index === 0 && epochs.length > 1)setIndex(1);
  }

  return <div className="shell">
    <header className="topbar">
      <a href="/" className="wordmark"><span className="brand-orbit">✺</span> COSMIC <span>SHIFT</span></a>
      <div className="top-actions"><span className="hackathon-label">SPHEREx DISCOVERY LAB</span><span className="status-dot"/><span className="status-label">Prototype v0.2</span></div>
    </header>
    <main className="content">
      <section className="intro">
        <div><p className="eyebrow">EXPLORE THE UNSEEN UNIVERSE</p><h1>Find what <span>moves</span> in the sky.</h1><p className="intro-copy">Compare images across time. Spot motion, brightness changes and unusual candidates in the infrared sky.</p></div>
        <div className="intro-stats"><div><strong>{epochs.length}</strong><small>OBSERVATIONS</small></div><div><strong>{usableBands.length}</strong><small>AVAILABLE BANDS</small></div></div>
      </section>
      <section className="notice"><span className="notice-icon">ⓘ</span><p><strong>{isDemo ? 'SYNTHETIC DEMONSTRATION' : 'RESEARCH PROTOTYPE'}</strong> — {isDemo ? 'These images and changes are deliberately simulated. They are NOT SPHEREx observations or discoveries.' : 'Local FITS data only. No verified NASA archive connection or calibrated discoveries.'}</p></section>
      <section className="workspace">
        <aside className="sidebar">
          <div className="section-head"><span className="section-count">01</span><h2>Sky coordinates</h2></div>
          <p className="sidebar-hint">Choose a simulated target or enter RA/Dec coordinates.</p>
          <div className="preset-row">{PRESETS.map(p => <button key={p.label} type="button" className="preset" onClick={()=>preset(p)}>{p.label}</button>)}</div>
          <form onSubmit={search} className="search-form">
            <div className="field-grid"><label>RIGHT ASCENSION <span>°</span><input aria-label="Right ascension in degrees" type="number" value={draft.ra} min="0" max="359.999" step="any" onChange={e=>setDraft({...draft,ra:e.target.value})}/></label><label>DECLINATION <span>°</span><input aria-label="Declination in degrees" type="number" value={draft.dec} min="-90" max="90" step="any" onChange={e=>setDraft({...draft,dec:e.target.value})}/></label></div>
            <label>FIELD OF VIEW <span>ARCMIN</span><select aria-label="Field of view" value={draft.fov} onChange={e=>setDraft({...draft,fov:e.target.value})}><option value="2">2 arcmin — Detail</option><option value="5">5 arcmin — Default</option><option value="10">10 arcmin — Wide</option><option value="20">20 arcmin — Survey</option></select></label>
            <button type="submit" disabled={!validated(draft)} className="primary-button">◎ &nbsp; Explore sky region</button>
          </form>
          <div className="side-divider"/>
          <div className="section-head"><span className="section-count">02</span><h2>Visualization</h2></div>
          <p className="mini-title">COMPARISON MODE</p>
          <div className="mode-switch"><button className={mode==='blink'?'selected':''} onClick={()=>changeMode('blink')}>◫ Blink</button><button className={mode==='difference'?'selected':''} onClick={()=>changeMode('difference')}>◈ Difference</button></div>
          <div className="mode-info">{mode==='blink'?'Frames share a consistent display stretch. Switching epochs reveals visual motion.':'Amber = brightened, blue = dimmed, relative to the first observation.'}</div>
          <p className="mini-title">SPECTRAL BAND</p>
          <select className="band-select" aria-label="Spectral band" value={selectedBand} disabled={!usableBands.length} onChange={e=>{setBand(e.target.value);setIndex(0);setPlaying(false);}}>{usableBands.length?usableBands.map(b=><option key={b} value={b}>{b}</option>):<option value="">No available bands</option>}</select>
          <div className="side-divider"/>
          <div className="section-head"><span className="section-count">03</span><h2>Data source</h2></div>
          <div className="metadata"><div><span>PROVENANCE</span><strong>{current?.source || 'Not loaded'}</strong></div><div><span>DETECTOR/BAND</span><strong>{current?.band || '—'}</strong></div><div><span>CALIBRATION</span><strong className="pending">Not validated</strong></div><div><span>UNIT</span><strong>{current?.bunit || '—'}</strong></div></div>
          <button className="share-button" onClick={share}>{copied?'✓ Copied link':'↗ Copy shareable URL'}</button>
        </aside>
        <section className="right-side">
          <div className="viewer-card">
            <div className="viewer-title"><div><p className="eyebrow">SKY VIEWPORT</p><h2>{mode==='blink'?'Time-domain explorer':'Difference analyzer'}</h2></div><span className="viewer-pill">{current?.kind==='demo'?'SIMULATION':current?'FITS DATA':'NO DATA'}</span></div>
            <div className="view-frame">
              {loading ? <p className="viewport-message">Loading observations…</p>
              : error ? <p role="alert" className="viewport-message error-message">{error}<br/><small>Start the FastAPI backend on port 8000.</small></p>
              : !epochs.length ? <p className="viewport-message">No observations in this sky region. Try a demo preset or add FITS files to backend/data/.</p>
              : imageUrl ? <>
                  <img key={imageUrl} className="sky-image" src={imageUrl} alt={`Synthetic or local FITS sky image, ${mode} mode, ${dateLabel(current?.date_obs)}`} onLoad={()=>setImageError(false)} onError={()=>setImageError(true)}/>
                  {imageError && <span role="alert" className="image-alert">Image unavailable at these coordinates.</span>}
                  {mode==='difference' && candidates?.candidates.slice(0,12).map((c,i)=><button key={`${c.x}-${c.y}-${i}`} className={`candidate-pin ${selected===i?'focus':''}`} title={`Unverified candidate: ${c.change}`} aria-label={`Inspect candidate ${i+1}`} style={{left:`${100*c.x/256}%`,top:`${100*c.y/256}%`}} onClick={()=>setSelected(i)}/>) }
                  <div className="compass">N ↑ &nbsp; W →</div>
                  <div className="image-footer">{current?.target || 'Sky region'} <span>ICRS · {active.fov}′</span></div>
                </> : <p className="viewport-message">Select at least two compatible observations.</p>}
            </div>
            <div className="timeline"><div className="timeline-head"><div><span className="timeline-title">OBSERVATION TIMELINE</span><strong>{dateLabel(current?.date_obs)}</strong></div><small>{epochs.length ? `${index+1} / ${epochs.length} frames`:'0 frames'}</small></div>
              <div className="timeline-controls"><button disabled={epochs.length<2} className="transport" onClick={()=>{setPlaying(false);setIndex(i=>Math.max(0,i-1));}}>‹</button><button disabled={epochs.length<2||mode!=='blink'} className="play" onClick={()=>setPlaying(p=>!p)}>{playing?'Ⅱ Pause':'▶ Play'}</button><button disabled={epochs.length<2} className="transport" onClick={()=>{setPlaying(false);setIndex(i=>Math.min(epochs.length-1,i+1));}}>›</button><input aria-label="Observation epoch" type="range" min="0" max={Math.max(0,epochs.length-1)} step="1" value={index} onChange={e=>{setPlaying(false);setIndex(Number(e.target.value));}} disabled={epochs.length<2}/></div>
              <div className="timeline-dates"><span>{dateLabel(epochs[0]?.date_obs)}</span><span>{dateLabel(epochs[epochs.length-1]?.date_obs)}</span></div>
            </div>
          </div>
          <div className="candidate-card"><div className="candidate-head"><div><p className="eyebrow">DISCOVERY WORKSPACE</p><h2>Candidate signals <span className="counter">{mode==='difference'?candidates?.candidates.length??0:'—'}</span></h2></div><span className="small-note">UNVERIFIED</span></div>
            {mode==='blink'?<p className="candidate-placeholder">Switch to <strong>Difference</strong> to find and inspect residual signals between two epochs.</p>
            : candidateLoading?<p className="candidate-placeholder">Analyzing registered images…</p>
            : candidates?.candidates.length?<div className="candidate-list">{candidates.candidates.slice(0,8).map((c,i)=><button onClick={()=>setSelected(i)} key={i} className={`candidate-row ${selected===i?'active':''}`}><span className={`candidate-icon ${c.change==='brightened'?'amber':'blue'}`}>{c.change==='brightened'?'↑':'↓'}</span><span><strong>{c.change==='brightened'?'Brightening':'Dimming'} signal #{i+1}</strong><small>RA {c.ra.toFixed(5)}° · Dec {c.dec.toFixed(5)}°</small></span><strong className="noise-label">{c.peak_over_local_noise}×</strong></button>)}</div>
            :<p className="candidate-placeholder">{canCompare?'No candidate signals above the illustrative threshold.':'Select a later epoch to compare with the first.'}</p>}
            <p className="science-disclaimer">Detection is heuristic only. No PSF matching, photometric calibration, uncertainty model or artifact validation yet. No candidate is a confirmed astronomical discovery.</p>
          </div>
        </section>
      </section>
      <footer>Built for the SPHEREx mission challenge · NASA is not affiliated with this prototype · <a href={`${API}/docs`} target="_blank" rel="noreferrer">API documentation ↗</a></footer>
    </main>
  </div>;
}
