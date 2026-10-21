/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/derive/sheet.ts` (KosmoOrbit, Blatt-Komposition).
 *
 * Runde 26 (14.10.2026): Das Vis-Werkzeug braucht davon nur die Papiergrösse eines Blatts
 * (`sheetPaperSize`, für den freien Bildplatz beim Übergeben eines Renders an ein Blatt).
 * Blätter selbst gibt es in Visbox nicht (`commands/publish.ts` sagt es) — die Komposition
 * mit Plankopf, Rahmen und Ansichten bleibt drüben. `ISO_LANG` und `sheetPaperSize` sind
 * wörtlich.
 *
 * Bild aufs Blatt (21.10.2026): dazu wörtlich `bildFeldRechteck`, `Druckaufloesung`, `DRUCK_DPI_MIN`,
 * `druckaufloesung` und `druckaufloesungSatz` (Prepare, bild-druckaufloesung) — das Vis-Werkzeug rechnet die
 * Druckauflösung mit genau dieser Funktion. In Visbox wird nichts platziert; die Rechnung steht, damit die Kopie
 * baut und dieselbe Zahl sagt.
 */
import type { ImageAsset, Sheet, SheetFormat, SheetImage } from '../model/entities';
import { bildGroesseAusBase64 } from './bildgroesse';

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

/** Dieselbe Rechnung wie `imagePaperBounds`, mit dem Bild in der Hand (es muss noch nicht im Dokument liegen). */
export function bildFeldRechteck(
  bild: Pick<SheetImage, 'x' | 'y' | 'w' | 'verhaeltnis'>,
  asset: Pick<ImageAsset, 'width' | 'height'> | undefined,
): { x: number; y: number; width: number; height: number } {
  const ratio =
    bild.verhaeltnis && bild.verhaeltnis > 0
      ? bild.verhaeltnis
      : asset?.width && asset?.height
        ? asset.width / asset.height
        : 1.5;
  return { x: bild.x, y: bild.y, width: bild.w, height: bild.w / ratio };
}

/**
 * Video-Demolauf 20.10.2026, L3-A4 / L4-16: ein Rendering stand als Bildschirmausschnitt von
 * 369 px Breite auf einem A0-Plakat — unscharf, und niemand hatte es gesagt. Gerechnet wird die
 * Aufloesung, in der das Bild WIRKLICH gedruckt wird: das Feld fuellt das Bild mit `slice`
 * (`xMidYMid slice`, s. `sheetSvg`), also wird es so skaliert, dass es das Feld in BEIDEN
 * Richtungen deckt — die bedruckte Breite ist `max(Feldbreite, Bildbreite × Feldhoehe/Bildhoehe)`,
 * und `dpi = Pixelbreite / (bedruckte Breite / 25.4)`.
 *
 * Die Pixelgroesse kommt vom Bild (`width`/`height`), sonst gelesen aus seinem Dateikopf
 * (PNG/JPEG); ist sie nirgends zu lesen, `null` — nie geraten. Ist nur die Breite bekannt, ist die
 * Zahl eine Obergrenze (`hoechstens`): `slice` kann das Bild nur groesser setzen, nie kleiner.
 */
export interface Druckaufloesung {
  dpi: number;
  breitePx: number;
  slotBreiteMm: number;
  /** Bedruckte Breite des Bilds (mm) — bei `slice` mindestens die Feldbreite. */
  gedruckteBreiteMm: number;
  /** Nur die Pixelbreite bekannt: die wahre Aufloesung ist hoechstens `dpi`. */
  hoechstens?: true;
}

/** Ab dieser Aufloesung gilt ein Bild als druckreif (Owner entscheidet; gewarnt wird darunter). */
export const DRUCK_DPI_MIN = 150;

export function druckaufloesung(
  asset: Pick<ImageAsset, 'width' | 'height' | 'data'> | undefined,
  slot: { width: number; height: number },
): Druckaufloesung | null {
  if (!asset || !(slot.width > 0)) return null;
  let width = asset.width;
  let height = asset.height;
  if (!(width && width > 0)) {
    const gelesen = asset.data ? bildGroesseAusBase64(asset.data) : null;
    if (!gelesen) return null;
    width = gelesen.width;
    height = gelesen.height;
  }
  const breitePx = width!;
  if (height && height > 0 && slot.height > 0) {
    const mmProPx = Math.max(slot.width / breitePx, slot.height / height);
    return { dpi: 25.4 / mmProPx, breitePx, slotBreiteMm: slot.width, gedruckteBreiteMm: breitePx * mmProPx };
  }
  return { dpi: breitePx / (slot.width / 25.4), breitePx, slotBreiteMm: slot.width, gedruckteBreiteMm: slot.width, hoechstens: true };
}

/** Der Satz dazu, fuer Befehlsantworten und `modell_lesen`: « · Druckaufloesung …». */
export function druckaufloesungSatz(d: Druckaufloesung | null): string {
  if (!d) return ' · Druckauflösung unbekannt (Pixelbreite des Bilds nicht bekannt)';
  const dpi = Math.round(d.dpi);
  const wie = `${d.breitePx} px auf ${Math.round(d.gedruckteBreiteMm)} mm`;
  const vor = d.hoechstens ? 'höchstens ' : '';
  if (d.dpi < DRUCK_DPI_MIN) {
    return ` · WARNUNG Druckauflösung: nur ${vor}${dpi} dpi (${wie}) — für den Druck zu grob, ab ${DRUCK_DPI_MIN} dpi`;
  }
  return ` · Druckauflösung ${vor}${dpi} dpi (${wie})`;
}
