/**
 * STELLVERTRETER (Visbox) (Kopfteile S2, Entscheide 105–108, 114–116, 20.10.2026) fuer
 * `state/claude-anschluss.ts` von KosmoOrbit.
 *
 * In KosmoOrbit haelt diese Datei die Leitung zum MCP-Server (Ereignisstrom bzw. Tauri), fuehrt
 * Claudes Aufrufe aus und legt die Karten. **In Visbox laeuft der MCP-Kern in der Mac-App**
 * (`Claude/Claudeanschluss.swift`, `Kizentrale`), die Aufrufe gehen an den KI-Werkzeugsatz der
 * Knotenansicht (`modules/vis/ki-werkzeuge.ts`, woertlich) — und die Karten liegen dort. Dieser
 * Stellvertreter fuehrt darum nur den **Zustand**, den die woertlichen Teile lesen (dazu `kartenOffen`/`kartenFokus`)
 * (`ClaudeAnschluss.tsx`, `ErzaehlZeile.tsx`, `ClaudeFensterRahmen.tsx`):
 *
 *  - `verbunden`, `internet` — von der Mac-App (`window.visboxWirt.lage({claude})`, `setzeClaudeLage`);
 *  - `vorschlaege` — die offenen Karten von Claude aus dem Werkzeugsatz (`haengeAnWerkzeugsatz`);
 *  - `zuletztAktiv` und der Taetigkeitsstrom (`state/claude-taetigkeit.ts`, woertlich) — aus seinen
 *    Ereignissen.
 *
 * «Anwenden»/«Ablehnen» entscheiden die Karte im Werkzeugsatz (`entscheide`); dessen Ereignis
 * «entschieden» geht ueber den Boten `visboxKi` an die App und weckt dort den wartenden Aufruf.
 * Eine eigene Antwort ueber die Leitung gibt es darum nicht (`antworte` tut nichts).
 *
 * Die Karten des Assistenten (Stufe 5) stehen nicht hier, sondern in der Mac-App und im Gespraechsfeld;
 * die Marke «Claude» zeigt nur Claudes eigene.
 */
import { create } from 'zustand';
import { abonniere, entscheide, offeneVorschlaege, VIS_PAKET, type KiVorschlag } from '../modules/vis/ki-werkzeuge';
import { beendeTaetigkeit, beginneTaetigkeit } from './claude-taetigkeit';

/** Wortgleich wie dort; in Visbox ohne Bedeutung (keine Leitung aus der Seite). */
export const CLAUDE_STANDARD_ADRESSE = 'http://127.0.0.1:8630';
export const CLAUDE_ADRESSE_SCHLUESSEL = 'kosmo.claude.adresse';

/** Eine Karte, so wie die Marke sie zeigt (Teilmenge der Form dort). */
export interface ClaudeVorschlag {
  kennung: string;
  commandId: string;
  params: unknown;
  zusammenfassung: string;
  werkzeug?: string;
  /** Bei einem Paket: die Schritte als Vorschau (eine Karte, ein Rückgängig). */
  schritte?: { zusammenfassung: string }[];
}

interface ClaudeAnschlussZustand {
  verbunden: boolean;
  vorschlaege: ClaudeVorschlag[];
  internet: boolean;
  zuletztAktiv: number | null;
  /** Wortgleich wie dort (Nachzug Int 1 R63): die Karten unten links an der Marke sind aufgeklappt. */
  kartenOffen: boolean;
  /** Zaehlt jedes «Karten zeigen» der Erzaehlzeile; die Marke fuehrt darauf den Fokus auf das erste «Anwenden». */
  kartenFokus: number;
}

export const useClaudeAnschluss = create<ClaudeAnschlussZustand>(() => ({
  kartenOffen: true,
  kartenFokus: 0,
  verbunden: false,
  vorschlaege: [],
  internet: false,
  zuletztAktiv: null,
}));

/** Die Antwort an die Leitung — in Visbox nie gebraucht (s. Kopf). */
export type ClaudeAntwort = never;

export interface ClaudeVerbindung {
  antworte(antwort: ClaudeAntwort): void;
  stoppe(): void;
}

/** Die Lage von Claude aus der Mac-App (`window.visboxWirt.lage({claude})`). */
export interface ClaudeLage {
  verbunden: boolean;
  internet?: boolean;
}

