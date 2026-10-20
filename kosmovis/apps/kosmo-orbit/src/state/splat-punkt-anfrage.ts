import { create } from 'zustand';

/**
 * **Einen Punkt auf dem Splat erfragen (Kontrollmass).**
 *
 * Die Oberflaeche (Ampel, Karte, Laengenfeld, Schreiben in die Verortung)
 * stellt die Frage `punktWaehlen()` und wartet auf die Antwort. Die 3D-Ansicht
 * (`modules/design/Viewport3D.tsx`) nimmt den Klick auf den Splat entgegen,
 * antwortet und zeichnet die Kontrollstrecke. Dieser Store ist die Naht
 * dazwischen: kein Modellzustand, nicht persistiert (Muster
 * `state/geschoss-eigenschaften-anfrage.ts`).
 *
 * EINHEIT: Splat-METER im LOKALEN System der Splat-Ebene, also die Koordinaten
 * der Wolke, wie sie in `SplatCloud.positions` stehen, VOR der Verortung
 * (Matrix der Ebene). Nur so misst die Laenge das, was die Verortung
 * korrigieren soll: das Verhaeltnis zwischen Splat-Meter und echtem Meter.
 * ACHTUNG, anders als `splatFangPunkt` (`derive/fang.ts`): jenes nimmt den
 * Punkt in Ansichtskoordinaten, also NACH der Matrix.
 *
 * ENDE EINER ANFRAGE: Klick auf den Splat (Punkt), Esc, Verlassen der
 * 3D-Ansicht oder eine zweite Anfrage (dann endet die erste mit null).
 */
export type SplatM = [number, number, number];

export interface SplatPunktAntwort {
  splat: SplatM;
  ebeneId: string;
}

export interface Kontrollstrecke {
  a: SplatM | null;
  b: SplatM | null;
}

export interface SplatPunktAnfrageZustand {
  /** Wartet gerade eine Anfrage auf einen Klick? */
  offen: boolean;
  /** Die aktuell gezeigte Kontrollstrecke (Splat-Meter), sonst beide null. */
  strecke: Kontrollstrecke;
  punktWaehlen: () => Promise<SplatPunktAntwort | null>;
  /** Zwei Marken mit Linie in Splat-Metern; (null, null) raeumt auf. */
  zeigeKontrollstrecke: (a: SplatM | null, b: SplatM | null) => void;
  laenge: (a: SplatM, b: SplatM) => number;
  /** Fuer die 3D-Ansicht: beantwortet die offene Anfrage (null = abgebrochen). */
  antworte: (p: SplatPunktAntwort | null) => void;
  /** Testweg: beantwortet eine offene Anfrage wie die Ansicht. */
  _antworteFuerTest: (p: SplatPunktAntwort | null) => void;
}

/** Abstand zweier Punkte in Splat-Metern. */
export function laenge(a: readonly number[], b: readonly number[]): number {
  return Math.hypot(b[0]! - a[0]!, b[1]! - a[1]!, b[2]! - a[2]!);
}

// Die Aufloesefunktion ist nicht serialisierbar und gehoert nicht in den Zustand.
let aufloesen: ((p: SplatPunktAntwort | null) => void) | null = null;

const kopie = (p: SplatM | null): SplatM | null => (p ? [p[0], p[1], p[2]] : null);

export const useSplatPunktAnfrage = create<SplatPunktAnfrageZustand>((set, get) => ({
  offen: false,
  strecke: { a: null, b: null },
  punktWaehlen: () => {
    // Eine zweite Anfrage beendet die erste mit null.
    get().antworte(null);
    return new Promise<SplatPunktAntwort | null>((resolve) => {
      aufloesen = resolve;
      set({ offen: true });
    });
  },
  zeigeKontrollstrecke: (a, b) => set({ strecke: { a: kopie(a), b: kopie(b) } }),
  laenge: (a, b) => laenge(a, b),
  antworte: (p) => {
    const fertig = aufloesen;
    aufloesen = null;
    if (get().offen) set({ offen: false });
    fertig?.(p ? { splat: [p.splat[0], p.splat[1], p.splat[2]], ebeneId: p.ebeneId } : null);
  },
  _antworteFuerTest: (p) => get().antworte(p),
}));
