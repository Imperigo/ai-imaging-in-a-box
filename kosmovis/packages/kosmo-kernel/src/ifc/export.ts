/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/ifc/export.ts` (KosmoOrbit).
 *
 * Warum (E26, 24.09.2026): Das Original schreibt IFC aus dem Bauwerksmodell von
 * KosmoOrbit. Visbox hat dieses Modell nicht. Das Vis-Werkzeug ruft `exportIfc` nur für
 * eine Innenansicht mit Zonen (`interiorFaehrt`) — in Visbox gibt es keine Zonen im
 * Dokument, der Weg wird also nicht erreicht. Wird er es doch, sagt der Fehler, warum.
 */
import type { KosmoDoc } from '../model/doc';

export function exportIfc(_doc: KosmoDoc, _projectName?: string): string {
  throw new Error(
    'IFC-Ausfuhr gibt es in Visbox nicht: Das Gebäude kommt als fertige Datei aus der Mappe.',
  );
}
