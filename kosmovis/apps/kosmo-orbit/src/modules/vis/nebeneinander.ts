/**
 * Entscheid 117a (Owner per Klickfrage, 21.10.2026; Entwurfsflaeche Blatt 35 «Grundbild neben KI-Bild») — W-4,
 * NEBENEINANDER.
 *
 * WARUM: Die Messungen 298 und 300 haben gezeigt, dass das KI-Bild das Licht der Stimmung nicht verlaesslich
 * uebernimmt — mit Bildeingang kommt es bis Staerke 0,9 nur als Gipsmodell mit Licht, bei 0,95 verliert das Haus die
 * Form. Statt beides in einem Bild zu mischen, steht das gerenderte Grundbild (Blender, Sonne und Schatten echt) NEBEN
 * dem KI-Bild (Entwurf, Grundsatz 97). Bildeingang und Farbabgleich bleiben Messschalter am Heim-PC, ab Werk aus.
 *
 * WAS DAFUER GESCHIEHT — kein neues Vertragsfeld, kein Umbau am Heim-PC:
 *  1. Der Render-Knoten bestellt das Grundbild von sich aus mit: `render.passes` enthaelt `schoenbild`
 *     (`mitGrundbild`); was schon bestellt war, bleibt. Der Heim-PC legt es je Kamera als `<kamera>__schoenbild.png`
 *     unter `ebenen` neben das KI-Bild — auch auf einer wiederverwendeten Grundlage.
 *  2. Nach dem Lauf zeigt der Knoten KI-Bild und Grundbild gleich gross nebeneinander (`grundbildZumBild` findet die
 *     Ebene zur Kamera des gezeigten Bildes). Umschalter «nebeneinander · nur KI · nur Grundbild», Vorgabe
 *     nebeneinander, als flacher Knoten-Parameter (`ANSICHT_PARAM`) — ueberlebt ein Neuladen, rueckgaengig machbar.
 *  3. Fehlt das Grundbild (aelterer Lauf, Heim-PC ohne Ebene), steht die KI-Kachel allein, ohne Luecke und ohne
 *     Umschalter.
 *
 * NICHT: der Varianten-Knoten (dort nur das KI-Bild, Blatt 35 C — das Grundbild gilt fuer alle Varianten gleich und
 * steht am Render-Knoten), «Grundlage rendern» (das Bild IST dann das Grundbild), Strichzeichnung und «nur Cycles»
 * (kein KI-Schritt) und die Skizze (sie rechnet ohne Blender-Bild).
 */

/** Die drei Ansichten des Umschalters. */
export type BildAnsicht = 'nebeneinander' | 'nur-ki' | 'nur-grundbild';

/** Der Parameter am Render-Knoten (`vis.nodeParametrieren`). */
export const ANSICHT_PARAM = 'bildAnsicht';

/** Vorgabe am Knoten (Blatt 35 A, nach Empfehlung). */
export const ANSICHT_VORGABE: BildAnsicht = 'nebeneinander';

export const ANSICHTEN: readonly BildAnsicht[] = ['nebeneinander', 'nur-ki', 'nur-grundbild'];

/** Wortlaut am Knoten (Blatt 35). */
export const ANSICHT_NAME: Record<BildAnsicht, string> = {
  nebeneinander: 'nebeneinander',
  'nur-ki': 'nur KI',
  'nur-grundbild': 'nur Grundbild',
};

/** Die Kurzhilfe am Umschalter (eine fuer alle drei Reiter — `KTabs` traegt keine je Reiter). */
export const ANSICHT_KURZHILFE =
  'Ansicht: KI-Bild und Grundbild nebeneinander, nur das KI-Bild (Entwurf) oder nur das Grundbild (gerendert, Sonne und Schatten echt). Gilt auch für das Bild am Knoten.';

/**
 * Am Knoten nebeneinander nur, wenn jedes Bild mindestens so breit bleibt (Vorgabe des UI-Workers) — sonst faellt
 * die Ansicht auf das KI-Bild zurueck, statt die Bilder zu stauchen.
 */
