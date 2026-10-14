/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/derive/sheet.ts` (KosmoOrbit, Blatt-Komposition).
 *
 * Runde 26 (14.10.2026): Das Vis-Werkzeug braucht davon nur die Papiergrösse eines Blatts
 * (`sheetPaperSize`, für den freien Bildplatz beim Übergeben eines Renders an ein Blatt).
 * Blätter selbst gibt es in Visbox nicht (`commands/publish.ts` sagt es) — die Komposition
 * mit Plankopf, Rahmen und Ansichten bleibt drüben. `ISO_LANG` und `sheetPaperSize` sind
 * wörtlich.
 */
import type { Sheet, SheetFormat } from '../model/entities';

const ISO_LANG: Record<SheetFormat, { width: number; height: number }> = {
  A0: { width: 1189, height: 841 },
  A1: { width: 841, height: 594 },
  A2: { width: 594, height: 420 },
  A3: { width: 420, height: 297 },
  A4: { width: 297, height: 210 },
  // v0.8.1/P13 (docs/V081-SPEZ.md §7(d)): Rollenformat, identisch zu
  // `blattlayout.ts`s `BLATT_FORMATE.Rolle` (1600×594mm, bewusst NICHT von
  // dort importiert, s. Datei-Kopfkommentar oben zur Trennung der beiden
  // Registrierungen bis zum künftigen Sammelwechsel).
  Rolle: { width: 1600, height: 594 },
};

export function sheetPaperSize(sheet: Pick<Sheet, 'format' | 'orientation'>): {
  width: number;
  height: number;
} {
  const s = ISO_LANG[sheet.format];
  return sheet.orientation === 'quer' ? { ...s } : { width: s.height, height: s.width };
}
