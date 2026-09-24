import { create } from 'zustand';
import type { BlenderSimJob, BakeJob } from '@kosmo/contracts';

/**
 * Blender-Jobs-Laufzeit (v0.8.9 §9 E11, PBL2) — schlanker Zustand-Store für
 * laufende BlenderSim-/Bake-Jobs, EIGENE Datei (Muster `vis-runtime.ts`,
 * aber bewusst getrennt: `vis-runtime.ts` ist Sanktion-13/14-tabu für dieses
 * Paket UND semantisch ein anderer Bereich — Node-Graph-Läufe vs.
 * Sonnenstunden-/Bake-Anfragen ausserhalb jedes Graphen).
 *
 * Wie `vis-runtime.laeufe`: BEWUSST ausserhalb des Doc (kein Undo, kein Yjs-
 * Sync) — ein Job-Status ist Laufzeit, kein Modell-Feld (Sanktion 14: kein
 * neues Doc-Feld für Sonnen-Params).
 *
 * Der Store hält NUR Zustand — Poll-Logik (Intervall, `holeBlenderSimJob`/
 * `holeBakeJob` aufrufen, Timeout) gehört in die aufrufende Komponente
 * (Muster `VisWorkspace.tsx`s `EinfachAnsicht`/`NodeCanvas.tsx`s Poll-Effekt),
 * nicht hierher.
 */

export type BlenderJobKind = 'blender-sim' | 'bake';

/** Wortgleich zu `BlenderSimJobStatus`/`BakeJobStatus` (`@kosmo/contracts`) —
 * beide Verträge teilen dieselben Statuswerte (s. `blender-sim.ts`/
 * `bake-job.ts` Kopfkommentare), darum EIN gemeinsamer Typ hier. */
export type BlenderJobStatus =
  | 'awaiting_approval'
  | 'queued'
  | 'running'
  | 'done'
  | 'error'
  | 'cancelled'
  | 'kein-blender-worker';

/** Zustände, in denen ein Blender-Job noch «offen» ist (Poll fragt sie ab). */
export const OFFENE_BLENDER_JOB_STATUS: readonly BlenderJobStatus[] = [
  'awaiting_approval',
  'queued',
  'running',
];

export interface BlenderJobLauf {
  kind: BlenderJobKind;
  status: BlenderJobStatus;
  jobId?: string;
  /** Ehrliche Begründung der Bridge, v.a. bei `kein-blender-worker` — wird
   *  WORTGLEICH angezeigt (E11: keine erfundene Zahl, keine «ungefähr»-
   *  Formulierung). */
  message?: string;
  /** Freigabe-Token aus dem Create-Response — nötig für `/approve`. */
  approvalToken?: string;
  /** Das eingebettete Ergebnis, sobald `done` (nur `blender-sim`/
   *  `art:'sonnenstunden'` befüllt es in dieser Version). */
  result?: BlenderSimJob['result'] | BakeJob['result'];
  /** Lokaler Fehlertext (Netz-/Bridge-Fehler ausserhalb des Job-Records). */
  fehler?: string;
  /** Date.now() beim Absenden — Basis für einen künftigen Timeout-Wächter
   *  (Muster `vis-runtime.gestartetUm`, hier nicht selbst ausgewertet). */
  gestartetUm?: number;
}

interface BlenderJobsRuntime {
  /** Geschlüsselt nach einem vom Aufrufer gewählten, stabilen Key (Muster
   *  `vis-runtime.laeufe`, dort `nodeId`) — hier z.B. `'sonnenstunden'` für
   *  die Sonne-Insel (genau ein aktiver Lauf dieser Art zur selben Zeit). */
  jobs: Record<string, BlenderJobLauf>;
  setzeJob: (key: string, lauf: BlenderJobLauf) => void;
  patchJob: (key: string, patch: Partial<BlenderJobLauf>) => void;
  entferneJob: (key: string) => void;
}

export const useBlenderJobsRuntime = create<BlenderJobsRuntime>((set) => ({
  jobs: {},
  setzeJob: (key, lauf) => set((s) => ({ jobs: { ...s.jobs, [key]: lauf } })),
  patchJob: (key, patch) =>
    set((s) => {
      const alt = s.jobs[key];
      if (!alt) return s;
      return { jobs: { ...s.jobs, [key]: { ...alt, ...patch } } };
    }),
  entferneJob: (key) =>
    set((s) => {
      const rest = { ...s.jobs };
      delete rest[key];
      return { jobs: rest };
    }),
}));

/**
 * Test-Hook (Playwright) — Muster `window.__kosmoVisRuntime` (`vis-runtime.ts`):
 * rein lesend/schreibend, ruft NUR bestehende Store-Funktionen auf.
 * `e2e/blender-bridge.spec.ts` nutzt ihn, um einen Blender-Job-Zustand ohne
 * einen echten Bridge-Roundtrip zu seeden (z.B. für UI-Grenzfälle).
 */
if (typeof window !== 'undefined') {
  (window as never as Record<string, unknown>)['__kosmoBlenderJobs'] = {
    setzeJob: (key: string, lauf: BlenderJobLauf) => useBlenderJobsRuntime.getState().setzeJob(key, lauf),
    patchJob: (key: string, patch: Partial<BlenderJobLauf>) => useBlenderJobsRuntime.getState().patchJob(key, patch),
    entferneJob: (key: string) => useBlenderJobsRuntime.getState().entferneJob(key),
    state: () => useBlenderJobsRuntime.getState().jobs,
  };
}
