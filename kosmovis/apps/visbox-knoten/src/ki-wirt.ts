/**
 * Visbox-eigen — der Wirt des KI-Werkzeugsatzes (Plan «KI-Bedienung» Stufe 3, 20.10.2026;
 * Entscheide 105–106f, 108, 114).
 *
 * Die Knotenansicht traegt den Werkzeugsatz (`modules/vis/ki-werkzeuge.ts`, woertlich aus
 * KosmoOrbit). Diese Datei haengt ihn so an, dass die Mac-App ihn bedienen kann:
 *
 *  - `window.visboxKi` — `werkzeuge`, `rufe`, `entscheide`, `offene`, `verwirf`,
 *    `rueckgaengigKi`, `kiVerlauf`. Die App ruft sie mit `callAsyncJavaScript` und liest die
 *    Antwort als JSON-Text (`alsText`), damit nichts an der Umwandlung von WebKit haengt.
 *  - jedes Ereignis (Taetigkeit, Karte, entschieden, kiverlauf) geht an
 *    `webkit.messageHandlers.visboxKi.postMessage` — dort fuehrt die App die Assistent-Leiste
 *    und weckt den wartenden MCP-Aufruf (`Mcpkern.entscheide`).
 *  - Strg+Z nimmt nur die eigenen Schritte zurueck (Entscheid 114): die Wache des Werkzeugsatzes
 *    (`kiVerlaufWache`) wird HIER gesetzt — in KosmoOrbit haelt sie `kosmo-coop.ts`.
 *  - Wechselt das Dokument (eine andere Mappe), fallen offene Karten und der KI-Verlauf weg
 *    (`verwirf`); ebenso, wenn die Seite neu laedt.
 *
 * Im Browser ohne App (Heim-PC, Entwicklungsserver) fehlt `webkit.messageHandlers`: Die
 * Schnittstelle steht trotzdem, die Ereignisse gehen nirgends hin.
 *
 * Die GPU-Freigabe ist auch hier kein Weg: `window.visboxKi` hat nichts, das freigibt.
 */
import { setzeVerlaufWache, useProject } from '../../kosmo-orbit/src/state/project-store';
import { kiSchnittstelle, kiVerlaufWache, verwirfVorschlaege, type KiEreignis } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';

/** Der Bote der Mac-App (`WKScriptMessageHandler` «visboxKi»). */
export interface KiBote {
  postMessage(nachricht: unknown): void;
}

/** Was die App ausser den Ereignissen bekommt: dass die Schnittstelle steht. */
export type KiBotschaft = KiEreignis | { art: 'bereit'; werkzeuge: number } | { art: 'weg'; grund: string };

export const MAPPE_GEWECHSELT = 'Die Mappe in der Knotenansicht wurde gewechselt';
export const SEITE_LAEDT_NEU = 'Die Knotenansicht wird neu geladen';

type MitWebkit = { webkit?: { messageHandlers?: { visboxKi?: KiBote } } };

/** Der Bote, wenn die Seite in der Mac-App laeuft — sonst `null`. */
export function boteDerApp(fenster: unknown): KiBote | null {
  return (fenster as MitWebkit).webkit?.messageHandlers?.visboxKi ?? null;
}

/** Ein Wert als JSON-Text — so liest die App jede Antwort (`callAsyncJavaScript`). */
export function alsText(wert: unknown): string {
  return JSON.stringify(wert ?? null);
}

export type VisboxKi = ReturnType<typeof baueVisboxKi>;

function baueVisboxKi() {
  const ki = kiSchnittstelle();
  return {
    werkzeuge: ki.werkzeuge,
    rufe: ki.rufe,
    entscheide: ki.entscheide,
    offene: ki.offene,
    verwirf: ki.verwirf,
    rueckgaengigKi: ki.rueckgaengigKi,
    kiVerlauf: ki.kiVerlauf,
    alsText,
  };
}

/**
 * Haengt den Werkzeugsatz an `fenster` an und meldet seine Ereignisse an den Boten. Liefert das
 * Abhaengen (fuer Proben).
 */
export function haengeKiAn(fenster: Window, bote: KiBote | null = boteDerApp(fenster)): () => void {
  const ki = kiSchnittstelle();
  const schnitt = baueVisboxKi();
  (fenster as unknown as { visboxKi?: VisboxKi }).visboxKi = schnitt;
  const sende = (b: KiBotschaft) => {
    if (!bote) return;
    try {
      // Als reiner JSON-Wert: WebKit wandelt ihn in ein Woerterbuch, ohne Funktionen und `undefined`.
      bote.postMessage(JSON.parse(alsText(b)));
    } catch (err) {
      console.error('[ki-wirt] Bote warf', err);
    }
  };
  const abEreignisse = ki.abonniere((e) => sende(e));
  setzeVerlaufWache(kiVerlaufWache);
  let doc = useProject.getState().doc;
  const abDoc = useProject.subscribe((s) => {
    if (s.doc === doc) return;
    doc = s.doc;
    verwirfVorschlaege(MAPPE_GEWECHSELT);
  });
  const beimVerlassen = () => {
    verwirfVorschlaege(SEITE_LAEDT_NEU);
    sende({ art: 'weg', grund: SEITE_LAEDT_NEU });
  };
  fenster.addEventListener('pagehide', beimVerlassen);
  sende({ art: 'bereit', werkzeuge: schnitt.werkzeuge().length });
  return () => {
    abEreignisse();
    abDoc();
    fenster.removeEventListener('pagehide', beimVerlassen);
    setzeVerlaufWache(null);
    delete (fenster as unknown as { visboxKi?: VisboxKi }).visboxKi;
  };
}
