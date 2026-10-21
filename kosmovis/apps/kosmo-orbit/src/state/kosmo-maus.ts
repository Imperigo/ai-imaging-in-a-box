/**
 * KosmoMaus und KosmoBlick als Werkzeuge (Owner-Entscheid E157, 06.10.2026;
 * Anleitung `docs/CLAUDE-ANSCHLUSS.md` «Mitschauen und Bedienen»).
 *
 * Owner wörtlich: «bau dir selbst eine maus zum bedienen (KosmoMaus)» —
 * «freigabe für eine eigene bedienung nicht fernsteuerung meiner maus sondern
 * einer eigenen innerhalb der software die mich nicht tangiert (dito für die
 * llms von kosmo)».
 *
 * Zwei Werkzeuge, dieselben für Claude (MCP) und Kosmo (Chat):
 *  - `kosmo_blick` — Lagebild als Text, für Claude auf Wunsch mit Bild
 *    (`kosmo-blick-live.ts`). Braucht «Mitschauen».
 *  - `kosmo_maus` — klicken, schweben, tippen, Tasten, ziehen, Rad, Auswahl, Datei —
 *    alles als synthetische Ereignisse in der App (`kosmo-maus-ereignisse.ts`).
 *    Braucht «Bedienen».
 *
 * **Leitplanken (fest, nicht abschaltbar):**
 *  1. Ohne Freigabe nichts (`kosmo-maus-freigabe.ts`, Standard seit 07.10.2026:
 *     Mitschauen an, Bedienen an; ein ausgeschalteter Gerätewert bleibt aus).
 *     Esc oder «Stopp» schalten Bedienen sofort aus.
 *  2. Claude nur lokal: Aufrufe ohne `herkunft: 'lokal'` (z.B. über den
 *     Tunnel aus E156) werden abgelehnt (Owner-Antwort zu E157 «Nur lokal»).
 *  3. Projektänderungen weiter über Karten (E157): löst eine Handlung einen
 *     Befehl aus, hält die Befehls-Wache (`project-store.ts`) ihn an und legt
 *     eine Karte an; erst «Anwenden» des Architekten ändert das Projekt.
 *     Ausnahme Coop (E158, `kosmo-coop.ts`): ist der Coop für den Urheber an,
 *     wendet die Wache die Änderung direkt an, mit Urheber; gesperrte Befehle
 *     bleiben Karte. Die Sperrzonen (4.) gelten im Coop unverändert.
 *  4. Sperrzonen: die Freigabe-Schalter und die Leiste, Bestätigungsdialoge
 *     (darüber laufen Projekt löschen und andere endgültige Schritte),
 *     Veröffentlichen, Rückgängig/Wiederholen. Bestätigen und Zurücknehmen
 *     bleibt beim Menschen.
 *  5. Jede Handlung steht mit Urheber im Journal.
 */

import { beendeTaetigkeit } from './claude-taetigkeit';
import { execute, istLesenderBefehl, istLesenderLauf, type ExecutionResult } from '@kosmo/kernel';
import type { ReadTool } from '@kosmo/ai';
import { melde } from '@kosmo/ui';
import { legtGrundausstattungAn, merkeAngehalten, setzeBefehlsWache, setzeHandlungsFang, setzeSammelWache, useProject, wendePaketAn } from './project-store';
import { beiProjektWechsel } from './project-vault';
import { coopWendetGeradeAn, coopWirksam, useKosmoCoop, versucheCoop } from './kosmo-coop';
import { agentLage } from './agent-lage';
// Nur die zwei Konstanten (Adresse); kein Kreis zur Laufzeit, weil sie erst im Aufruf gelesen werden.
import { CLAUDE_ADRESSE_SCHLUESSEL, CLAUDE_STANDARD_ADRESSE, verwirfClaudeVorschlaege } from './claude-anschluss';
import {
  URHEBER_NAME,
  bedienZustandText,
  beendeEigenesBedienen,
  freigabe,
  legeVorschlagAn,
  nimmVorschlag,
  protokolliere,
  setzeZeiger,
  useKosmoMaus,
  verwirfMausVorschlaege,
  type Urheber,
} from './kosmo-maus-freigabe';
import {
  DURCHLAESSIG_ATTR,
  EIGENE_EBENE_ATTR,
  beschriftung,
  blickFehlerText,
  formatiereBlick,
  hoereAufFehler,
  istSichtbar,
  nimmBlickBild,
  sammleBlick,
  warteAufScrollRuhe,
} from './kosmo-blick-live';
import { dateiGeben, doppelklick, elementKennung, klick, klickMitPause, rad, rechtsklick, schweben, taste, tippen, waehlen, zerlegeTaste, ziehen, type Tasten } from './kosmo-maus-ereignisse';
import { istHarmloserFensterHinweis } from './harmlose-fensterhinweise';
import { leseDesktopDatei, pruefePfad } from './desktop-datei';
import { appName } from './kosmo-name';

export const BLICK_WERKZEUG = 'kosmo_blick';
export const MAUS_WERKZEUG = 'kosmo_maus';
export const KOSMO_MAUS_WERKZEUGE: readonly string[] = [BLICK_WERKZEUG, MAUS_WERKZEUG];

export const MAUS_AKTIONEN = [
  'klick',
  'doppelklick',
  'rechtsklick',
  'tippen',
  'taste',
  'ziehen',
  'rad',
  'waehlen',
  'datei',
  'schweben',
  'beenden',
] as const;
export type MausAktion = (typeof MAUS_AKTIONEN)[number];

/**
 * lw-kosmomaus-tasten (14.10.2026, Nachprobe R26): gehaltene Umschalter für
 * rad, klick, doppelklick, rechtsklick und ziehen. Der Grundriss zoomt nur mit
 * Strg+Rad (PlanView `radZoom`: `ctrlKey` hat Vorrang vor dem Schwenk, wie ein
 * Trackpad-Pinch in Chromium); Shift+Klick wählt mehrere.
 */
export const MAUS_TASTEN = ['ctrl', 'shift', 'alt', 'meta'] as const;
export type MausTaste = (typeof MAUS_TASTEN)[number];
const TASTE_FELD: Record<MausTaste, keyof Tasten> = { ctrl: 'ctrlKey', shift: 'shiftKey', alt: 'altKey', meta: 'metaKey' };
const TASTE_NAME: Record<MausTaste, string> = { ctrl: 'Strg', shift: 'Shift', alt: 'Alt', meta: 'Meta' };
const MIT_TASTEN: readonly MausAktion[] = ['rad', 'klick', 'doppelklick', 'rechtsklick', 'ziehen'];

export function tastenFelder(liste: readonly MausTaste[] | undefined): Tasten {
  const t: Tasten = {};
  for (const k of liste ?? []) t[TASTE_FELD[k]] = true;
  return t;
}

// ---------------------------------------------------------------------------
// Werkzeug-Beschreibungen (kurz: jedes Wort kostet Kosmo Kontextfenster)
// ---------------------------------------------------------------------------

const ZIEL_EIGENSCHAFTEN = {
  testid: { type: 'string', description: 'aus kosmo_blick (bevorzugt)' },
  text: { type: 'string', description: 'sichtbare Beschriftung' },
  x: { type: 'number', description: 'CSS-px von links' },
  y: { type: 'number', description: 'CSS-px von oben' },
} as const;

/** Dasselbe Ziel für `nach`, ohne die Feldbeschreibungen ein zweites Mal (Kontextfenster). */
const ZIEL_TYPEN = {
  testid: { type: 'string' },
  text: { type: 'string' },
  x: { type: 'number' },
  y: { type: 'number' },
} as const;

export const BLICK_PARAMETER = {
  type: 'object',
  properties: {
    bild: { type: 'boolean', description: 'zusätzlich ein Bild der App (nur Claude, max. 1280 px)' },
  },
  additionalProperties: false,
} as const;

export const MAUS_PARAMETER = {
  type: 'object',
  properties: {
    aktion: { type: 'string', enum: [...MAUS_AKTIONEN] },
    ...ZIEL_EIGENSCHAFTEN,
    nach: { type: 'object', properties: ZIEL_TYPEN, additionalProperties: false, description: 'ziehen: Ziel wie oben' },
    eingabe: { type: 'string', description: 'tippen: Text; taste: z.B. «Enter», «Control+a»; waehlen: Wert' },
    dx: { type: 'number' },
    dy: { type: 'number', description: 'rad: positiv = nach unten' },
    dauer_ms: { type: 'number', description: 'schweben (Hover, kein Klick): ms, Vorgabe 300, max. 3000' },
    tasten: { type: 'array', items: { enum: [...MAUS_TASTEN] } },
    pfad: { type: 'string', description: 'datei: absoluter Pfad im Heimordner (nur Desktop-App)' },
    pfade: {
      type: 'array',
      items: { type: 'string' },
      description: 'datei: mehrere Pfade in EINE Auswahl (Wolke + .verortung.json)',
    },
  },
  required: ['aktion'],
  additionalProperties: false,
} as const;

export const BLICK_BESCHREIBUNG =
  'Sieht in die laufende KosmoOrbit-App: Projekt, Bereich, Dialoge, Meldungen, Fehler, Fokus, Auswahl, offene Karten und die sichtbaren Bedienelemente mit testid und Rechteck. Ändert nichts. Braucht die Freigabe «Mitschauen».';

export const MAUS_BESCHREIBUNG =
  'Eigene Maus in der App (nicht die des Architekten); zuerst kosmo_blick. Klick/tippen per testid/text trifft nur Sichtbares; Hover-Menü: zuerst schweben. Projektänderungen: Karte oder direkt, je nach Modus (kosmo_blick, Zeile MODUS). Braucht «Bedienen».';

// ---------------------------------------------------------------------------
// Ziel finden, Sperrzonen
// ---------------------------------------------------------------------------

export interface MausZiel {
  testid?: string;
  text?: string;
  x?: number;
  y?: number;
}

