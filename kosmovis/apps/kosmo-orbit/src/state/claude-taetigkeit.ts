/**
 * R37, Video-Befund L1-7 (Demolauf 20.10.2026): der Tätigkeitsstrom.
 *
 * Was Claude über den MCP-Weg gerade tut, als kurze Liste für eine
 * Erzählzeile in der Oberfläche («Claude zeichnet eine Wand …»). Gefüllt an
 * genau zwei Stellen beider Verbindungswege (Browser und Desktop,
 * `claude-anschluss.ts`): beim Eingang eines Aufrufs `beginneTaetigkeit`,
 * an der Antwortstelle `beendeTaetigkeit` — auch für Antworten, die erst mit
 * «Anwenden»/«Ablehnen» einer Karte kommen. Eine Tätigkeit ohne `ende` läuft
 * noch oder wartet auf eine Karte.
 *
 * Form mit UI abgestimmt (Zentrale 20.10.2026): {id, werkzeug, urheber,
 * beginn, ende?, fehler?, versuch?}; Zeiten in ms seit Epoche. Laufzeit-Store,
 * nicht im Doc (kein Yjs, kein Undo).
 */
import { create } from 'zustand';

export type TaetigkeitUrheber = 'claude' | 'kosmo';

export interface ClaudeTaetigkeit {
  /** Kennung des Aufrufs (vom MCP-Server, eindeutig je Aufruf). */
  id: string;
  werkzeug: string;
  urheber: TaetigkeitUrheber;
  beginn: number;
  ende?: number;
  /** Erste Zeile der Antwort, wenn sie nicht ok war (gekürzt). */
  fehler?: string;
  /** Ab 2: derselbe Werkzeugaufruf direkt nach einem Fehlschlag desselben Werkzeugs. */
  versuch?: number;
}

export const TAETIGKEIT_MAX = 50;
const FEHLER_MAX_ZEICHEN = 160;

interface TaetigkeitZustand {
  eintraege: ClaudeTaetigkeit[];
}

export const useClaudeTaetigkeit = create<TaetigkeitZustand>(() => ({ eintraege: [] }));

/** Ein Aufruf ist eingegangen. Ein zweiter Eingang derselben Kennung (Neuverbinden) zählt nicht doppelt. */
export function beginneTaetigkeit(
  id: string,
  werkzeug: string,
  urheber: TaetigkeitUrheber = 'claude',
  jetzt: number = Date.now(),
): void {
  useClaudeTaetigkeit.setState((z) => {
    if (z.eintraege.some((e) => e.id === id)) return z;
    const vorher = [...z.eintraege].reverse().find((e) => e.urheber === urheber);
    const versuch =
      vorher && vorher.werkzeug === werkzeug && vorher.fehler !== undefined ? (vorher.versuch ?? 1) + 1 : undefined;
    const neu: ClaudeTaetigkeit = { id, werkzeug, urheber, beginn: jetzt, ...(versuch !== undefined ? { versuch } : {}) };
    return { eintraege: [...z.eintraege, neu].slice(-TAETIGKEIT_MAX) };
  });
}

/** Die Antwort ist hinausgegangen. Unbekannte Kennungen werden übergangen. */
export function beendeTaetigkeit(antwort: { kennung: string; ok: boolean; text: string }, jetzt: number = Date.now()): void {
  useClaudeTaetigkeit.setState((z) => {
    const i = z.eintraege.findIndex((e) => e.id === antwort.kennung);
    if (i < 0 || z.eintraege[i]!.ende !== undefined) return z;
    const fehler = antwort.ok ? undefined : (antwort.text.split('\n')[0] ?? '').slice(0, FEHLER_MAX_ZEICHEN);
    const eintraege = z.eintraege.slice();
    eintraege[i] = { ...eintraege[i]!, ende: jetzt, ...(fehler !== undefined ? { fehler } : {}) };
    return { eintraege };
  });
}

/** Was noch läuft oder auf eine Karte wartet, älteste zuerst. */
export function laufendeTaetigkeiten(): ClaudeTaetigkeit[] {
  return useClaudeTaetigkeit.getState().eintraege.filter((e) => e.ende === undefined);
}

/** Die letzten `n` Einträge, jüngste zuletzt. */
export function letzteTaetigkeiten(n: number): ClaudeTaetigkeit[] {
  return n <= 0 ? [] : useClaudeTaetigkeit.getState().eintraege.slice(-n);
}

/** Für Proben und beim Trennen nicht nötig: der Strom bleibt als Rückblick stehen. */
export function leereTaetigkeiten(): void {
  useClaudeTaetigkeit.setState({ eintraege: [] });
}
