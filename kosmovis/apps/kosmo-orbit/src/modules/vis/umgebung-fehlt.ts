/**
 * «OHNE UMGEBUNG» AM RENDER-KNOTEN (Bitte des Integrators, Runde 29, 14.10.2026).
 *
 * Geht ein Splat nicht als Umgebung mit (etwa: aus dem Dateidialog ohne Pfad geladen), traegt
 * der Lauf `NodeLauf.umgebungFehlt` den Grund als Satz (aus dem Splat-Teil des Auftrags,
 * `vis-jobs.ts`). Der Render-Knoten zeigt dann, solange der Lauf steht, eine Zeile
 * «Ohne Umgebung: <Grund>». Fehlt das Feld, ging die Umgebung mit oder es gab keinen Splat —
 * keine Zeile.
 *
 * Seit dem Nachzug auf Runde 29 steht das Feld am Typ (`NodeLauf.umgebungFehlt?: string`) und
 * wird nur noch so gelesen. Die frueheren duldsamen Formen (`{ grund }`, `true`) gab es im
 * Integrator-Stand nie; sie sind entfallen. Ein leerer Satz zaehlt wie ein fehlendes Feld —
 * `vis-jobs.ts` setzt es nur mit Grund.
 */
import type { NodeLauf } from './vis-runtime';

export function umgebungFehltSatz(lauf: Pick<NodeLauf, 'umgebungFehlt'> | null | undefined): string | null {
  const satz = lauf?.umgebungFehlt;
  if (typeof satz !== 'string') return null;
  const t = satz.trim();
  return t ? t : null;
}
