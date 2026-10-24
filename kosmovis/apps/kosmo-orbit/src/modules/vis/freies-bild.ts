/**
 * Visbox-Entscheid 149 (Owner ueber die Zentrale, 24.10.2026, Option 1 nach Visbox-Messung 353):
 * DAS FREIE BILD — bewusst ohne das Grundbild als Start (txt2img mit der Tiefe) und ohne «Umriss
 * halten», fuer ein Stimmungsbild. Der Prompt kommt so an (Licht in den Fenstern, Wiese, Waldrand),
 * Form und Fenster halten dafuer nicht. Darum ist es NIE Vorgabe — Varianten rechnen ohne Wahl vom
 * Grundbild (Bildeingang 0,7 mit «Umriss halten», Entscheid 149) — und es traegt seine Marke ueberall,
 * wo das Bild steht, damit niemand es fuer ein modelltreues Bild haelt.
 *
 * Bestellt wird `vis.freies_bild: true` (Vertrag `render-scene`); die Gegenseite meldet `freies_bild:
 * true` im Ergebnis (`render-result`) und den Satz «FREIES BILD (Entscheid 149) …» in
 * `qa.verdict.hinweise`. Die Saetze zu Form und Fenster bleiben stehen.
 *
 * Die Wahl ist ein flacher Parameter am Knoten (`vis.nodeParametrieren`) — am Varianten-Knoten ein
 * Haken, am Render-Knoten das dritte Wort in der Zeile «Güte». Reine Logik, ohne React.
 */

/** Der Parameter am Render- und am Varianten-Knoten. */
export const FREIES_BILD_PARAM = 'freiesBild';

/** Der Name am Schalter. */
export const FREIES_BILD_NAME = 'Freies Bild (ohne Grundbild)';
/** Das Wort in der Zeile «Güte» am Render-Knoten (dort passt nur ein Wort). */
export const FREIES_BILD_WORT = 'Frei';
/** Der eine Satz zum Schalter. */
export const FREIES_BILD_SATZ =
  'Für ein Stimmungsbild: die KI malt ohne das Grundbild als Start — das Haus kann dann vom Modell abweichen.';
/** Die Kurzhilfe am Schalter: Name und Satz. */
export const FREIES_BILD_HINWEIS = `${FREIES_BILD_NAME}: ${FREIES_BILD_SATZ} Ohne Wahl rechnet eine Variante vom Grundbild (Bildeingang 0,7, Umriss gehalten).`;

/** Die Marke am Bild. */
export const FREIES_BILD_MARKE_TEXT = 'freies Bild';
export const FREIES_BILD_MARKE_HINWEIS =
  'Freies Bild: ohne das Grundbild als Start gerechnet, nur aus Text und Tiefe — ein Stimmungsbild, kein modelltreues Bild. Das Haus kann vom Modell abweichen; die Sätze zu Form und Fenster bleiben stehen.';

/** Der Anfang des Satzes der Gegenseite — wortgleich mit dem Visbox-Kern (`kosmo_szene.SATZ_FREIES_BILD`). */
export const SATZ_FREIES_BILD = 'FREIES BILD (Entscheid 149)';

/** Ist am Knoten das freie Bild gewaehlt? Nur ausdruecklich `true` — alles andere ist die Vorgabe. */
export function freiesBildAmKnoten(params: Record<string, unknown> | undefined): boolean {
  return params?.[FREIES_BILD_PARAM] === true;
}

/**
 * Meldet das Ergebnis ein freies Bild? `freies_bild: true` oben — oder, bei einer Gegenseite, die das
 * Feld noch nicht setzt, der Satz in `qa.verdict.hinweise`. Gelesen ohne den Vertragstyp (wie
 * `gueteAusErgebnis`); ohne Angabe `undefined`, nie ein geratenes `false`.
 */
export function freiesBildAusErgebnis(r: unknown): true | undefined {
  if (typeof r !== 'object' || r === null) return undefined;
  const o = r as { freies_bild?: unknown; qa?: { verdict?: { hinweise?: unknown } } };
  if (o.freies_bild === true) return true;
  const h = o.qa?.verdict?.hinweise;
  if (Array.isArray(h) && h.some((x) => typeof x === 'string' && x.startsWith(SATZ_FREIES_BILD))) return true;
  return undefined;
}

/** Alles, was ein Bild beschreibt (Lauf, Zelle, Verlaufseintrag, Kuratier-Quelle). */
export type MitFreiemBild = { freiesBild?: boolean | undefined } | object | null | undefined;

export function istFreiesBild(x: MitFreiemBild): boolean {
  return typeof x === 'object' && x !== null && (x as { freiesBild?: unknown }).freiesBild === true;
}

/** Zusatz fuer Knopfnamen und Alternativtexte: «, freies Bild» oder nichts. */
export function freiesBildZusatz(x: MitFreiemBild): string {
  return istFreiesBild(x) ? `, ${FREIES_BILD_MARKE_TEXT}` : '';
}
