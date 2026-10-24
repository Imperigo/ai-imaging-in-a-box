/**
 * Visbox-eigen — der Wirt des KI-Werkzeugsatzes (Plan «KI-Bedienung» Stufe 3, 20.10.2026;
 * Entscheide 105–106f, 108, 114).
 *
 * Die Knotenansicht traegt den Werkzeugsatz (`modules/vis/ki-werkzeuge.ts`, woertlich aus
 * KosmoOrbit). Diese Datei haengt ihn so an, dass die Mac-App ihn bedienen kann:
 *
 *  - `window.visboxKi` — `werkzeuge`, `rufe`, `entscheide`, `offene`, `verwirf`, `stelleWieder`,
 *    `rueckgaengigKi`, `kiVerlauf`, seit Stufe 6 `blickMausWerkzeuge`, `blick`, `maus`. Die App ruft sie mit `callAsyncJavaScript` und liest die
 *    Antwort als JSON-Text (`alsText`), damit nichts an der Umwandlung von WebKit haengt.
 *  - jedes Ereignis (Taetigkeit, Karte, entschieden, kiverlauf) geht an
 *    `webkit.messageHandlers.visboxKi.postMessage` — dort fuehrt die App die Assistent-Leiste
 *    und weckt den wartenden MCP-Aufruf (`Mcpkern.entscheide`).
 *  - Strg+Z nimmt nur die eigenen Schritte zurueck (Entscheid 114): die Wache des Werkzeugsatzes
 *    (`kiVerlaufWache`) wird HIER gesetzt — in KosmoOrbit haelt sie `kosmo-coop.ts`.
 *  - Wechselt das Dokument (eine andere Mappe), fallen offene Karten und der KI-Verlauf weg
 *    (`verwirf`, mit «VERWORFEN» an die App).
 *  - **Laedt die Seite neu, bleiben die Karten** (Strang Karten, 21.10.2026): Die Seite meldet nur
 *    «weg». Die Mac-App haelt die Karten (`Kizentrale`, `Kartenablage`) und gibt sie der neu
 *    angemeldeten Seite zurueck (`stelleWieder`) — die rechnet jede im jetzigen Graph neu durch.
 *    Anlass: Claudes Karte verschwand beim Wechsel zur Visbox-Seite, still.
 *
 * Im Browser ohne App (Heim-PC, Entwicklungsserver) fehlt `webkit.messageHandlers`: Die
 * Schnittstelle steht trotzdem, die Ereignisse gehen nirgends hin.
 *
 * Die GPU-Freigabe ist auch hier kein Weg: `window.visboxKi` hat nichts, das freigibt.
 *
 * **Vollautomatik ohne Klick** (Owner-Entscheid 146, 24.10.2026): `rufe(ruf, modus, voll)` nimmt als
 * drittes die Lage der Vollautomatik, die die App vor jedem Aufruf in «Voll» beim Heim-PC holt
 * (`GET /bruecke/voll`). Damit entscheidet `voll-render.ts`, ob `vis_render`, `vis_varianten` und
 * `vis_grundlage` ohne Karte laufen (höchstens 5 Läufe je Stunde, nie ein Bildmodell mit offener oder
 * Forschungs-Lizenz, Löschen bleibt Karte). «Grundlage rendern» ist ein Werkzeug
 * (`grundlage-werkzeug.ts`). Ob die Grafikkarte dann ohne «Freigeben» startet, entscheidet der Heim-PC.
 *
 * **Blick und Maus** (Plan «KI-Bedienung» Stufe 6, 21.10.2026; Vorlage `kosmo_blick`/`kosmo_maus`
 * von KosmoOrbit, woertlich in `state/kosmo-maus.ts`): `blick(urheber, argumente)` gibt das Lagebild
 * der Knotenansicht als Text (fuer Claude auf Wunsch mit Bild), `maus(urheber, argumente)` klickt,
 * tippt, zieht mit einer EIGENEN Maus der KI (nicht der des Architekten). Was die Maus am Graph
 * aendert, geht durch denselben Werkzeugsatz wie ein Werkzeugaufruf (`versucheCoop` im Stellvertreter
 * `kosmo-coop.ts`): Karte, Coop oder Voll; Loeschen und Rendern immer Karte. Die Sperrzonen stehen in
 * `kosmo-maus.ts` («Freigeben», «Alle freigeben», die direkt sendenden Bestell-Knoepfe, Loeschen,
 * Kennwoerter, Karten, Schalter, Rueckgaengig) und hier fuer die Teile, die es nur in Visbox gibt
 * (`WIRT_SPERRZONEN`). Die Namen der zwei Werkzeuge bildet die App wie alle (`blickMausWerkzeuge`).
 */