export interface MausArgumente extends MausZiel {
  aktion: MausAktion;
  nach?: MausZiel;
  eingabe?: string;
  dx?: number;
  dy?: number;
  /** schweben: Verweildauer vor der Antwort (ms). */
  dauer_ms?: number;
  pfad?: string;
  /** kosmo-maus-3: mehrere Dateien in EINE Auswahl (Splat + `.verortung.json`). */
  pfade?: string[];
  /** lw-kosmomaus-tasten: gehaltene Umschalter (rad, klick, doppelklick, rechtsklick, ziehen). */
  tasten?: MausTaste[];
}

const INTERAKTIV_ZIEL =
  'button, a[href], input, select, textarea, summary, [role="button"], [role="tab"], [role="menuitem"], [role="option"], [role="checkbox"], [role="switch"], [role="radio"], [contenteditable="true"], [data-testid]';

function escapeAttr(s: string): string {
  return typeof CSS !== 'undefined' && typeof CSS.escape === 'function' ? CSS.escape(s) : s.replace(/["\\]/g, '\\$&');
}

function mitte(el: Element): { x: number; y: number } {
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

/** Bedienteile: in einem durchlässigen Teil (Figur) bleiben sie Ziel — und damit Sperrzone. */
const BEDIENTEIL =
  'button, a[href], input, select, textarea, summary, [role="button"], [role="switch"], [role="checkbox"], [role="menuitem"], [role="tab"], [contenteditable="true"]';

/** Ein Teil der eigenen Ebene, das nur zeigt (Körper, Schild, Spitze der Figur) — kein Bedienteil darin. */
export function istDurchlaessig(el: Element): boolean {
  return el.closest(`[${DURCHLAESSIG_ATTR}]`) !== null && el.closest(BEDIENTEIL) === null;
}

/**
 * Das Element, das an (x, y) den Klick bekommen soll (lw-maus-sperrzone-esc,
 * Gerätebefund v0.1.7): nach `taste Escape` verweigerte ein sofortiger
 * Doppel-/Rechtsklick auf die Planfläche mit «Freigabe-Schalter und die
 * Leiste …», der zweite Versuch ging. URSACHE: die Figur des Agenten selbst.
 * Die Taste ohne Ziel setzt sie auf die Mitte des Fokus (oft der Plan), sie
 * gleitet federnd dorthin, und Körper und Schild nehmen Zeigerereignisse
 * (fürs Aufklappen der Karte) — `elementFromPoint` traf also, solange sie
 * über dem Punkt stand oder durch ihn glitt, die eigene Ebene, und
 * `sperrGrund` verweigerte. Jetzt zählt, was UNTER der Figur liegt; die
 * Sperrzonen bleiben: Leiste, Schalter, Karten und jedes Bedienteil der Figur
 * («Stopp» der aufgeklappten Karte) sind weiter Ziel und damit gesperrt.
 */
export function elementAmPunkt(x: number, y: number): Element | null {
  if (typeof document.elementsFromPoint === 'function') {
    const stapel = document.elementsFromPoint(x, y);
    if (stapel.length) return stapel.find((el) => !istDurchlaessig(el)) ?? null;
  }
  if (typeof document.elementFromPoint !== 'function') return null;
  const oben = document.elementFromPoint(x, y);
  if (!oben || !istDurchlaessig(oben)) return oben;
  // Ohne `elementsFromPoint`: die Figuren für die eine Abfrage unberührbar machen.
  const figuren = [...document.querySelectorAll<HTMLElement>(`[${DURCHLAESSIG_ATTR}]`)];
  const teile = figuren.flatMap((f) => [f, ...f.querySelectorAll<HTMLElement>('*')]).filter((t) => !t.closest(BEDIENTEIL));
  const teileVorher = teile.map((t) => [t.style.getPropertyValue('pointer-events'), t.style.getPropertyPriority('pointer-events')] as const);
  try {
    for (const t of teile) t.style.setProperty('pointer-events', 'none', 'important');
    return document.elementFromPoint(x, y);
  } finally {
    teile.forEach((t, i) => {
      const [wert, prio] = teileVorher[i]!;
      if (wert) t.style.setProperty('pointer-events', wert, prio);
      else t.style.removeProperty('pointer-events');
    });
  }
}

/**
 * Findet das Ziel; wirft mit einem Satz, den das Modell versteht.
 * `dateiFeld`: für `datei` darf eine testid auch ein VERSTECKTES Dateifeld
 * meinen — die App versteckt jedes `<input type="file">` hinter einem Knopf
 * (`DateiWahlKnopf.tsx`, Insel-Splat), die testid sitzt aber am Feld.
 */
export function findeZiel(z: MausZiel, dateiFeld = false): { el: Element; p: { x: number; y: number }; wie: string } {
  if (z.testid) {
    const alle = [...document.querySelectorAll(`[data-testid="${escapeAttr(z.testid)}"]`)];
    const versteckt = dateiFeld ? alle.find((x) => x instanceof HTMLInputElement && x.type === 'file') : undefined;
    const el = alle.find(istSichtbar) ?? versteckt ?? null;
    if (!el) {
      throw new Error(
        alle.length
          ? `[${z.testid}] ist da, aber nicht sichtbar.`
          : `Kein Element mit testid «${z.testid}» — kosmo_blick zeigt, was es gibt.`,
      );
    }
    const p = typeof z.x === 'number' && typeof z.y === 'number' ? { x: z.x, y: z.y } : mitte(el);
    return { el, p, wie: `[${z.testid}]` };
  }
  if (z.text) {
    const gesucht = z.text.trim().toLowerCase();
    const kandidaten = [...document.querySelectorAll(INTERAKTIV_ZIEL)].filter(
      (el) => !el.closest(`[${EIGENE_EBENE_ATTR}]`) && istSichtbar(el),
    );
    const gleich = kandidaten.filter((el) => beschriftung(el).toLowerCase() === gesucht);
    const enthalten = kandidaten.filter((el) => beschriftung(el).toLowerCase().includes(gesucht));
    // Das innerste Element gewinnt (ein Knopf statt seines Rahmens mit testid).
    const wahl = (gleich.length ? gleich : enthalten).sort((a, b) => (a.contains(b) ? 1 : b.contains(a) ? -1 : 0));
    const el = wahl[0];
    if (!el) throw new Error(`Kein sichtbares Bedienelement mit der Beschriftung «${z.text}».`);
    return { el, p: mitte(el), wie: `«${z.text}»${wahl.length > 1 ? ` (${wahl.length} Treffer, erster genommen)` : ''}` };
  }
  if (typeof z.x === 'number' && typeof z.y === 'number') {
    const el = elementAmPunkt(z.x, z.y);
    if (!el) throw new Error(`Am Punkt ${z.x},${z.y} liegt nichts (Fenster ${window.innerWidth}×${window.innerHeight}).`);
    return { el, p: { x: z.x, y: z.y }, wie: `Punkt ${Math.round(z.x)},${Math.round(z.y)}` };
  }
  throw new Error('Ziel fehlt: testid, text oder x und y angeben.');
}

// ---------------------------------------------------------------------------
// datei: welches Dateifeld der Aufruf meint (kosmo-maus-2, Owner-Abnahme 07.10.)
// ---------------------------------------------------------------------------

/**
 * Owner-Abnahme 07.10.2026: `datei` auf [island-splat-laden] oder
 * [splat-volumen-input-wahl] landete beim DXF-Import («DXF unlesbar …
 * gefunden «ply»»). URSACHE: das Ziel war ein KNOPF, kein Dateifeld; also
 * gingen `dragenter/dragover/drop` an den Knopf, stiegen auf und trafen die
 * Ablage der ganzen Arbeitsfläche (`DesignWorkspace.tsx` `onDrop` →
 * `verarbeiteUnternehmerplanDatei`, also DXF). Das echte Feld liegt
 * versteckt daneben.
 *
 * Darum löst `datei` das Ziel zuerst auf das gemeinte `<input type="file">`
 * auf, in dieser Reihenfolge (ohne Nebenwirkung zuerst):
 *  1. das Ziel ist selbst ein Dateifeld;
 *  2. Muster von `DateiWahlKnopf`: testid «X-knopf», «X-wahl», «X-name» → Feld «X»;
 *  3. das Ziel enthält genau ein Dateifeld (z.B. der Rahmen «X-wahl»);
 *  4. im nächsten Rahmen (bis drei Ebenen hoch) liegt genau ein Dateifeld
 *     (Insel: Knopf und Feld nebeneinander);
 *  5. ein Knopf, der sein Feld per `feld.click()` öffnet: der Klick läuft,
 *     das Öffnen des Dialogs wird abgefangen und merkt sich das Feld.
 * Nur wenn das Ziel kein Knopf ist und kein Feld gefunden wird, gilt es als
 * Ablagefläche (Ziehen und Ablegen wie bisher).
 */
export type DateiZiel = { art: 'feld'; feld: HTMLInputElement; wie: string } | { art: 'ablage' };

const DATEI_RAHMEN_EBENEN = 3;

function istDateiFeld(el: Element | null | undefined): el is HTMLInputElement {
  return el instanceof HTMLInputElement && el.type === 'file';
}

function dateiFelderIn(el: Element): HTMLInputElement[] {
  return [...el.querySelectorAll('input[type="file"]')].filter(istDateiFeld);
}

function istKnopfArtig(el: Element): boolean {
  return Boolean(el.closest('button, [role="button"], a[href], label, summary'));
}

function feldName(feld: HTMLInputElement): string {
  const t = feld.getAttribute('data-testid');
  return t ? `[${t}]` : 'Dateifeld';
}

/** Läuft `f`; ruft dabei jemand `click()`/`showPicker()` an einem Dateifeld, öffnet sich kein Dialog — das Feld wird gemerkt. */
export function fangeDateiwahl(f: () => void): HTMLInputElement | null {
  const proto = HTMLInputElement.prototype as HTMLInputElement & { showPicker?: () => void };
  const klickAlt = proto.click;
  const pickerAlt = proto.showPicker;
  let gefangen: HTMLInputElement | null = null;
  proto.click = function (this: HTMLInputElement) {
    if (this.type === 'file') {
      gefangen ??= this;
      return;
    }
    return klickAlt.call(this);
  };
  if (pickerAlt) {
    proto.showPicker = function (this: HTMLInputElement) {
      if (this.type === 'file') {
        gefangen ??= this;
        return;
      }
      return pickerAlt.call(this);
    };
  }
  try {
    f();
  } finally {
    proto.click = klickAlt;
    if (pickerAlt) proto.showPicker = pickerAlt;
  }
  return gefangen;
}

/** Löst das Ziel von `datei` auf; wirft mit einem Satz, wenn ein Knopf kein Feld hat. */
export function findeDateiZiel(el: Element, wie: string, p: { x: number; y: number }): DateiZiel {
  if (istDateiFeld(el)) return { art: 'feld', feld: el, wie };
  const testid = el.closest('[data-testid]')?.getAttribute('data-testid') ?? '';
  const basis = /^(.+)-(knopf|wahl|name)$/.exec(testid)?.[1];
  if (basis) {
    const feld = [...document.querySelectorAll(`[data-testid="${escapeAttr(basis)}"]`)].find(istDateiFeld);
    if (feld) return { art: 'feld', feld, wie: `${wie} → ${feldName(feld)}` };
  }
  const innen = dateiFelderIn(el);
  if (innen.length === 1) return { art: 'feld', feld: innen[0]!, wie: `${wie} → ${feldName(innen[0]!)}` };
  let rahmen: Element | null = el.parentElement;
  for (let i = 0; rahmen && i < DATEI_RAHMEN_EBENEN; i++, rahmen = rahmen.parentElement) {
    const felder = dateiFelderIn(rahmen);
    if (felder.length === 1) return { art: 'feld', feld: felder[0]!, wie: `${wie} → ${feldName(felder[0]!)}` };
    if (felder.length > 1) break;
  }
  if (istKnopfArtig(el)) {
    const feld = fangeDateiwahl(() => klick(el, p));
    if (feld) return { art: 'feld', feld, wie: `${wie} → ${feldName(feld)}` };
    throw new Error(
      `${wie} ist ein Knopf ohne Dateifeld — nichts gegeben (sonst nähme die Ablage der Arbeitsfläche die Datei, z.B. als DXF). Nenne den Dateiwahl-Knopf oder die testid des Dateifelds.`,
    );
  }
  return { art: 'ablage' };
}

/** Karten, über die der Architekt Änderungen freigibt: Claude, Kosmo (Einzel/Paket), Governance. */
export const KARTEN_SELEKTOR =
  '[data-testid="claude-anschluss"], [data-testid="proposal-card"], [data-testid="paket-card"], .kp-freigabe-knoepfe, [data-testid="apply-proposal"], [data-testid="apply-paket"], [data-testid^="governance-immer"]';

/** Freigaben, mit denen Rechenzeit auf fremden Geraeten startet (Grafikkarte, Training). */
export const RECHEN_FREIGABE_SELEKTOR =
  '[data-testid="render-freigeben"], [data-testid="varianten-freigeben"], [data-testid="video-splat-freigeben"], [data-testid="train-freigabe-knopf"], [data-testid="train-freigabe-bestaetigen"]';

/**
 * KosmoVis-Kopf (Visbox Plan KI-Bedienung Stufe 6, 21.10.2026): Löschen im Vis-Werkzeug — das
 * Kreuz am Knoten und «Graph löschen» in der Insel. Über die Wache würde daraus zwar eine Karte;
 * gesperrt ist es trotzdem, damit eine Agenten-Hand nie in die Nähe kommt (Visbox-Entscheid 106c:
 * Löschen nur über Karte, die ein Mensch anwendet).
 */
export const LOESCHEN_SELEKTOR = '[data-testid="node-loeschen"], [data-testid="visisl-graph-loeschen"]';

/**
 * KosmoVis-Kopf (Visbox Stufe 6, 21.10.2026): die Knöpfe, die ein Bild DIREKT an die Brücke schicken
 * («Ausführen»/«Grundlage» am Render-Knoten, «Render senden» der Austausch-Insel, «N Bilder bestellen»
 * am Varianten-Knoten). Sie laufen nicht über einen Befehl, also an der Wache vorbei — und ohne
 * Freigabe-Pflicht rechnet die Grafikkarte sofort. Ein Agent bestellt ein Bild darum nur über
 * `vis_render`/`vis_varianten`, das immer eine Karte ist (Visbox-Entscheid 106b). Probe
 * `kv-maus-sperrzonen`: jede neue Stelle im Vis-Werkzeug, die direkt sendet, macht sie rot.
 */
export const RENDER_BESTELLEN_SELEKTOR =
  '[data-testid="render-ausfuehren"], [data-testid="render-grundlage"], [data-testid^="island-render-ausfuehren-"], [data-testid="varianten-bestellen"]';

/** Kennwort-Felder: ein Agent tippt nie ein Kennwort (Regel 3 der Visbox, Anmeldung am Heim-PC). */
export const KENNWORT_SELEKTOR = 'input[type="password"], [autocomplete="current-password"], [autocomplete="new-password"]';

/**
 * Alles, was die Sperrzonen sichtbar macht, solange ein Agent bedient (`kosmo-maus.css`,
 * `[data-kosmo-maus-bedient]`). Wortgleich zu den vier Selektoren oben (Probe `kv-maus-sperrzonen`).
 */
export const SPERRZONEN_SICHTBAR_SELEKTOR = `${RECHEN_FREIGABE_SELEKTOR}, ${RENDER_BESTELLEN_SELEKTOR}, ${LOESCHEN_SELEKTOR}, ${KENNWORT_SELEKTOR}`;

/**
 * Nahtstelle für einen Wirt (KosmoVis-Kopf, 21.10.2026): weitere Sperrzonen, die es nur dort gibt
 * (Visbox: die Anmeldung am Heim-PC, «Wer rechnet?», der Schalter «Claude über MCP»). Gefragt wird
 * NACH den festen Zonen; ohne Anmeldung ist alles wie vorher. Liefert das Abmelden.
 */
const weitereSperrzonen = new Set<(el: Element) => string | null>();
export function registriereSperrzone(pruefer: (el: Element) => string | null): () => void {
  weitereSperrzonen.add(pruefer);
  return () => void weitereSperrzonen.delete(pruefer);
}

const MUSTER_VEROEFFENTLICHEN = /ver(ö|oe)ffentlich|publizier|website-sync/i;
const MUSTER_ZURUECK = /r(ü|ue)ckg(ä|ae)ngig|wiederholen|\bundo\b|\bredo\b/i;

/** Warum ein Ziel gesperrt ist — oder `null`. */
export function sperrGrund(el: Element): string | null {
  if (el.closest(`[${EIGENE_EBENE_ATTR}]`)) return 'Freigabe-Schalter und die Leiste bedient nur der Architekt.';
  if (el.closest(KARTEN_SELEKTOR)) return 'Vorschlagskarten entscheidet nur der Architekt (Anwenden, Ablehnen, Immer erlauben).';
  if (el.closest(RECHEN_FREIGABE_SELEKTOR)) return 'Rechenfreigaben (Render, Varianten, Video-Splat, Training) gibt nur der Architekt.';
  if (el.closest(RENDER_BESTELLEN_SELEKTOR)) return 'Ein Bild bestellt eine KI nur über eine Karte (vis_render, vis_varianten) — dieser Knopf schickt direkt an die Grafikkarte.';
  if (el.closest(LOESCHEN_SELEKTOR)) return 'Löschen im Render-Graph bleibt beim Architekten (eine KI schlägt es über eine Karte vor).';
  if (el.closest(KENNWORT_SELEKTOR)) return 'Kennwörter gibt nur der Architekt ein.';
  const bestaetigung = el.closest('[data-testid="bestaetigung"]');
  if (bestaetigung && !el.closest('[data-testid="bestaetigung-nein"]')) {
    return 'Bestätigungen (z.B. Projekt löschen) gibt nur der Architekt. «Abbrechen» ist erlaubt.';
  }
  const kennung = `${el.closest('[data-testid]')?.getAttribute('data-testid') ?? ''} ${el.getAttribute('aria-label') ?? ''} ${beschriftung(el)}`;
  if (MUSTER_VEROEFFENTLICHEN.test(kennung)) return 'Veröffentlichen bleibt beim Architekten (E158).';
  if (MUSTER_ZURUECK.test(kennung)) return 'Rückgängig und Wiederholen bleiben beim Architekten.';
  if (/löschen|loeschen/i.test(el.getAttribute('aria-label') ?? '') && el.closest('.app-projekt-liste, [data-testid*="projekt"]')) {
    return 'Projekte löschen bleibt beim Architekten (E158).';
  }
  for (const pruefer of weitereSperrzonen) {
    const grund = pruefer(el);
    if (grund) return grund;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Trefferprobe: ein Klick per testid/text trifft nur, was obenauf liegt
// (lw-kosmomaus-testid-verdeckt, Integrator-Entscheid 14.10.2026)
// ---------------------------------------------------------------------------

/**
 * Befund aus lw-kosmomaus-schweben (§5): ein Klick per testid ging direkt ans
 * Element, auch wenn darüber etwas lag oder es (geschlossener Fächer,
 * zeigerdicht) gar nicht treffbar war. Eine echte Maus kann das nicht. Jetzt
 * prüfen `klick`, `doppelklick`, `rechtsklick` und `tippen` mit Ziel, was am
 * Prüfpunkt zuoberst liegt (`elementAmPunkt`, die eigene Figur bleibt
 * durchlässig):
 *  - Prüfpunkt = Mitte des sichtbaren Rechtecks (Schnitt mit dem Fenster);
 *  - liegt dort etwas anderes, sucht ein Raster im sichtbaren Rechteck einen
 *    Punkt, an dem das Ziel (oder ein Nachfahre) obenauf liegt — dort wird
 *    geklickt, wie ein Mensch an den freien Rand einer halb verdeckten Kachel;
 *  - kein solcher Punkt: abgelehnt, die Antwort nennt, was an der Mitte
 *    obenauf liegt (testid, Text, Rolle);
 *  - Sperrzonen wie beim Klick per Punkt: liegt am Treffpunkt ein gesperrtes
 *    Element (auch als Nachfahre des Ziels), wird verweigert.
 * Nennt der Aufruf testid UND x,y, zählt nur dieser Punkt. Ohne
 * `elementFromPoint` (jsdom) gibt es keine Probe, das Ziel gilt als getroffen.
 * Ein Ziel ausserhalb des Fensters gibt es hier nicht: `findeZiel` nimmt nur
 * sichtbare (`istSichtbar`, im Fenster) — gescrollt wurde nie und wird nicht.
 */
export const TREFFER_RASTER = 5;

export type Trefferprobe =
  | { art: 'frei'; p: { x: number; y: number } }
  | { art: 'verdeckt'; oben: Element }
  | { art: 'gesperrt'; grund: string; oben: Element }
  | { art: 'ungeprueft' };

function kannTreffpruefen(): boolean {
  return typeof document.elementsFromPoint === 'function' || typeof document.elementFromPoint === 'function';
}

/** Das sichtbare Rechteck des Elements: geschnitten mit dem Fenster. */
function sichtbaresRechteck(el: Element): { l: number; t: number; r: number; b: number } {
  const q = el.getBoundingClientRect();
  return { l: Math.max(q.left, 0), t: Math.max(q.top, 0), r: Math.min(q.right, window.innerWidth), b: Math.min(q.bottom, window.innerHeight) };
}

/** Probe an einem Punkt. `null` = dort liegt nichts (oder nur die eigene Figur). */
function probeAm(ziel: Element, p: { x: number; y: number }): Trefferprobe | null {
  const oben = elementAmPunkt(p.x, p.y);
  if (!oben) return null;
  if (oben !== ziel && !ziel.contains(oben)) return { art: 'verdeckt', oben };
  const grund = oben !== ziel ? sperrGrund(oben) : null;
  return grund ? { art: 'gesperrt', grund, oben } : { art: 'frei', p };
}

/** Wo ein Klick auf `ziel` wirklich landet (s. oben). `fest`: nur dieser Punkt. */
export function trefferprobe(ziel: Element, fest?: { x: number; y: number }): Trefferprobe {
  if (!kannTreffpruefen()) return { art: 'ungeprueft' };
  if (fest) return probeAm(ziel, fest) ?? { art: 'ungeprueft' };
  const s = sichtbaresRechteck(ziel);
  const erste = probeAm(ziel, { x: (s.l + s.r) / 2, y: (s.t + s.b) / 2 });
  if (!erste) return { art: 'ungeprueft' };
  if (erste.art !== 'verdeckt') return erste;
  // Halb verdeckt: ein freier Punkt im sichtbaren Rechteck (innere Rasterpunkte, nicht der Rand).
  for (let i = 1; i <= TREFFER_RASTER; i++) {
    for (let j = 1; j <= TREFFER_RASTER; j++) {
      const p = { x: s.l + ((s.r - s.l) * j) / (TREFFER_RASTER + 1), y: s.t + ((s.b - s.t) * i) / (TREFFER_RASTER + 1) };
      const probe = probeAm(ziel, p);
      if (probe && probe.art !== 'verdeckt') return probe;
    }
  }
  return erste;
}

const ROLLE_NACH_TAG: Record<string, string> = {
  button: 'button',
  a: 'link',
  select: 'combobox',
  textarea: 'textbox',
  img: 'img',
  dialog: 'dialog',
  canvas: 'Zeichenfläche',
  nav: 'navigation',
  li: 'listitem',
  ul: 'list',
};

function rolle(el: Element): string {
  const r = el.getAttribute('role');
  if (r) return r;
  if (el instanceof HTMLInputElement) return el.type === 'checkbox' || el.type === 'radio' ? el.type : 'textbox';
  return ROLLE_NACH_TAG[el.tagName.toLowerCase()] ?? el.tagName.toLowerCase();
}

/** Bedienteile und Rollen, deren Beschriftung etwas sagt (nicht `main` & Co. mit dem halben App-Text). */
const SPRECHEND = `${BEDIENTEIL}, [role="dialog"], [role="alertdialog"], [role="menu"], [role="listbox"], [role="option"], [role="tooltip"], [role="radio"], [role="slider"], [role="link"]`;

/** Nur der eigene Text (direkte Textknoten), ohne den der Kinder. */
function eigenerText(el: Element): string {
  return [...el.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent ?? '').join(' ').replace(/\s+/g, ' ').trim();
}

/** «[testid] «Text» (Rolle …)» — was obenauf liegt, für die Antwort. */
export function obenaufText(oben: Element): string {
  const bedien = oben.closest(SPRECHEND);
  const traeger = (bedien ?? oben).closest('[data-testid]');
  const kennung = traeger ? `[${traeger.getAttribute('data-testid')}]` : elementKennung(bedien ?? oben);
  const name = (bedien ? beschriftung(bedien) : (oben.getAttribute('aria-label') ?? eigenerText(oben))).slice(0, 40);
  return `${kennung}${name ? ` «${name}»` : ''} (Rolle ${rolle(bedien ?? oben)})`;
}

/** Tastenkombinationen, die nur der Mensch drückt. */
export function tastenSperre(kombination: string): string | null {
  const { key, tasten } = zerlegeTaste(kombination);
  if ((tasten.ctrlKey || tasten.metaKey) && /^[zy]$/i.test(key)) return 'Rückgängig und Wiederholen bleiben beim Architekten.';
  return null;
}

// ---------------------------------------------------------------------------
// Befehls-Wache: Projektänderungen werden zur Karte (E157)
// ---------------------------------------------------------------------------

let handelnder: Urheber | null = null;
let nachlaufBis = 0;
/** So lange nach einer Handlung gelten ausgelöste Befehle noch als ihre (späte Handler, Zeitgeber). */
export const NACHLAUF_MS = 400;

/**
 * lw-maus-rad-vollbild (c, Folge): `datei` mit einer Splat-Datei unter der
 * Wache — das Laden läuft weiter, nachdem die Handlung zurückkehrt, und
 * endet als Karte (`halteHandlungFest`). So lange wartet die Antwort auf die
 * Karte, um ihre Kennung zu nennen; danach sagt sie nur, dass eine kommt.
 */
export const SPLAT_KARTE_WARTEN_MS = 1500;
const SPLAT_ENDUNG = /\.(ply|splat)$|\.verortung\.json$/i;
export const SPLAT_LAEUFT_HINWEIS = 'Laden läuft — das Ergebnis kommt als Vorschlagskarte (erst «Anwenden» ändert das Projekt).';

async function warteAufNeueKarte(vorher: number, ms: number): Promise<boolean> {
  const bis = Date.now() + ms;
  while (useKosmoMaus.getState().vorschlaege.length <= vorher) {
    if (Date.now() >= bis) return false;
    await new Promise((r) => setTimeout(r, 50));
  }
  return true;
}

function handelnderJetzt(): Urheber | null {
  if (handelnder) return handelnder;
  return Date.now() < nachlaufBis ? zuletztHandelnder : null;
}
let zuletztHandelnder: Urheber | null = null;

/** Nur für Proben: der Nachlauf einer früheren Handlung gilt nicht mehr (sonst zählen Befehle danach noch als ihre). */
export function beendeNachlauf(): void {
  nachlaufBis = 0;
  zuletztHandelnder = null;
}

/** Läuft gerade ein «Anwenden» des Architekten? Dann nie abfangen (auch im Nachlauf). */
let architektWendetAn = false;

/**
 * Lesende Läufe, die die Wache ohne Karte durchliess (lw-lesend-wache,
 * 08.10.2026) — `fuehreMausAus` gibt deren Zusammenfassung an den Agenten
 * zurück, wie die Karten. Nur die letzten paar; älteres liest niemand mehr.
 */
const lesendeLaeufe: { urheber: Urheber; commandId: string; zusammenfassung: string; gekennzeichnet: boolean }[] = [];
let lesendeLaeufeGesamt = 0;

/**
 * Ein LESENDER Befehl hat nichts freizugeben: Kennzeichen `lesend: true` am
 * Befehl (`commands/core.ts`) ODER — Rückfall ohne Kennzeichen — der
 * Probelauf liefert keinen Patch. Dann läuft er sofort (die Wache gibt `null`
 * zurück, `runCommand` führt ihn normal aus). Ein Probelauf, der wirft, hält
 * nichts auf: der bisherige Weg (Karte bzw. Fehler) bleibt.
 */
function laesstLesendDurch(wer: Urheber, commandId: string, params: unknown): boolean {
  let probe: ExecutionResult;
  try {
    probe = execute(useProject.getState().doc, commandId, params, { actor: 'kosmo', dryRun: true });
  } catch {
    return false;
  }
  if (!istLesenderLauf(commandId, probe)) return false;
  // Zwei Fälle getrennt (Integrator 08.10.): «lesend» = Kennzeichen am Befehl;
  // «ohne Änderung» = Rückfall, ein Befehl OHNE Kennzeichen lief leer — so
  // sieht man später, welcher schreibende Befehl nichts tat.
  const gekennzeichnet = istLesenderBefehl(commandId);
  lesendeLaeufe.push({ urheber: wer, commandId, zusammenfassung: probe.summary, gekennzeichnet });
  if (lesendeLaeufe.length > 20) lesendeLaeufe.shift();
  lesendeLaeufeGesamt += 1;
  protokolliere({
    urheber: wer,
    werkzeug: 'maus',
    aktion: gekennzeichnet ? 'lesend' : 'ohne Änderung',
    ziel: commandId,
    ergebnis: 'ok',
    text: gekennzeichnet
      ? `Lesender Befehl ohne Karte ausgeführt: ${probe.summary}`
      : `Ohne Änderung (Befehl ohne Lesend-Kennzeichen, Probelauf 0 Patches), keine Karte: ${probe.summary}`,
  });
  return true;
}

/** Für welches Doc die feste Grundausstattung schon im Journal steht (eine Zeile je neuem Projekt). */
let grundausstattungGemeldet: object | null = null;

function wache(commandId: string, params: unknown): ExecutionResult | null {
  if (architektWendetAn || coopWendetGeradeAn()) return null;
  const wer = handelnderJetzt();
  if (!wer) return null;
  // kosmo-maus-2 (Integrator-Freigabe 08.10.2026): «Neues Projekt» mit der
  // FESTEN Grundausstattung (EG, 1.OG, AW Beton 36, IW Beton 18 —
  // `bootstrapProject`) ist EIN UI-Schritt, keine Karte. Nur diese Vorlage;
  // alles darüber (Parameter eines Modells) bleibt Karte. Owner-Abnahme
  // 07.10.: vorher wurden die vier zu m-1…m-4, das Projekt blieb leer.
  if (legtGrundausstattungAn()) {
    const doc = useProject.getState().doc;
    if (grundausstattungGemeldet !== doc) {
      grundausstattungGemeldet = doc;
      protokolliere({
        urheber: wer,
        werkzeug: 'maus',
        aktion: 'grundausstattung',
        ziel: 'neues Projekt',
        ergebnis: 'ok',
        text: 'Neues Projekt: feste Grundausstattung (EG, 1.OG, AW Beton 36, IW Beton 18) direkt angelegt — ein UI-Schritt, keine Karte.',
      });
    }
    return null;
  }
  // lw-lesend-wache: lesende Befehle laufen sofort, ohne Karte (nichts freizugeben).
  if (laesstLesendDurch(wer, commandId, params)) return null;
  // E158 Coop: frei, mit Urheber (`kosmo-coop.ts`); `null` = Coop aus oder gesperrt → Karte wie immer.
  const coop = versucheCoop(wer, commandId, params, 'maus');
  if (coop) return coop;
  // kosmo-maus-3: als angehalten markiert — `istAngehalten(r)` (project-store.ts)
  // sagt Aufrufern, dass das Projekt unverändert ist und die Kennungen nicht gibt.
  const probe = merkeAngehalten(execute(useProject.getState().doc, commandId, params, { actor: 'kosmo', dryRun: true }));
  const v = legeVorschlagAn({ urheber: wer, commandId, params, zusammenfassung: probe.summary });
  protokolliere({
    urheber: wer,
    werkzeug: 'maus',
    aktion: 'vorschlag',
    ziel: commandId,
    ergebnis: 'ok',
    text: `Projektänderung angehalten, wartet als Karte ${v.kennung}: ${probe.summary}`,
  });
  return probe;
}
setzeBefehlsWache(wache);

// lw-maus-rad-vollbild (c): lange Ladewege (Splat) halten den Handelnden fest
// (`halteHandlungFest`, project-store.ts) — sonst liefe ihr Schreibschritt
// nach dem Nachlauf als Handlung des Architekten, ohne Karte.
setzeHandlungsFang(() => {
  const wer = handelnderJetzt();
  if (!wer) return { agent: null, lauf: (fn) => fn() };
  return {
    agent: wer,
    lauf(fn) {
      const vorher = handelnder;
      handelnder = wer;
      try {
        return fn();
      } finally {
        handelnder = vorher;
      }
    },
  };
});

// Sammelweg (`alsEinVorschlag`, project-store.ts; Befund auf-272): EINE Karte
// für eine Handlung mit mehreren Befehlen. Hält an, wo die Wache einen
// Einzelbefehl anhielte; im Coop/der Vollautomatik nicht — dort läuft jeder
// Schritt wie bisher über `versucheCoop`.
setzeSammelWache({
  haeltAn() {
    if (architektWendetAn || coopWendetGeradeAn() || legtGrundausstattungAn()) return false;
    const wer = handelnderJetzt();
    return wer !== null && !coopWirksam(wer);
  },
  legePaketAn(titel, schritte) {
    const wer = handelnderJetzt();
    if (!wer) return;
    const aendernd = schritte.filter((s) => s.patchAnzahl > 0);
    const zusammenfassung = `${titel} — ${aendernd.length} Schritte als ein Paket: ${aendernd.map((s) => s.zusammenfassung).join(' · ')}`;
    const v = legeVorschlagAn({ urheber: wer, commandId: 'paket', params: null, zusammenfassung, schritte });
    protokolliere({
      urheber: wer,
      werkzeug: 'maus',
      aktion: 'vorschlag',
      ziel: `Paket (${schritte.length} Schritte)`,
      ergebnis: 'ok',
      text: `Projektänderung angehalten, wartet als EINE Karte ${v.kennung}: ${zusammenfassung}`,
    });
  },
});

/** «Anwenden» einer Maus-Karte: derselbe `runCommand`-Weg wie jede Kosmo-Karte. */
export function wendeMausVorschlagAn(kennung: string): string | null {
  const v = nimmVorschlag(kennung);
  if (!v) return null;
  architektWendetAn = true;
  let summary: string;
  try {
    if (v.schritte) {
      // Paket: atomar, EINE Rückgängig-Gruppe (`wendePaketAn`).
      wendePaketAn(v.schritte, { actor: 'kosmo' });
      summary = v.zusammenfassung;
    } else {
      summary = useProject.getState().runCommand(v.commandId, v.params, { actor: 'kosmo' }).summary;
    }
  } catch (e) {
    // Owner-Abnahme 07.10.: «Geschoss-Index 0 ist bereits vergeben» stieg als
    // ungefangener Fehler bis ans Fenster (Klick im Knopf). Jetzt: Meldung
    // und Journal, die Karte ist weg, das Projekt unverändert.
    const text = e instanceof Error ? e.message : String(e);
    protokolliere({ urheber: v.urheber, werkzeug: 'maus', aktion: 'angewendet', ziel: v.commandId, ergebnis: 'fehler', text });
    melde(`Karte ${v.kennung} liess sich nicht anwenden: ${text}`, { ton: 'fehler' });
    return null;
  } finally {
    architektWendetAn = false;
  }
  protokolliere({ urheber: v.urheber, werkzeug: 'maus', aktion: 'angewendet', ziel: v.commandId, ergebnis: 'ok', text: summary });
  return summary;
}

export function lehneMausVorschlagAb(kennung: string): boolean {
  const v = nimmVorschlag(kennung);
  if (!v) return false;
  protokolliere({ urheber: v.urheber, werkzeug: 'maus', aktion: 'abgelehnt', ziel: v.commandId, ergebnis: 'ok', text: v.zusammenfassung });
  return true;
}

// ---------------------------------------------------------------------------
// Ausführen
// ---------------------------------------------------------------------------

export interface WerkzeugAntwort {
  ok: boolean;
  text: string;
  bild?: { data: string; mimeType: string };
}

/** Woher ein Aufruf kommt. Kosmo läuft in der App selbst: immer lokal. */
export type Herkunft = 'lokal' | 'tunnel' | undefined;

function absage(urheber: Urheber, werkzeug: 'blick' | 'maus', aktion: string, text: string): WerkzeugAntwort {
  protokolliere({ urheber, werkzeug, aktion, ergebnis: 'verweigert', text });
  return { ok: false, text: `VERWEIGERT: ${text}` };
}

function pruefeHerkunft(urheber: Urheber, herkunft: Herkunft): string | null {
  if (urheber === 'kosmo') return null;
  return herkunft === 'lokal'
    ? null
    : 'Mitschauen und Bedienen gibt es nur auf diesem Rechner, nicht über den Weg aus dem Internet (Owner-Entscheid E157).';
}

function naechsterTakt(): Promise<void> {
  return new Promise((resolve) => {
    const t = setTimeout(resolve, 120); // im Hintergrund ruht der Bildtakt
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(() => requestAnimationFrame(() => {
        clearTimeout(t);
        resolve();
      }));
    }
  });
}

export async function fuehreBlickAus(urheber: Urheber, args: unknown, herkunft: Herkunft): Promise<WerkzeugAntwort> {
  hoereAufFehler();
  const nurLokal = pruefeHerkunft(urheber, herkunft);
  if (nurLokal) return absage(urheber, 'blick', 'lesen', nurLokal);
  if (!freigabe(urheber).mitschauen) {
    return absage(urheber, 'blick', 'lesen', `«Mitschauen» ist für ${URHEBER_NAME[urheber]} ausgeschaltet. Der Architekt kann es in ${appName()} einschalten.`);
  }
  // Bild und Liste aus demselben Moment: erst ein laufendes (weiches)
  // Scrollen abwarten, dann Liste und Scrollstand lesen; das Bild zeigt genau
  // diesen Scrollstand (kosmo-blick-live, 08.10.2026).
  const scrollStaende = await warteAufScrollRuhe();
  const lage = { ...sammleBlick(urheber), modus: agentLage(urheber) };
  let text = formatiereBlick(lage);
  const willBild = (args as { bild?: unknown } | null)?.bild === true;
  let bild: WerkzeugAntwort['bild'];
  if (willBild && urheber === 'claude') {
    try {
      const b = await nimmBlickBild(urheber, undefined, scrollStaende);
      bild = { data: b.data, mimeType: b.mimeType };
      text += `\nBILD: ${b.breite}×${b.hoehe} px, Massstab ${b.massstab.toFixed(3)} zu den CSS-Pixeln oben${b.geschwaerzt ? `, ${b.geschwaerzt} Normansicht(en) geschwärzt` : ''}.`;
    } catch (e) {
      text += `\nBILD: nicht möglich (${blickFehlerText(e)}).`;
    }
  } else if (willBild) {
    text += `\nBILD: für ${URHEBER_NAME[urheber]} hier nicht — dafür gibt es bild_ansehen.`;
  }
  protokolliere({
    urheber,
    werkzeug: 'blick',
    aktion: bild ? 'text+bild' : 'text',
    ergebnis: 'ok',
    text: `${lage.bereich}, ${lage.elemente.length} Bedienelemente${lage.normansichtenGeschwaerzt ? `, ${lage.normansichten.length} Normansicht(en) geschwärzt` : ''}`,
  });
  return { ok: true, text, ...(bild ? { bild } : {}) };
}

// lw-splat-context (08.10.2026): das Lesen steht seither in
// `desktop-datei.ts` — dieselbe Regel für KosmoMaus und die Desktop-Ablage,
// und dort wird der Pfad an der gebauten `File` gemerkt (`datei-pfade.ts`).
export { DATEI_TEIL_BYTES } from './desktop-datei';

/** Höchstens so viele Dateien je `datei` (eine Auswahl im Dateidialog ist selten grösser). */
export const DATEI_MAX_ANZAHL = 16;

function zahl(v: unknown): number | undefined {
  return typeof v === 'number' && Number.isFinite(v) ? v : undefined;
}

function zielAus(o: unknown): MausZiel {
  const r = (o && typeof o === 'object' ? o : {}) as Record<string, unknown>;
  return {
    ...(typeof r['testid'] === 'string' ? { testid: r['testid'] } : {}),
    ...(typeof r['text'] === 'string' ? { text: r['text'] } : {}),
    ...(zahl(r['x']) !== undefined ? { x: zahl(r['x'])! } : {}),
    ...(zahl(r['y']) !== undefined ? { y: zahl(r['y'])! } : {}),
  };
}

export function leseMausArgumente(args: unknown): MausArgumente {
  const r = (args && typeof args === 'object' ? args : {}) as Record<string, unknown>;
  const aktion = r['aktion'];
  if (typeof aktion !== 'string' || !(MAUS_AKTIONEN as readonly string[]).includes(aktion)) {
    throw new Error(`aktion fehlt oder ist unbekannt; erlaubt: ${MAUS_AKTIONEN.join(', ')}`);
  }
  return {
    aktion: aktion as MausAktion,
    ...zielAus(r),
    ...(r['nach'] ? { nach: zielAus(r['nach']) } : {}),
    ...(typeof r['eingabe'] === 'string' ? { eingabe: r['eingabe'] } : {}),
    ...(zahl(r['dx']) !== undefined ? { dx: zahl(r['dx'])! } : {}),
    ...(zahl(r['dy']) !== undefined ? { dy: zahl(r['dy'])! } : {}),
    ...(zahl(r['dauer_ms']) !== undefined ? { dauer_ms: zahl(r['dauer_ms'])! } : {}),
    ...(typeof r['pfad'] === 'string' ? { pfad: r['pfad'] } : {}),
    ...(r['pfade'] !== undefined ? { pfade: pfadeAus(r['pfade']) } : {}),
    ...(r['tasten'] !== undefined ? { tasten: tastenAus(r['tasten']) } : {}),
  };
}

function tastenAus(v: unknown): MausTaste[] {
  if (!Array.isArray(v) || v.some((k) => !(MAUS_TASTEN as readonly unknown[]).includes(k))) {
    throw new Error(`tasten muss eine Liste aus ${MAUS_TASTEN.join(', ')} sein.`);
  }
  return [...new Set(v as MausTaste[])];
}

function pfadeAus(v: unknown): string[] {
  if (!Array.isArray(v) || v.some((p) => typeof p !== 'string')) throw new Error('pfade muss eine Liste von Pfaden (Text) sein.');
  return v as string[];
}

/** Welche Pfade `datei` meint: `pfad` ODER `pfade`, geprüft, bevor irgendetwas gelesen wird. */
function dateiPfade(a: MausArgumente): string[] {
  if (a.pfad !== undefined && a.pfade !== undefined) throw new Error('Entweder pfad oder pfade angeben, nicht beides.');
  const liste = a.pfade ?? (a.pfad !== undefined ? [a.pfad] : []);
  if (liste.length === 0) throw new Error('pfad fehlt (oder pfade).');
  if (liste.length > DATEI_MAX_ANZAHL) throw new Error(`Höchstens ${DATEI_MAX_ANZAHL} Dateien auf einmal.`);
  for (const p of liste) pruefePfad(p);
  return liste;
}

function dateienText(dateien: File[]): string {
  const je = dateien.map((d) => `«${d.name}» (${d.size} Bytes)`).join(', ');
  return dateien.length === 1 ? `Datei ${je}` : `${dateien.length} Dateien ${je}`;
}

function hatZiel(a: MausZiel): boolean {
  return Boolean(a.testid || a.text || (a.x !== undefined && a.y !== undefined));
}

// Seit Runde 13 (Integrator) in `harmlose-fensterhinweise.ts`, damit auch
// der Fehlermeldeweg (`fehlerberichte.ts`) denselben Filter liest.
export { istHarmloserFensterHinweis };

// ---------------------------------------------------------------------------
// schweben (lw-kosmomaus-schweben, 14.10.2026)
// ---------------------------------------------------------------------------

export const SCHWEBEN_VORGABE_MS = 300;
export const SCHWEBEN_MAX_MS = 3000;

export function schwebeDauer(ms: number | undefined): number {
  if (ms === undefined) return SCHWEBEN_VORGABE_MS;
  return Math.round(Math.max(0, Math.min(SCHWEBEN_MAX_MS, ms)));
}

/** Was als «offen» gilt: aufgeklappte Knöpfe, offene Fächer/Menüs, Kurzhilfen. */
const OFFEN_SELEKTOR = '[aria-expanded="true"], [data-testid].offen, [role="menu"], [role="listbox"], [role="tooltip"]';

function offeneTeile(): Set<Element> {
  return new Set([...document.querySelectorAll(OFFEN_SELEKTOR)].filter((el) => !el.closest(`[${EIGENE_EBENE_ATTR}]`) && istSichtbar(el)));
}

/** «geöffnet: … · geschlossen: …» — was das Schweben auf- bzw. zugeklappt hat. */
function offenWechsel(vorher: Set<Element>, nachher: Set<Element>): string {
  const auf = [...nachher].filter((el) => !vorher.has(el)).map(elementKennung);
  const zu = [...vorher].filter((el) => !nachher.has(el) && el.isConnected).map(elementKennung);
  const teile = [auf.length ? `geöffnet ${[...new Set(auf)].join(', ')}` : '', zu.length ? `geschlossen ${[...new Set(zu)].join(', ')}` : ''];
  return teile.filter(Boolean).join('; ') || 'nichts auf- oder zugeklappt';
}

/** Kennung und Beschriftung des Elements am Punkt, für die Antwort. */
function amPunktText(p: { x: number; y: number }, rueckfall: Element): string {
  const el = elementAmPunkt(p.x, p.y) ?? rueckfall;
  const mitKennung = el.closest('[data-testid]') ?? el;
  const name = beschriftung(mitKennung).slice(0, 40);
  return `${elementKennung(mitKennung)}${name ? ` «${name}»` : ''}`;
}

/**
 * Bonus (Fund «JETZT nennt nach Klick aufs Logo noch den alten Bereich»):
 * der Klick aufs Logo startet den Rückzug der Station (`station-uebergang.ts`,
 * Klasse `app-zieht-zurueck`); erst nach der Bewegung (höchstens 600 ms) steht
 * die Zentrale. So lange wartet die Antwort, bevor sie den Bereich liest.
 */
export const STATIONSWECHSEL_WARTEN_MS = 900;
async function warteAufStationsRueckzug(): Promise<void> {
  const bis = Date.now() + STATIONSWECHSEL_WARTEN_MS;
  while (document.querySelector('.app-zieht-zurueck') && Date.now() < bis) {
    await new Promise((r) => setTimeout(r, 50));
  }
}

export async function fuehreMausAus(urheber: Urheber, args: unknown, herkunft: Herkunft): Promise<WerkzeugAntwort> {
  const nurLokal = pruefeHerkunft(urheber, herkunft);
  if (nurLokal) return absage(urheber, 'maus', 'bedienen', nurLokal);
  if (!freigabe(urheber).bedienen) {
    return absage(
      urheber,
      'maus',
      'bedienen',
      // Runde 34 (Nr. 73–77): Grund und Zeit statt «Esc beendet es jederzeit» —
      // Claude las daraus, sein eigenes `taste Escape` habe es beendet (das
      // kann es nicht: ein synthetisches Esc beendet nie, `istStoppTaste`).
      `«Bedienen» ist für ${URHEBER_NAME[urheber]} ausgeschaltet. ${bedienZustandText(urheber)}.`,
    );
  }
  let a: MausArgumente;
  try {
    a = leseMausArgumente(args);
  } catch (e) {
    return { ok: false, text: `FEHLER: ${e instanceof Error ? e.message : String(e)}` };
  }
  // Owner-Entscheid 20.10.2026: der Agent beendet sein eigenes Bedienen (nie einschalten).
  if (a.aktion === 'beenden') {
    beendeEigenesBedienen(urheber);
    return { ok: true, text: 'Bedienen beendet. Wieder einschalten kann nur der Architekt.' };
  }
  const vorher = useKosmoMaus.getState().vorschlaege.length;
  const coopLetzte = useKosmoCoop.getState().gruppen.at(-1);
  const lesendVorher = lesendeLaeufeGesamt;
  let ergebnis: string;
  let zielText = '';
  const tasten = a.tasten?.length && MIT_TASTEN.includes(a.aktion) ? a.tasten : [];
  const gehalten = tastenFelder(tasten);
  // «mit Strg+Shift», an jede Antwort mit Tasten angehängt.
  const mit = tasten.length ? ` mit ${tasten.map((k) => TASTE_NAME[k]).join('+')}` : '';
  // (c, Folge): eine Splat-Datei unter der Wache (kein Coop) — Karte abwarten bzw. ankündigen.
  let splatUnterWache = false;
  // kosmo-maus-3: wirft ein Handler der App während der Handlung (z.B.
  // CommandError «Geschoss-Index 1 ist bereits vergeben» aus `runCommand`),
  // meldet React das nur ans Fenster — die Handlung hiess dann «OK». Jetzt
  // erfährt der Agent es, und es steht im Journal und als Meldung.
  const handlerFehler: string[] = [];
  const hoereFehler = (ev: ErrorEvent) => {
    // kosmo-maus-4 (Geräteprobe 1745, Befund 3): der harmlose Browser-Hinweis
    // «ResizeObserver loop …» ist kein Fehler der Handlung.
    if (istHarmloserFensterHinweis(ev)) return;
    const f: unknown = ev.error;
    handlerFehler.push(f instanceof Error ? `${f.name === 'Error' ? '' : `${f.name}: `}${f.message}` : ev.message || String(f));
  };
  try {
    // Ziel: bei tippen/taste ohne Ziel das fokussierte Element.
    const ohneZiel = (a.aktion === 'tippen' || a.aktion === 'taste') && !hatZiel(a);
    const fokus = document.activeElement && document.activeElement !== document.body ? document.activeElement : document.body;
    let z = ohneZiel
      ? { el: fokus, p: istSichtbar(fokus) ? mitte(fokus) : { x: 0, y: 0 }, wie: 'Fokus' }
      : findeZiel(a, a.aktion === 'datei');
    zielText = z.wie;
    const gesperrt = sperrGrund(z.el);
    if (gesperrt) return absage(urheber, 'maus', a.aktion, `${gesperrt} Ziel: ${z.wie}.`);
    // lw-kosmomaus-testid-verdeckt: ein Klick per testid/text trifft nur, was obenauf liegt
    // (per Punkt nimmt `findeZiel` ohnehin das oberste Element).
    const klickt = a.aktion === 'klick' || a.aktion === 'doppelklick' || a.aktion === 'rechtsklick' || (a.aktion === 'tippen' && !ohneZiel);
    if (klickt && (a.testid || a.text)) {
      const fest = a.testid && typeof a.x === 'number' && typeof a.y === 'number' ? z.p : undefined;
      const t = trefferprobe(z.el, fest);
      if (t.art === 'gesperrt') return absage(urheber, 'maus', a.aktion, `${t.grund} Am Punkt von ${z.wie} liegt ${obenaufText(t.oben)}.`);
      if (t.art === 'verdeckt') {
        return absage(
          urheber,
          'maus',
          a.aktion,
          `${z.wie} ist verdeckt durch ${obenaufText(t.oben)} — eine echte Maus träfe das auch nicht. Erst öffnen, was darüber liegt (z.B. schweben über die Kugel, deren Fächer es trägt), dann klicken.`,
        );
      }
      if (t.art === 'frei') z = { ...z, p: t.p };
    }
    // schweben: wie eine echte Maus trifft der Zeiger, was am Punkt zuoberst liegt —
    // auch das darf keine Sperrzone sein (eine Karte über dem Ziel, die Leiste …).
    const schwebeEl = a.aktion === 'schweben' ? (elementAmPunkt(z.p.x, z.p.y) ?? z.el) : null;
    if (schwebeEl && schwebeEl !== z.el) {
      const darueber = sperrGrund(schwebeEl);
      if (darueber) return absage(urheber, 'maus', a.aktion, `${darueber} Am Punkt von ${z.wie} liegt ${elementKennung(schwebeEl)}.`);
    }
    if (a.aktion === 'taste') {
      const ts = tastenSperre(a.eingabe ?? '');
      if (ts) return absage(urheber, 'maus', a.aktion, ts);
    }
    setzeZeiger(urheber, z.p.x, z.p.y);
    window.addEventListener('error', hoereFehler);
    handelnder = urheber;
    zuletztHandelnder = urheber;
    try {
      switch (a.aktion) {
        case 'klick':
          await klickMitPause(z.el, z.p, gehalten);
          ergebnis = `geklickt auf ${z.wie}${mit}`;
          break;
        case 'doppelklick':
          await doppelklick(z.el, z.p, gehalten);
          ergebnis = `doppelt geklickt auf ${z.wie}${mit}`;
          break;
        case 'rechtsklick':
          await rechtsklick(z.el, z.p, gehalten);
          ergebnis = `rechts geklickt auf ${z.wie}${mit}`;
          break;
        case 'tippen':
          if (!a.eingabe) throw new Error('eingabe fehlt (der Text).');
          if (ohneZiel) tippen(z.el, a.eingabe);
          else {
            await klickMitPause(z.el, z.p);
            tippen(document.activeElement && z.el.contains(document.activeElement) ? document.activeElement : z.el, a.eingabe);
          }
          ergebnis = `getippt in ${z.wie}: «${a.eingabe.length > 40 ? `${a.eingabe.slice(0, 40)}…` : a.eingabe}»`;
          break;
        case 'taste':
          if (!a.eingabe) throw new Error('eingabe fehlt (z.B. «Enter»).');
          taste(z.el, a.eingabe);
          ergebnis = `Taste ${a.eingabe} an ${z.wie}`;
          break;
        case 'waehlen':
          if (!a.eingabe) throw new Error('eingabe fehlt (der Wert).');
          ergebnis = `gewählt in ${z.wie}: «${await waehlen(z.el, a.eingabe)}»`;
          break;
        case 'rad': {
          const r = rad(z.el, z.p, a.dx ?? 0, a.dy ?? 0, gehalten);
          const wo =
            r.art === 'app'
              ? 'von der App selbst behandelt (z.B. Zoom), nicht gescrollt'
              : r.art === 'nichts'
                ? 'nichts gescrollt (kein scrollbarer Bereich in diese Richtung)'
                : `gescrollt ${r.kennung}` +
                  (r.vorher.y !== r.nachher.y ? ` senkrecht ${r.vorher.y}→${r.nachher.y}` : '') +
                  (r.vorher.x !== r.nachher.x ? ` waagrecht ${r.vorher.x}→${r.nachher.x}` : '');
          ergebnis = `Rad${mit} an ${z.wie}: dx ${a.dx ?? 0}, dy ${a.dy ?? 0} — ${wo}`;
          break;
        }
        case 'ziehen': {
          if (!a.nach || !hatZiel(a.nach)) throw new Error('nach fehlt (Ziel des Ziehens).');
          const n = findeZiel(a.nach);
          await ziehen(z.el, z.p, n.p, gehalten);
          setzeZeiger(urheber, n.p.x, n.p.y);
          ergebnis = `gezogen von ${z.wie} nach ${n.wie}${mit}`;
          break;
        }
        case 'schweben': {
          const el = schwebeEl ?? z.el;
          const vorherOffen = offeneTeile();
          schweben(el, z.p);
          await new Promise((r) => setTimeout(r, schwebeDauer(a.dauer_ms)));
          await naechsterTakt();
          const verdeckt = el !== z.el && !z.el.contains(el) ? ` (verdeckt: der Zeiger trifft ${elementKennung(el)})` : '';
          ergebnis = `geschwebt über ${z.wie}${verdeckt}; am Punkt jetzt ${amPunktText(z.p, el)}; ${offenWechsel(vorherOffen, offeneTeile())}`;
          break;
        }
        case 'datei': {
          const pfade = dateiPfade(a);
          // Erst das Ziel, dann lesen: eine 750-MB-Wolke wird nicht gelesen, wenn das Ziel nicht passt.
          const ziel = findeDateiZiel(z.el, z.wie, z.p);
          if (ziel.art === 'feld') {
            const feldGesperrt = sperrGrund(ziel.feld);
            if (feldGesperrt) throw new Error(`${feldGesperrt} Ziel: ${ziel.wie}.`);
          }
          // kosmo-maus-3 (Geräteprobe 575, Befund 5): der Splat-Lader liest die
          // `.verortung.json` nur in DERSELBEN Auswahl wie die Wolke
          // (`island-splat-input multiple`). Mehrere Dateien darum nur an ein
          // Feld mit `multiple` — sonst nähme es still nur die erste.
          if (pfade.length > 1) {
            if (ziel.art !== 'feld') {
              throw new Error(`${z.wie} ist eine Ablagefläche; mehrere Dateien gehen nur an ein Dateifeld, das mehrere nimmt. Nichts gegeben.`);
            }
            if (!ziel.feld.multiple) {
              throw new Error(`${ziel.wie} nimmt nur eine Datei (kein «multiple»); ${pfade.length} genannt — nichts gegeben. Gib die Dateien einzeln.`);
            }
          }
          // Nacheinander gelesen: jede Datei für sich mit allen Leitplanken (Heimordner, gewöhnliche Datei, Log je Datei, Teile).
          const dateien: File[] = [];
          for (const pfad of pfade) dateien.push(await leseDesktopDatei(pfad));
          splatUnterWache = dateien.some((d) => SPLAT_ENDUNG.test(d.name)) && !coopWirksam(urheber);
          if (ziel.art === 'feld') {
            dateiGeben(ziel.feld, dateien, z.p);
            ergebnis = `${dateienText(dateien)} ins Dateifeld ${ziel.wie} gegeben`;
          } else {
            dateiGeben(z.el, dateien, z.p);
            ergebnis = `${dateienText(dateien)} auf die Ablage ${z.wie} gegeben`;
          }
          break;
        }
      }
    } finally {
      handelnder = null;
      nachlaufBis = Date.now() + NACHLAUF_MS;
    }
    await naechsterTakt();
    await warteAufStationsRueckzug();
    if (splatUnterWache && !(await warteAufNeueKarte(vorher, SPLAT_KARTE_WARTEN_MS))) {
      ergebnis = `${ergebnis!}. ${SPLAT_LAEUFT_HINWEIS.replace(/\.$/, '')}`;
    }
    window.removeEventListener('error', hoereFehler);
    if (handlerFehler.length) {
      const text = `${ergebnis!} — dabei meldete die App einen Fehler: ${handlerFehler.join(' | ')}`;
      melde(`${URHEBER_NAME[urheber]}: ${text}`, { ton: 'fehler' });
      throw new Error(text);
    }
  } catch (e) {
    window.removeEventListener('error', hoereFehler);
    const text = e instanceof Error ? e.message : String(e);
    protokolliere({ urheber, werkzeug: 'maus', aktion: a.aktion, ziel: zielText, ergebnis: 'fehler', text });
    return { ok: false, text: `FEHLER: ${text}` };
  }
  const neu = useKosmoMaus.getState().vorschlaege.slice(vorher);
  protokolliere({ urheber, werkzeug: 'maus', aktion: a.aktion, ziel: zielText, ergebnis: 'ok', text: ergebnis });
  const lage = sammleBlick(urheber);
  const danach = [
    `JETZT: ${lage.bereich}`,
    lage.dialoge.length ? `Dialoge: ${lage.dialoge.join(' | ')}` : '',
    lage.meldungen.length ? `Meldungen: ${lage.meldungen.map((m) => `${m.ton}: ${m.text}`).join(' | ')}` : '',
  ]
    .filter(Boolean)
    .join('; ');
  const karten = neu.length
    ? ` Die Handlung wollte das Projekt ändern — als Karte für den Architekten angehalten: ${neu.map((v) => `${v.kennung} «${v.zusammenfassung}»`).join(', ')}. Erst «Anwenden» ändert das Projekt.`
    : '';
  // E158: was im Coop direkt geändert wurde, steht im Journal dieses Aufrufs.
  const gruppen = useKosmoCoop.getState().gruppen;
  const coopNeu = gruppen
    .slice(coopLetzte ? gruppen.indexOf(coopLetzte) + 1 : 0)
    .filter((g) => g.urheber === urheber && g.weg === 'maus');
  const coopText = coopNeu.length
    ? ` Im Coop direkt angewendet (ohne Karte, Urheber ${URHEBER_NAME[urheber]}): ${coopNeu.map((g) => `«${g.zusammenfassung}»`).join(', ')}.`
    : '';
  const lesendNeu = lesendeLaeufe
    .slice(Math.max(0, lesendeLaeufe.length - (lesendeLaeufeGesamt - lesendVorher)))
    .filter((l) => l.urheber === urheber);
  const liste = (ls: typeof lesendNeu) => ls.map((l) => `${l.commandId}: «${l.zusammenfassung}»`).join(', ');
  const gekennzeichnete = lesendNeu.filter((l) => l.gekennzeichnet);
  const leere = lesendNeu.filter((l) => !l.gekennzeichnet);
  const lesendText =
    (gekennzeichnete.length ? ` Lesend ausgeführt (ohne Karte, das Projekt ist unverändert): ${liste(gekennzeichnete)}.` : '') +
    (leere.length ? ` Ohne Änderung gelaufen (kein Lesend-Kennzeichen, 0 Patches, keine Karte): ${liste(leere)}.` : '');
  return { ok: true, text: `OK: ${ergebnis}.${karten}${coopText}${lesendText}\n${danach}` };
}

// ---------------------------------------------------------------------------
// Anschluss Claude (MCP) — ein Aufruf, eine Zeile in claude-anschluss.ts
// ---------------------------------------------------------------------------

/** Die Liste, die Claude zusätzlich sieht (Form wie `ClaudeWerkzeug`). */
export function kosmoMausWerkzeugeFuerClaude(): { name: string; description: string; inputSchema: unknown }[] {
  return [
    { name: BLICK_WERKZEUG, description: BLICK_BESCHREIBUNG, inputSchema: BLICK_PARAMETER },
    { name: MAUS_WERKZEUG, description: MAUS_BESCHREIBUNG, inputSchema: MAUS_PARAMETER },
  ];
}

export function istKosmoMausAufruf(aufruf: { werkzeug: string }): boolean {
  return KOSMO_MAUS_WERKZEUGE.includes(aufruf.werkzeug);
}

/** Einen MCP-Aufruf von Claude ausführen. Die Antwort trägt optional ein Bild (kern.mjs reicht es weiter). */
export async function fuehreKosmoMausAufrufFuerClaude(aufruf: {
  kennung: string;
  werkzeug: string;
  argumente: unknown;
  herkunft?: string;
}): Promise<{ kennung: string; ok: boolean; text: string; bild?: { data: string; mimeType: string } }> {
  const herkunft: Herkunft = aufruf.herkunft === 'lokal' ? 'lokal' : aufruf.herkunft === 'tunnel' ? 'tunnel' : undefined;
  const r =
    aufruf.werkzeug === BLICK_WERKZEUG
      ? await fuehreBlickAus('claude', aufruf.argumente, herkunft)
      : await fuehreMausAus('claude', aufruf.argumente, herkunft);
  return { kennung: aufruf.kennung, ...r };
}

/** Aufrufe, die gerade laufen — der Server reicht offene Aufrufe nach jedem
 *  Neuverbinden noch einmal (lw-claude-karten); eine Maus-Handlung darf dabei
 *  nicht zweimal laufen. */
const laufend = new Set<string>();

/** Wohin die Antwort geht: wie `ClaudeAnschluss.tsx` (`leseAdresse`). */
let antwortWeg: ((antwort: object) => void) | null = null;

/**
 * Für I7a (Anschluss in Rust, Tauri-Ereignisse): dort meldet der neue
 * Anschluss hier seinen Antwortweg an. Ohne Anmeldung gilt der heutige Weg
 * über `POST <adresse>/app/antwort`.
 */
export function setzeKosmoMausAntwortWeg(f: ((antwort: object) => void) | null): void {
  antwortWeg = f;
}

function sendeAntwort(antwort: object): void {
  if (antwortWeg) {
    antwortWeg(antwort);
    return;
  }
  beendeTaetigkeit(antwort as { kennung: string; ok: boolean; text: string }); // R37 L1-7 (der Desktop-Weg trägt es in `antworte`)
  let adresse = CLAUDE_STANDARD_ADRESSE;
  try {
    adresse = localStorage.getItem(CLAUDE_ADRESSE_SCHLUESSEL) || CLAUDE_STANDARD_ADRESSE;
  } catch {
    /* Standard */
  }
  void fetch(`${adresse}/app/antwort`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(antwort),
  }).catch(() => undefined);
}

/**
 * Einhängepunkt für den heutigen, synchronen `behandleClaudeAufruf`: startet
 * die Handlung, liefert `null` («Antwort kommt später») und schickt die
 * Antwort selbst, sobald sie da ist. Nach I7b reicht stattdessen
 * `fuehreKosmoMausAufrufFuerClaude` (gibt die Antwort als Promise zurück).
 */
export function starteKosmoMausAufruf(aufruf: { kennung: string; werkzeug: string; argumente: unknown; herkunft?: string }): null {
  if (laufend.has(aufruf.kennung)) return null;
  laufend.add(aufruf.kennung);
  void fuehreKosmoMausAufrufFuerClaude(aufruf)
    .catch((e) => ({ kennung: aufruf.kennung, ok: false, text: `FEHLER: ${e instanceof Error ? e.message : String(e)}` }))
    .then((antwort) => {
      laufend.delete(aufruf.kennung);
      sendeAntwort(antwort);
    });
  return null;
}

// ---------------------------------------------------------------------------
// Anschluss Kosmo (Chat-Werkzeuge über `kosmoUiWerkzeuge`)
// ---------------------------------------------------------------------------

/**
 * Dieselben zwei Werkzeuge für Kosmo, mit dem Urheber «kosmo». `meldung`
 * schreibt jede Maus-Handlung als sichtbare Zeile in den Chat (dieselbe
 * Ehrlichkeit wie bei den `ui.*`-Werkzeugen).
 */
export function kosmoMausReadTools(meldung?: (text: string) => void): ReadTool[] {
  const alsText = (r: WerkzeugAntwort) => (r.ok ? r.text : r.text.startsWith('FEHLER') ? r.text : `FEHLER: ${r.text}`);
  return [
    {
      name: BLICK_WERKZEUG,
      description: BLICK_BESCHREIBUNG,
      parameters: BLICK_PARAMETER,
      execute: async (args: unknown) => alsText(await fuehreBlickAus('kosmo', args, 'lokal')),
    },
    {
      name: MAUS_WERKZEUG,
      description: MAUS_BESCHREIBUNG,
      parameters: MAUS_PARAMETER,
      execute: async (args: unknown) => {
        const r = await fuehreMausAus('kosmo', args, 'lokal');
        if (r.ok) meldung?.(`Kosmo bedient: ${r.text.split('\n')[0]!.replace(/^OK: /, '')}`);
        return alsText(r);
      },
    },
  ];
}

// ---------------------------------------------------------------------------
// Projektwechsel: offene Karten sichtbar verwerfen (Owner-Entscheid 08.10.2026, «A»)
// ---------------------------------------------------------------------------

export const VERWORFEN_PROJEKTWECHSEL = 'Projekt gewechselt';

/**
 * Owner-Abnahme 07.10.: offene Karten (Claude c-154, Kosmos
 * `kosmoprepare_splat_verorten`) waren nach einem Wechsel über die
 * Projektreiter still weg bzw. hingen am falschen Projekt — eine Karte gilt
 * für das Doc, in dem sie entstand. Owner-Entscheid 08.10.2026 «A: sichtbar
 * verwerfen»: beim Wechsel fallen offene Karten von Claude und aus der
 * KosmoMaus weg, mit Journalzeile «verworfen: Projekt gewechselt», einer
 * Meldung, und Claude erfährt es (`kosmo_vorschlag_status` liefert
 * «VERWORFEN: Projekt gewechselt …»). Kosmos Chat-Karten liegen in
 * `KosmoPanel.tsx` (UI-Worker) — dort nicht hier.
 */
export function verwirfOffeneKartenBeimWechsel(): number {
  const claude = verwirfClaudeVorschlaege(VERWORFEN_PROJEKTWECHSEL);
  const maus = verwirfMausVorschlaege(VERWORFEN_PROJEKTWECHSEL);
  for (const v of claude) {
    protokolliere({
      urheber: 'claude',
      werkzeug: 'maus',
      aktion: 'verworfen',
      ziel: v.commandId,
      ergebnis: 'ok',
      text: `verworfen: ${VERWORFEN_PROJEKTWECHSEL} — Claude-Karte ${v.kennung} «${v.zusammenfassung}»`,
    });
  }
  const n = claude.length + maus.length;
  if (n > 0) {
    melde(
      n === 1
        ? `1 offene Karte verworfen: ${VERWORFEN_PROJEKTWECHSEL} (sie galt für das vorige Projekt).`
        : `${n} offene Karten verworfen: ${VERWORFEN_PROJEKTWECHSEL} (sie galten für das vorige Projekt).`,
      { ton: 'info' },
    );
  }
  return n;
}
beiProjektWechsel(() => {
  verwirfOffeneKartenBeimWechsel();
});
