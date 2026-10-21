import type { ModuleId } from '@kosmo/ui';

/**
 * Werkzeug-Stichworte je Station (ursprünglich Serie K / A2, Owner-Befund
 * K12: «Hover zeigt enthaltene Tools»). Reine Datentabelle (unit-testbar) —
 * seit Serie K / F3 die Quelle für die «Fähigkeit»-Hovertexte im neuen
 * Orbit-Startmenü (`OrbitStart.tsx`, Zuordnung in `orbit-werkzeuge.ts`).
 *

 * Ehrlichkeitsregel (Owner-Mandat): jedes Stichwort verweist auf eine WIRKLICH
 * gebaute Fähigkeit des jeweiligen Workspace — belegt gegen den Quellcode
 * unter `src/modules/<station>/`, keine Wunschliste. Wo eine Station von der
 * HomeStation/Bridge abhängt (KosmoVis-Render, KosmoSpeak-Sprache), sagt das
 * Stichwort das offen (keine vorgetäuschte Autonomie).
 *
 * `orbit`/`kosmo` sind bewusst NICHT hier drin: das sind reine Farbton-/Logo-
 * Werte aus `moduleHue` (Kopfzeile, Badges) — nie eine eigene Zentrale-Kachel
 * (siehe `modules` in App.tsx, das nie eine dieser zwei Ids listet).
 */

export type StationModulId = Exclude<ModuleId, 'orbit' | 'kosmo'>;

/** Alle Stations-Ids, exakt wie in `modules` (App.tsx) — dient der
 *  Vollständigkeitsprüfung im Unit-Test. Stand P-SPEZ: 15 (vierzehn +
 *  KosmoSpez, `docs/KOSMOSPEZ-KONZEPT.md`, s. `STATIONS_WERKZEUGE.spez`
 *  unten). */
export const STATIONS_MODUL_IDS: StationModulId[] = [
  'design',
  'draw',
  'sketch',
  'data',
  'vis',
  'publish',
  'prepare',
  'asset',
  'dev',
  'speak',
  'doc',
  'train',
  'trust',
  'paket',
  'spez',
];

export const STATIONS_WERKZEUGE: Record<StationModulId, string[]> = {
  design: [
    'Wände, Decken, Dach zeichnen',
    '2D-Werkplan (Grundriss/Schnitt)',
    'Volumenstudien-Generator',
    'DXF/IFC-Export/Import',
    'Sonnenstudie',
  ],
  draw: ['Modellbaum mit IFC-Identität', 'Mengenauszug / Vorausmasse', 'Ausmass als CSV'],
  sketch: ['Freihandzug → Wandachse', 'Winkel-Snap (0°/45°/90°)', 'Vorschlag vor Übernahme geprüft'],
  data: ['Referenzen- und Bauteilkatalog', 'Materialkatalog mit U-Wert', 'Wissenssuche mit Belegen', 'Trainings-Kuration'],
  vis: ['Render-Jobs an die HomeStation', 'Node-Graph für Render-Prompts', 'Drei-Stimmungen-Serie', 'QA-Verdikt je Ergebnis'],
  publish: ['Blätter und Plansätze', 'Grundriss/Axo/Schnitt platzieren', 'PDF/SVG/Transmittal-Export', 'Renderbild einfügen'],
  prepare: ['Dokumente aufnehmen (Ingest)', 'Wissenssuche mit [Qn]-Belegen', 'OneDrive/Graph-Anbindung', 'Wettbewerbsdossier übernehmen'],
  asset: ['GLB-Objekt-Bibliothek', 'CH-Bauteilkatalog übernehmen', 'Materialkarten (PBR)', 'Ins Modell laden'],
  dev: ['Auftragsbuch erfassen', 'Workorder-Export (Markdown)', 'An HomeStation übergeben'],
  speak: ['Text-Chat mit Kosmo', 'Push-to-Talk-Mikrofon (Bridge)', 'Vorlesen (TTS)', 'Vorschlagskarten mit Undo'],
  doc: ['Selbstdiagnose', 'Hilfe-Themen (Werkzeug-Wissen)', 'Lernjournal-Berichte'],
  train: ['Lernstand-Übersicht', 'Kuration fürs Training', 'JSONL-Trainingspaket-Export'],
  trust: [
    '.kxp-Hyper-Modell exportieren (Modell + Pläne)',
    '.kxp-Paket read-only öffnen und prüfen',
    'Freigabe-Zustandsmaschine mit Verlauf (lokal, Platzhalter-Rollen)',
    'Signatur-Slot ehrlich als unsigniert ausgewiesen',
  ],
  paket: [
    'Sechs reale Exportformate an einem Ort (PDF/SVG/DXF/IFC/Splat/Logo)',
    'Jede Kachel mit ehrlichem Status statt totem Klick',
    '.kxp-Paket-Export gebündelt neben den Dateiformaten',
    'Ein Klick führt zur bestehenden Fach-Station bei fehlendem Kontext',
  ],
  spez: [
    'Sonnenstudie mit echtem Sonnenstand (SunCalc, Klasse B)',
    'Vier Inseln: Studie · Darstellung · Befund · Austausch',
    'Ergebnisliste mit Verlässlichkeitsklasse und Grenzen-Satz',
    'Ehrliche Platzhalter für Klimasteckbrief/Tageslicht/Thermik/Wind',
  ],
};

/** Werkzeuge einer Zentrale-Kachel — leer für `orbit`/`kosmo` (nie als
 *  Kachel gerendert, siehe Kommentar oben), sonst 3–5 ehrliche Stichworte. */
export function werkzeugeFuerStation(id: ModuleId): string[] {
  return id === 'orbit' || id === 'kosmo' ? [] : STATIONS_WERKZEUGE[id];
}