import { setzeVerlaufWache, useProject } from '../../kosmo-orbit/src/state/project-store';
import {
  behandle,
  kiSchnittstelle,
  kiSchritte,
  kiVerlaufWache,
  offeneVorschlaege,
  verwirfVorschlaege,
  werkzeugNameFuer,
  VIS_PAKET,
  type KiEreignis,
  type KiUrheber,
  type KiVorschlag,
} from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import {
  BLICK_PARAMETER,
  MAUS_PARAMETER,
  fuehreBlickAus,
  fuehreMausAus,
  registriereSperrzone,
  type WerkzeugAntwort,
} from '../../kosmo-orbit/src/state/kosmo-maus';
import { registriereAppName } from '../../kosmo-orbit/src/state/kosmo-name';
import { meldeProjektWechsel } from '../../kosmo-orbit/src/state/project-vault';
import { graphMappe } from './graph-sichern';
import { haengeVollAn, rufeMitVoll, type VollLage } from './voll-render';
import { haengeGrundlageAn, meldeGrundlageBefehlAn } from './grundlage-werkzeug';

// «Grundlage rendern» ist ein Vis-Befehl der Knotenansicht von Visbox (Entscheid 146) — angemeldet,
// sobald der Wirt geladen ist, damit die Werkzeugliste (auch die im Bau) ihn nennt.
meldeGrundlageBefehlAn();

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

// ---------------------------------------------------------------------------------- Blick und Maus

/** Der Name der App in den Saetzen der KosmoMaus («… in Visbox einschalten»). */
export const APP_NAME = 'Visbox';

/** Die Namen der zwei Werkzeuge — wie die App sie Claude nennt (`Mcp.servername` + «_blick»). */
export const BLICK_NAME = 'visbox_blick';
export const MAUS_NAME = 'visbox_maus';

export const BLICK_BESCHREIBUNG =
  'Sieht in die Knotenansicht von Visbox: Bereich, Dialoge, Meldungen, Fehler, Fokus, offene Karten, den Modus und die sichtbaren Bedienelemente mit testid und Rechteck; gesperrte stehen als solche da. Mit bild:true für Claude zusätzlich ein Bild (höchstens 1280 px). Ändert nichts. Braucht «Mitschauen».';
export const MAUS_BESCHREIBUNG =
  'Eine eigene Maus in der Knotenansicht (nicht die des Architekten); zuerst visbox_blick. Klick/tippen per testid oder Text trifft nur Sichtbares. Ändert ein Klick den Render-Graph, gilt der Modus: Karte, Coop oder Voll — Löschen und Rendern immer eine Karte. Nie: «Freigeben»/«Alle freigeben» (Grafikkarte), die Bestell-Knöpfe, Löschen, Karten, Schalter, Rückgängig, Kennwörter. Keine Dateien von der Platte. Braucht «Bedienen».';

/** Die zwei Werkzeuge in der Form der Werkzeugliste (`art`: lesen bzw. bedienen — nie selbst eine Karte). */
export function blickMausWerkzeuge(): { name: string; description: string; inputSchema: unknown; art: 'lesen' | 'bedienen' }[] {
  return [
    { name: BLICK_NAME, description: BLICK_BESCHREIBUNG, inputSchema: BLICK_PARAMETER, art: 'lesen' },
    { name: MAUS_NAME, description: MAUS_BESCHREIBUNG, inputSchema: MAUS_PARAMETER, art: 'bedienen' },
  ];
}

/** Der Urheber des Werkzeugsatzes zum Urheber der KosmoMaus («kosmo» traegt in Visbox den Namen «Assistent»). */
function mausUrheber(u: KiUrheber | undefined): 'claude' | 'kosmo' {
  return u === 'assistent' ? 'kosmo' : 'claude';
}

/**
 * Die Teile, die es nur in Visbox gibt und die eine KI nie bedient: der Schalter «Claude über MCP»,
 * die Anmeldung am Heim-PC, «Wer rechnet?», «Aktualisieren» und das Gespräch mit dem Assistenten.
 */
export const WIRT_SPERRZONEN: readonly { selektor: string; grund: string }[] = [
  { selektor: '[data-testid="einstellungen-claude-schalter"]', grund: '«Claude über MCP» schaltet nur der Architekt.' },
  { selektor: '[data-testid="einstellungen-heimpc-einrichten"], [data-testid="einstellungen-heimpc"]', grund: 'Die Anmeldung am Heim-PC richtet nur der Architekt ein.' },
  { selektor: '[data-testid="einstellungen-rechner"]', grund: '«Wer rechnet?» wählt nur der Architekt.' },
  { selektor: '[data-testid="einstellungen-aktualisieren"]', grund: 'Aktualisieren bleibt beim Architekten.' },
  { selektor: '.kp-panel', grund: 'Das Gespräch mit dem Assistenten führt der Architekt.' },
];