export const BILD_MIN_BREITE = 96;
/** Abstand zwischen den zwei Bildern am Knoten (px, `--k-s1`). */
export const BILD_LUECKE = 4;

export function nebeneinanderPasst(breite: number): boolean {
  return (breite - BILD_LUECKE) / 2 >= BILD_MIN_BREITE;
}

/**
 * Was der Knoten wirklich zeigt: ohne Grundbild immer das KI-Bild (allein, ohne Luecke); «nebeneinander» nur, wenn
 * es in die Breite passt, sonst das KI-Bild (`rueckfall: true`).
 */
export function wirksameAnsicht(
  wahl: BildAnsicht,
  hatGrundbild: boolean,
  breite: number,
): { ansicht: BildAnsicht; rueckfall: boolean } {
  if (!hatGrundbild) return { ansicht: 'nur-ki', rueckfall: false };
  if (wahl === 'nebeneinander' && !nebeneinanderPasst(breite)) return { ansicht: 'nur-ki', rueckfall: true };
  return { ansicht: wahl, rueckfall: false };
}

/** Beschriftung der zwei Kacheln (Blatt 35). */
export const KI_BILD_NAME = 'KI-Bild';
export const GRUNDBILD_NAME = 'Grundbild mit Licht';

/** Die Wahl am Knoten; alles Unbekannte ist die Vorgabe. */
export function bildAnsichtAmKnoten(params: Record<string, unknown> | undefined): BildAnsicht {
  const a = params?.[ANSICHT_PARAM];
  return a === 'nur-ki' || a === 'nur-grundbild' ? a : ANSICHT_VORGABE;
}

type Passes = 'alle' | readonly ('schoenbild' | 'tiefe' | 'material-id')[];

/**
 * Die Paesse einer Bestellung MIT Grundbild: ohne Angabe nur `schoenbild`; `'alle'` bleibt `'alle'` (enthaelt es);
 * eine Liste behaelt ihre Paesse und bekommt `schoenbild` dazu, falls es fehlt.
 */
export function mitGrundbild(passes?: Passes): Passes {
  if (passes === 'alle') return 'alle';
  if (passes === undefined) return ['schoenbild'];
  return passes.includes('schoenbild') ? passes : [...passes, 'schoenbild'];
}

/** Eine Ebene, wie das Ergebnis sie meldet (`RenderResult.ebenen[]`) — nur was hier gelesen wird. */
export interface EbeneKurz {
  kamera: string;
  art: string;
  datei: string | null;
}

/** Der Stamm eines Bildnamens («Suedost.png» → «Suedost»): so nennt der Heim-PC die Kamera. */
function stamm(name: string): string {
  const i = name.lastIndexOf('.');
  return i > 0 ? name.slice(0, i) : name;
}

/**
 * Das Grundbild zur Kamera des gezeigten Bildes, oder `undefined`. Die Kamera kommt aus dem Bildnamen (der Heim-PC
 * legt `<kamera>.png` ab); passt keiner, aus der Liste je Kamera an derselben Stelle wie das Bild in `bilder`. Eine
 * bestellte, aber fehlende Ebene (`datei: null`) gibt kein Grundbild — dann steht die KI-Kachel allein.
 */
export function grundbildZumBild(
  ebenen: readonly EbeneKurz[] | undefined,
  bild: string,
  bilder?: readonly string[],
  kameras?: readonly { kamera: string }[],
): string | undefined {
  const schoen = (ebenen ?? []).filter((e) => e.art === 'schoenbild' && e.datei !== null);
  if (schoen.length === 0 || !bild) return undefined;
  const direkt = schoen.find((e) => e.kamera === stamm(bild));
  if (direkt) return direkt.datei ?? undefined;
  const i = bilder?.indexOf(bild) ?? -1;
  const kamera = i >= 0 ? kameras?.[i]?.kamera : undefined;
  return kamera !== undefined ? (schoen.find((e) => e.kamera === kamera)?.datei ?? undefined) : undefined;
}