export function setzeClaudeLage(lage: ClaudeLage): void {
  useClaudeAnschluss.setState({ verbunden: lage.verbunden === true, internet: lage.internet === true });
}

/** Die Seite haelt keine Leitung; die Marke startet hier darum nichts. */
export function starteClaudeVerbindung(_adresse: string = CLAUDE_STANDARD_ADRESSE): ClaudeVerbindung {
  return { antworte: () => {}, stoppe: () => {} };
}

/** Ob die Marke anschliessen darf — ein- und ausgeschaltet wird Claude in der Mac-App. */
export function claudeAnschlussErlaubt(_speicher?: Storage, _webdriver?: boolean): boolean {
  return true;
}

export function meldeClaudeAnschlussAus(): void {
  useClaudeAnschluss.setState({ verbunden: false });
}

/** Eine Karte des Werkzeugsatzes in der Form der Marke. */
export function alsClaudeVorschlag(v: KiVorschlag): ClaudeVorschlag {
  const erster = v.schritte[0];
  return {
    kennung: v.kennung,
    commandId: erster?.commandId ?? v.werkzeug,
    params: erster?.params ?? null,
    zusammenfassung: v.zusammenfassung,
    werkzeug: v.werkzeug,
    ...(v.werkzeug === VIS_PAKET || v.schritte.length > 1 ? { schritte: v.schritte.map((s) => ({ zusammenfassung: s.zusammenfassung })) } : {}),
  };
}

function leseKarten(): void {
  useClaudeAnschluss.setState({
    vorschlaege: offeneVorschlaege()
      .filter((v) => v.urheber === 'claude')
      .map(alsClaudeVorschlag),
  });
}

/** «Anwenden» an der Karte: entscheidet im Werkzeugsatz. Die Antwort an Claude geht ueber die App. */
export function wendeClaudeVorschlagAn(kennung: string): null {
  entscheide(kennung, true);
  return null;
}

/** «Ablehnen» an der Karte. */
export function lehneClaudeVorschlagAb(kennung: string): null {
  entscheide(kennung, false);
  return null;
}

/**
 * Die Erzaehlzeile oben Mitte fuehrt zu den Karten (Nachzug Int 1 R63, wortgleich wie dort): aufklappen und den
 * Fokus auf das erste «Anwenden» bitten. Entschieden wird nur an der Karte; die Zeile traegt keine eigenen Knoepfe
 * mehr (bis 0.3.54 hatte sie «Anwenden»/«Ablehnen», der Weg `entscheideClaudeVorschlag` ist darum weg).
 */
export function zeigeClaudeKarten(): void {
  useClaudeAnschluss.setState((z) => ({ kartenOffen: true, kartenFokus: z.kartenFokus + 1 }));
}

/**
 * Haengt den Zustand an die Ereignisse des Werkzeugsatzes: Karten, Taetigkeit, «zuletzt aktiv».
 * Gerufen vom Wirt (`apps/visbox-knoten/src/wirt-bruecke.ts`). Liefert das Abhaengen.
 */
export function haengeAnWerkzeugsatz(): () => void {
  leseKarten();
  return abonniere((e) => {
    if (e.art === 'karte' || e.art === 'entschieden') leseKarten();
    if (e.art !== 'taetigkeit' || e.urheber !== 'claude') return;
    useClaudeAnschluss.setState({ zuletztAktiv: e.zeit });
    if (e.phase === 'beginn') beginneTaetigkeit(e.kennung, e.werkzeug, 'claude', e.zeit);
    else beendeTaetigkeit({ kennung: e.kennung, ok: e.ok, text: e.text }, e.zeit);
  });
}

/**
 * KI-Bedienung Stufe 6 (21.10.2026): die KosmoMaus (`state/kosmo-maus.ts`, woertlich) verwirft beim
 * Projektwechsel auch Claudes offene Karten. In Visbox liegen sie im Werkzeugsatz — der Wirt verwirft
 * sie dort selbst (`visboxKi.verwirf`, neues Dokument), mit «VERWORFEN» an Claude ueber die App. Hier
 * darum nichts doppelt: leer.
 */
export function verwirfClaudeVorschlaege(_grund: string): ClaudeVorschlag[] {
  return [];
}