function pruefeWirtSperrzone(el: Element): string | null {
  for (const z of WIRT_SPERRZONEN) if (el.closest(z.selektor)) return z.grund;
  return null;
}

/**
 * Was die Maus am Graph ausloeste, als Satz an die KI: neue Karten (Kennung «M-…») und Schritte ohne
 * Karte. Die woertliche Antwort der KosmoMaus kennt nur ihre eigenen Maus-Karten — in Visbox gehen
 * Vis-Befehle durch den Werkzeugsatz, darum sagt es der Wirt.
 */
function folgenDerMaus(kartenVorher: Set<string>, schritteVorher: Set<string>): string {
  const karten = offeneVorschlaege().filter((v) => !kartenVorher.has(v.kennung));
  const schritte = kiSchritte().filter((s) => !schritteVorher.has(s.kennung));
  const teile: string[] = [];
  if (karten.length) {
    teile.push(
      `Die Handlung wollte den Render-Graph ändern — als Karte für den Architekten angehalten: ${karten
        .map((v) => `${v.kennung} «${v.zusammenfassung}»`)
        .join(', ')}. Erst «Anwenden» ändert ihn.`,
    );
  }
  if (schritte.length) {
    teile.push(`Ohne Karte angewendet (Coop/Voll, in der Leiste zurücknehmbar): ${schritte.map((s) => `«${s.zusammenfassung}»`).join(', ')}.`);
  }
  return teile.join(' ');
}

/** `visbox_blick`: das Lagebild, fuer Claude mit Bild auf Wunsch. Nur auf diesem Rechner. */
export async function blick(urheber: KiUrheber | undefined, argumente: unknown): Promise<WerkzeugAntwort> {
  return fuehreBlickAus(mausUrheber(urheber), argumente, 'lokal');
}

/** `visbox_maus`: eine Handlung der eigenen Maus; die Antwort nennt, was sie am Graph ausloeste. */
export async function maus(urheber: KiUrheber | undefined, argumente: unknown): Promise<WerkzeugAntwort> {
  const karten = new Set(offeneVorschlaege().map((v) => v.kennung));
  const schritte = new Set(kiSchritte().map((s) => s.kennung));
  const r = await fuehreMausAus(mausUrheber(urheber), argumente, 'lokal');
  const folgen = folgenDerMaus(karten, schritte);
  if (!folgen) return r;
  const [kopf, ...rest] = r.text.split('\n');
  return { ...r, text: [`${kopf} ${folgen}`, ...rest].join('\n') };
}

// ---------------------------------------------------------------------------------- Karten zurueck

/** Was `stelleWieder` je Karte sagt: liegt sie wieder, oder warum nicht (der Satz des Probelaufs). */
export interface Wiedergabe {
  kennung: string;
  liegt: boolean;
  text: string;
}

/** Ein Vorschlag, wie die App ihn zurueckgibt (die Form des Ereignisses «karte»), als Aufruf. */
function alsAufruf(v: KiVorschlag): { kennung: string; werkzeug: string; argumente: unknown; urheber: KiUrheber } {
  const urheber: KiUrheber = v.urheber === 'assistent' ? 'assistent' : 'claude';
  const schritte = Array.isArray(v.schritte) ? v.schritte : [];
  if (v.werkzeug === VIS_PAKET || schritte.length > 1) {
    return {
      kennung: v.kennung,
      werkzeug: VIS_PAKET,
      argumente: { schritte: schritte.map((s) => ({ befehl: werkzeugNameFuer(s.commandId), argumente: s.params ?? {} })) },
      urheber,
    };
  }
  const erster = schritte[0];
  return { kennung: v.kennung, werkzeug: erster ? werkzeugNameFuer(erster.commandId) : v.werkzeug, argumente: erster?.params ?? {}, urheber };
}

/**
 * Mac-Befund 0.3.33 (22.10.2026, Protokoll 74 §231): **eine Karte gehoert zur Mappe, in der sie
 * entstand.** Ohne Mappe am Mac kennt die App nur «am Heim-PC» — und der Heim-PC zeigt nach dem
 * Neuladen die Mappe, die zuletzt irgendein Geraet geoeffnet hat. So bekam die Knotenansicht von
 * «probe330» die Karte K-2 aus einer anderen Mappe zurueck. Darum traegt jede Karte, die der Wirt
 * der App meldet, die Kennung der Mappe ihres Graphen (`mappe`, aus `graphMappe`), und
 * `stelleWieder` nimmt eine Karte einer anderen Mappe nicht an: Die App weist «Anwenden» dann mit
 * dem Satz ab. Ohne Kennung (Mappe am Mac — dort unterscheidet die App die Mappen selbst) wie bisher.
 */
export function mappeDerKarte(v: unknown): string | null {
  const m = (v as { mappe?: unknown } | null)?.mappe;
  return typeof m === 'string' && m !== '' ? m : null;
}

