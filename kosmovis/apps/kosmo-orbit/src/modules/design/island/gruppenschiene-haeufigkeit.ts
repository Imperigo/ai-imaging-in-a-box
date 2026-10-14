/**
 * Gruppenschiene — Haeufigkeits-Zaehler je Werkzeug (K1,
 * `docs/AUFTRAG-EINBAU-B163-KOSMODESIGN-AN-INTEGRATOR.md`: «das Programm
 * zaehlt jede Aktivierung je Werkzeug (lokal gespeichert) und zeigt die drei
 * meistbenutzten. Bis 20 Aktivierungen gezaehlt sind: Auswahl, Wand,
 * Oeffnung. Heute zaehlt das Programm nichts — das ist neu zu bauen.»).
 *
 * Reine, pure Funktionen ueber `window.localStorage` — kein Store-Feld (der
 * Zaehler ist reiner UI-Ruhestand der Gruppenschiene, kein Kosmo-/Yjs-Doc-
 * Feld, dasselbe Muster wie `state/touch-undo.ts`). Defensiv gegen fehlendes
 * `localStorage` (SSR/Privatmodus) UND gegen ein kaputtes/fremdes Feld
 * (Muster `state/touch-undo.ts`s `try/catch`-Lesart) — ein Zaehler, der beim
 * ersten fremden Wert wirft, waere schlimmer als gar keiner.
 */

/** Speicherschluessel — versioniert (`.v1`), falls sich die Form je aendert. */
export const HAEUFIGKEIT_SPEICHER_SCHLUESSEL = 'kosmo.island.zeichnen.gruppenschiene.haeufigkeit.v1';

/** K1, woertlich: «Bis 20 Aktivierungen gezaehlt sind». */
export const HAEUFIGKEIT_VORGABE_SCHWELLE = 20;

/** K1, woertlich: «Auswahl, Wand, Oeffnung» — als Katalog-`id`s. */
export const HAEUFIGKEIT_VORGABE: readonly string[] = ['auswahl', 'wand', 'oeffnung'];

type Zaehlung = Record<string, number>;

function leseZaehlung(): Zaehlung {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return {};
    const roh = window.localStorage.getItem(HAEUFIGKEIT_SPEICHER_SCHLUESSEL);
    if (!roh) return {};
    const wert: unknown = JSON.parse(roh);
    if (typeof wert !== 'object' || wert === null || Array.isArray(wert)) return {};
    const bereinigt: Zaehlung = {};
    for (const [id, anzahl] of Object.entries(wert as Record<string, unknown>)) {
      if (typeof anzahl === 'number' && Number.isFinite(anzahl) && anzahl >= 0) bereinigt[id] = anzahl;
    }
    return bereinigt;
  } catch {
    // Kaputtes JSON, blockiertes localStorage (Privatmodus) o. Ä. — ein
    // leerer Zaehler ist der sichere Rueckfall, kein Wurf.
    return {};
  }
}

function schreibeZaehlung(zaehlung: Zaehlung): void {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return;
    window.localStorage.setItem(HAEUFIGKEIT_SPEICHER_SCHLUESSEL, JSON.stringify(zaehlung));
  } catch {
    // Speichern darf nie die Aktivierung selbst zum Scheitern bringen.
  }
}

/** Summe aller gezaehlten Aktivierungen (fuer die 20er-Schwelle). */
function gesamtsumme(zaehlung: Zaehlung): number {
  return Object.values(zaehlung).reduce((summe, n) => summe + n, 0);
}

/**
 * Zaehlt EINE Aktivierung des Werkzeugs `werkzeugId` hoch — aufgerufen bei
 * JEDER Erst-Aktivierung eines Zeichnen-Werkzeugs ueber die Gruppenschiene
 * (Rail-Knopf, Gruppenkarte-Kachel ODER Suchtreffer — derselbe Aufrufer,
 * `IslandShell.tsx`s `aufWerkzeugKlick`).
 */
export function registriereAktivierung(werkzeugId: string): void {
  const zaehlung = leseZaehlung();
  zaehlung[werkzeugId] = (zaehlung[werkzeugId] ?? 0) + 1;
  schreibeZaehlung(zaehlung);
}

/**
 * Die drei meistbenutzten Werkzeuge — vor Erreichen der 20er-Schwelle
 * (K1, woertlich) die feste Vorgabe `Auswahl, Wand, Oeffnung`. Bei
 * Punktgleichheit entscheidet rein die Alphabetik (`localeCompare` auf der
 * Katalog-`id`) — deterministisch, damit die Reihenfolge in der Leiste
 * nicht bei jedem Aufruf hin- und herspringt. K1 selbst verlangt keinen
 * bestimmten Tie-Break; ein frueherer Kommentar hier beschrieb zusaetzlich
 * einen Vorgabe-Vorrang («zuerst in der Vorgabe genannte, dann
 * alphabetisch»), den der Code nie hatte (Gegenpruefung 25.09.2026,
 * Pruefer-Fund) — berichtigt, kein Verhalten geaendert.
 */
export function topDreiHaeufigste(): string[] {
  const zaehlung = leseZaehlung();
  if (gesamtsumme(zaehlung) < HAEUFIGKEIT_VORGABE_SCHWELLE) return [...HAEUFIGKEIT_VORGABE];
  return Object.entries(zaehlung)
    .sort(([idA, nA], [idB, nB]) => {
      if (nB !== nA) return nB - nA;
      return idA.localeCompare(idB);
    })
    .slice(0, 3)
    .map(([id]) => id);
}
