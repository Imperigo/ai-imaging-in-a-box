import { useEffect, useState } from 'react';
import { exportGlb } from '@kosmo/kernel';
import { KButton, melde, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../../../state/project-store';
import { postBlenderSimJob, holeBlenderSimJob, abbrechenBlenderSimJob } from '../../vis-jobs';
import { useBlenderJobsRuntime, OFFENE_BLENDER_JOB_STATUS } from '../../blender-jobs-runtime';
import { visInhaltsRegistry } from './registry';
import '../vis-island.css';

/**
 * SONNE-Insel (v0.8.9 §9 E11, `docs/V089-SPEZ.md`, PBL2) — Sonnenstunden-
 * Client: Datum-Input (eigener, LOKALER `useState` — KEIN Doc-Feld,
 * Sanktion 14: Laufzeit ≠ Modell), Anzeige des Projektstandorts (aus
 * `doc.settings.standort` NUR GELESEN — `design.ts` bleibt PA2-exklusiv,
 * Sanktion 14), Knopf «Sonnenstunden berechnen (HomeStation)» →
 * `exportGlb(doc)` + `postBlenderSimJob('sonnenstunden', {lat,lon,datum})` →
 * Poll (`holeBlenderSimJob`) → Ergebnis-Anzeige.
 *
 * Ehrlichkeitsgrenze (E11, wörtlich): OHNE echten Blender-Worker endet der
 * Job auf `kein-blender-worker` — die Bridge-`message` wird WORTGLEICH
 * angezeigt, KEINE erfundene Zahl, KEINE «ungefähr»-Formulierung. Echte
 * Zahlen (`stunden`/`kriteriumErfuellt`/`methode`) kommen NUR aus `result`
 * eines `done`-Jobs (Fake-Bridge im Container erreicht das nie, s.
 * `main.py` `_fake_worker_step`/Sanktion 12-Nachbarschaft in `blender-sim.ts`).
 */

/** 2000ms — knapp über dem 1s-Takt des Fake-Worker-Loops (`main.py`
 *  `_fake_worker_loop`), Muster `VisWorkspace.tsx`s `EinfachAnsicht`-Poll
 *  (2500ms) bzw. `NodeCanvas.tsx`s Render-Poll (2500ms). */
const POLL_MS = 2000;

/** Store-Key für den (genau einen) aktiven Sonnenstunden-Lauf dieser Insel —
 *  s. `blender-jobs-runtime.ts`s Kopfkommentar («ein Aufrufer-Key»). */
const JOB_KEY = 'sonnenstunden';

function SonnenstundenStufe2() {
  const revision = useProject((s) => s.revision);
  void revision;
  const doc = useProject.getState().doc;
  const standort = doc.settings.standort;

  const lauf = useBlenderJobsRuntime((s) => s.jobs[JOB_KEY]);
  const setzeJob = useBlenderJobsRuntime((s) => s.setzeJob);
  const patchJob = useBlenderJobsRuntime((s) => s.patchJob);

  const [datum, setDatum] = useState('2026-06-21');
  const [sendend, setSendend] = useState(false);

  const offen = lauf ? (OFFENE_BLENDER_JOB_STATUS as readonly string[]).includes(lauf.status) : false;

  // Poll — läuft NUR solange ein Job offen ist (s. `OFFENE_BLENDER_JOB_
  // STATUS`). Race-Schutz wie `NodeCanvas.tsx`s Render-Poll (P6-Review #7):
  // eine verspätete Antwort darf einen NEUEN Lauf (anderer/kein jobId) nie
  // überschreiben — darum wird `jobId` je Tick frisch aus dem Store gelesen.
  useEffect(() => {
    const t = setInterval(() => {
      const aktuell = useBlenderJobsRuntime.getState().jobs[JOB_KEY];
      if (!aktuell?.jobId) return;
      if (!(OFFENE_BLENDER_JOB_STATUS as readonly string[]).includes(aktuell.status)) return;
      const jobId = aktuell.jobId;
      void holeBlenderSimJob(jobId)
        .then((j) => {
          if (useBlenderJobsRuntime.getState().jobs[JOB_KEY]?.jobId !== jobId) return;
          patchJob(JOB_KEY, {
            status: j.status,
            ...(j.message !== undefined ? { message: j.message } : {}),
            ...(j.result !== undefined ? { result: j.result } : {}),
            ...(j.approval_token !== undefined ? { approvalToken: j.approval_token } : {}),
          });
        })
        .catch((err) => {
          if (useBlenderJobsRuntime.getState().jobs[JOB_KEY]?.jobId !== jobId) return;
          // Transiente Netzfehler nicht sofort hochziehen wäre auch denkbar
          // (Muster `sendeGraphRenderAuftrag`), aber ein einzelner Sonnen-
          // stunden-Lauf ist kein Dauerbetrieb — ehrlich anzeigen statt
          // stillschweigend weiterzupollen, der Nutzer sieht sofort, dass
          // etwas hakt.
          patchJob(JOB_KEY, { status: 'error', fehler: err instanceof Error ? err.message : String(err) });
        });
    }, POLL_MS);
    return () => clearInterval(t);
  }, [patchJob]);

  const berechnen = async () => {
    if (!standort) return;
    setSendend(true);
    try {
      const glb = exportGlb(doc, doc.settings.projectName);
      const job = await postBlenderSimJob('sonnenstunden', { lat: standort.lat, lon: standort.lon, datum }, glb);
      setzeJob(JOB_KEY, {
        kind: 'blender-sim',
        status: job.status,
        jobId: job.job_id,
        gestartetUm: Date.now(),
        ...(job.message !== undefined ? { message: job.message } : {}),
        ...(job.result !== undefined ? { result: job.result } : {}),
        ...(job.approval_token !== undefined ? { approvalToken: job.approval_token } : {}),
      });
    } catch (err) {
      setzeJob(JOB_KEY, {
        kind: 'blender-sim',
        status: 'error',
        fehler: err instanceof Error ? err.message : String(err),
      });
      meldeFehler(err);
    } finally {
      setSendend(false);
    }
  };

  const abbrechen = async () => {
    if (!lauf?.jobId) return;
    try {
      const job = await abbrechenBlenderSimJob(lauf.jobId);
      patchJob(JOB_KEY, { status: job.status });
      melde('Sonnenstunden-Berechnung abgebrochen.', { ton: 'info' });
    } catch (err) {
      meldeFehler(err);
    }
  };

  // `'stunden' in …`-Schmalspur-Typwächter (E11): `lauf.result` ist
  // `SonnenstundenResult | BakeResult | undefined` (`blender-jobs-
  // runtime.ts`s gemeinsames Feld für beide Job-Arten) — nur der
  // Sonnenstunden-Zweig trägt `stunden`.
  const ergebnis = lauf?.result && 'stunden' in lauf.result ? lauf.result : undefined;

  return (
    <div className="visisl-stufe2" data-testid="island-sonnenstunden-stufe2" onClick={(e) => e.stopPropagation()}>
      <label className="visisl-reihe">
        <span>Datum</span>
        <input
          type="date"
          data-testid="island-sonnenstunden-datum"
          value={datum}
          onChange={(e) => setDatum(e.target.value)}
        />
      </label>

      {standort ? (
        <p className="visisl-hinweis-klein" data-testid="island-sonnenstunden-standort">
          Standort: {standort.label} ({standort.lat.toFixed(4)}, {standort.lon.toFixed(4)})
        </p>
      ) : (
        <p className="visisl-hinweis" data-testid="island-sonnenstunden-standort-fehlt">
          Kein Projektstandort gesetzt — zuerst in KosmoDesign die Adresse suchen.
        </p>
      )}

      <div className="visisl-reihe">
        <KButton
          size="touch"
          tone="accent"
          disabled={!standort || sendend || offen}
          data-testid="island-sonnenstunden-berechnen"
          onClick={() => void berechnen()}
        >
          {sendend ? 'Sende…' : 'Sonnenstunden berechnen (HomeStation)'}
        </KButton>
        {offen ? (
          <KButton size="touch" tone="quiet" data-testid="island-sonnenstunden-abbrechen" onClick={() => void abbrechen()}>
            Abbrechen
          </KButton>
        ) : null}
      </div>

      {lauf ? (
        <p className="visisl-hinweis-klein" data-testid="island-sonnenstunden-status">
          Status: {lauf.status}
        </p>
      ) : null}

      {lauf?.status === 'kein-blender-worker' && lauf.message ? (
        // E11: die Bridge-`message` WORTGLEICH, kein Umschreiben/Beschönigen.
        <p className="visisl-hinweis" data-testid="island-sonnenstunden-hinweis">
          {lauf.message}
        </p>
      ) : null}

      {lauf?.status === 'error' && lauf.fehler ? (
        <p className="visisl-hinweis" data-testid="island-sonnenstunden-fehler">
          {lauf.fehler}
        </p>
      ) : null}

      {ergebnis ? (
        <div className="visisl-hinweis-klein" data-testid="island-sonnenstunden-ergebnis">
          <p>Sonnenstunden: {ergebnis.stunden.toFixed(1)} h</p>
          <p>Kriterium erfüllt: {ergebnis.kriteriumErfuellt ? 'ja' : 'nein'}</p>
          <p>Methode: {ergebnis.methode}</p>
        </div>
      ) : null}
    </div>
  );
}

visInhaltsRegistry.registriere('sonnenstunden', { Stufe2: SonnenstundenStufe2, Stufe3: SonnenstundenStufe2 });