/** Der Satz, wenn eine Karte zu einer anderen Mappe gehoert (in der Form des Probelaufs). */
export function andereMappeSatz(karte: string, offen: string): string {
  return `FEHLER: Der Vorschlag gehört zur Mappe «${karte}», offen ist «${offen}» — nichts wurde vorgeschlagen.`;
}

/**
 * Die offenen Karten von der Mac-App zurueck in den Werkzeugsatz (nach dem Neuladen). Jede geht
 * durch denselben Probelauf wie beim ersten Mal, **immer im Modus «karte»** — eine zurueckgegebene
 * Karte wird nie still angewendet. Liegt sie wieder, kommt das Ereignis «karte» wie sonst; scheitert
 * der Probelauf (der Graph passt nicht mehr), sagt die Antwort den Satz, und die App weist sie beim
 * Anwenden damit ab.
 */
export function stelleWieder(karten: unknown): Wiedergabe[] {
  if (!Array.isArray(karten)) return [];
  const antwort: Wiedergabe[] = [];
  for (const roh of karten) {
    const v = roh as KiVorschlag;
    if (!v || typeof v.kennung !== 'string' || typeof v.werkzeug !== 'string') continue;
    const karteMappe = mappeDerKarte(v);
    const offen = graphMappe();
    if (karteMappe && offen && karteMappe !== offen) {
      antwort.push({ kennung: v.kennung, liegt: false, text: andereMappeSatz(karteMappe, offen) });
      continue;
    }
    const r = behandle(alsAufruf(v), 'karte');
    antwort.push('karte' in r ? { kennung: v.kennung, liegt: true, text: r.karte.zusammenfassung } : { kennung: v.kennung, liegt: false, text: r.sofort.text });
  }
  return antwort;
}

export type VisboxKi = ReturnType<typeof baueVisboxKi>;

function baueVisboxKi() {
  const ki = kiSchnittstelle();
  return {
    werkzeuge: ki.werkzeuge,
    /** Entscheid 146: das Dritte ist die Lage der Vollautomatik vom Heim-PC (`null` ausser in «Voll»). */
    rufe: (aufruf: Parameters<typeof ki.rufe>[0], modus: Parameters<typeof ki.rufe>[1] = 'karte', voll?: VollLage | null) =>
      rufeMitVoll(aufruf, modus, voll, ki.rufe),
    entscheide: ki.entscheide,
    offene: ki.offene,
    verwirf: ki.verwirf,
    stelleWieder,
    rueckgaengigKi: ki.rueckgaengigKi,
    kiVerlauf: ki.kiVerlauf,
    blickMausWerkzeuge,
    blick,
    maus,
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
      // §231: eine Karte mit der Mappe ihres Graphen — sie kommt so mit `stelleWieder` zurueck.
      const mappe = graphMappe();
      const mitMappe = b.art === 'karte' && mappe ? { ...b, vorschlag: { ...b.vorschlag, mappe } } : b;
      // Als reiner JSON-Wert: WebKit wandelt ihn in ein Woerterbuch, ohne Funktionen und `undefined`.
      bote.postMessage(JSON.parse(alsText(mitMappe)));
    } catch (err) {
      console.error('[ki-wirt] Bote warf', err);
    }
  };
  const abEreignisse = ki.abonniere((e) => sende(e));
  setzeVerlaufWache(kiVerlaufWache);
  registriereAppName(APP_NAME);
  const abSperre = registriereSperrzone(pruefeWirtSperrzone);
  const abVoll = haengeVollAn();
  const abGrundlage = haengeGrundlageAn();
  let doc = useProject.getState().doc;
  const abDoc = useProject.subscribe((s) => {
    if (s.doc === doc) return;
    doc = s.doc;
    verwirfVorschlaege(MAPPE_GEWECHSELT);
    // Die Maus-Karten der KosmoMaus gehen mit (dort «Projekt gewechselt»).
    meldeProjektWechsel();
  });
  // DIE KARTEN BLEIBEN (Strang Karten): Die Seite sagt nur, dass sie geht — die App haelt die
  // Karten und gibt sie nach dem Neuladen zurueck. Nichts wird hier verworfen.
  const beimVerlassen = () => sende({ art: 'weg', grund: SEITE_LAEDT_NEU });
  fenster.addEventListener('pagehide', beimVerlassen);
  sende({ art: 'bereit', werkzeuge: schnitt.werkzeuge().length });
  return () => {
    abEreignisse();
    abSperre();
    abVoll();
    abGrundlage();
    registriereAppName(null);
    abDoc();
    fenster.removeEventListener('pagehide', beimVerlassen);
    setzeVerlaufWache(null);
    delete (fenster as unknown as { visboxKi?: VisboxKi }).visboxKi;
  };
}
