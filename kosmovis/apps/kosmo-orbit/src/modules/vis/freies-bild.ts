/**
 * Owner-Entscheid Masstreue (30.10.2026, woertlich): «jedes bild muss basierend auf blender render und
 * multipasses laufen». Damit ist der Visbox-Entscheid 149 «Freies Bild (ohne Grundbild)» vom 24.10.2026
 * aufgehoben (nicht zu verwechseln mit dem KosmoOrbit-E149, Claude-Anschluss). Wie in KosmoOrbit A0049; hier A0256.
 *
 * Was bleibt: ein BEREITS gerechnetes freies Bild in einem bestehenden Projekt bleibt lesbar und traegt weiter
 * seine Marke «freies Bild», damit es nirgends wie ein modelltreues Bild aussieht. Gelesen wird, was das Ergebnis
 * meldet (`freies_bild: true` in `render-result` oder der Satz «FREIES BILD (Entscheid 149) …» in
 * `qa.verdict.hinweise`).
 *
 * Was weg ist: jeder Weg, ein freies Bild NEU zu bestellen — der Haken am Varianten-Knoten, das Wort «Frei» in der
 * Zeile «Güte», das Feld `vis.freies_bild` in der Bestellung. Wer es trotzdem verlangt (ein Aufruf mit
 * `freiesBild: true`), bekommt `FREIES_BILD_ABSAGE`, und an die Bruecke geht nichts. Eine alte Wahl am Knoten
 * (`freiesBild: true` aus einem Projekt vor dem 30.10.) wird nicht mehr gelesen: der Knoten rechnet auf der
 * Grundlage. Der Server sperrt den Weg ebenfalls (A0051). Reine Logik, ohne React.
 */

/** Der alte Parameter am Render- und am Varianten-Knoten — nur noch Name, gelesen wird er nirgends. */
export const FREIES_BILD_PARAM = 'freiesBild';

/** Der Satz, mit dem jede Bestellung ohne Grundlage abgewiesen wird (wie `FREIES_BILD_ABSAGE` in KosmoOrbit A0049). */
export const FREIES_BILD_ABSAGE =
  'Kein KI-Bild ohne Grundlage: jedes Bild beruht auf einem Blender-Render mit Multipässen derselben Kamera. Ein freies Bild (ohne Grundbild) gibt es nicht mehr.';

/** Die Marke am Bild. */
export const FREIES_BILD_MARKE_TEXT = 'freies Bild';
export const FREIES_BILD_MARKE_HINWEIS =
  'Freies Bild: ohne das Grundbild als Start gerechnet, nur aus Text und Tiefe — ein Stimmungsbild, kein modelltreues Bild. Das Haus kann vom Modell abweichen; die Sätze zu Form und Fenster bleiben stehen.';

/** Der Anfang des Satzes der Gegenseite — wortgleich mit dem Visbox-Kern (`kosmo_szene.SATZ_FREIES_BILD`). */
export const SATZ_FREIES_BILD = 'FREIES BILD (Entscheid 149)';

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
