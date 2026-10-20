import { URHEBER_NAME as NAME, type Urheber } from '../../state/kosmo-maus-freigabe';

/**
 * **Erzählzeile** (Video-Analyse 16.10. L5-5/13/18/21, Integrator L1-7, Nr. 55 Teil 2).
 *
 * Im Demolauf sah man in der App nicht, was Claude oder Kosmo gerade tun: die
 * Werkzeuge hinterliessen eine winzige Textzeile, Wartezeiten auf den Owner
 * (24 Phasen, 13 min) standen nirgends, eine offene Karte lag klein unten links.
 * Die Erzählzeile oben in der Mitte sagt es in einem Satz:
 *
 * 1. **wartet** — eine Karte wartet auf den Architekten («Claude wartet auf dich»);
 *    hat Vorrang, weil ohne ihn nichts weitergeht;
 * 2. **schritt** — ein Schritt ist eben gesetzt («Claude · Wand 4.00 m»);
 * 3. **arbeitet** — ein Aufruf kam gerade an, ohne sichtbaren Schritt (lesen, schauen).
 *
 * Reine Ableitung aus offenen Claude-Karten, Coop-Schritten, der Zeit des letzten
 * Aufrufs und (L71) dem Tätigkeitsstrom aus R37 (`state/claude-taetigkeit.ts`):
 * damit sagt «arbeitet» das Werkzeug und «Versuch 2» (L5-21), und ein Fehlschlag
 * steht als eigene Zeile **fehler** da, statt still zu verschwinden.
 */

/** So lange nach einem gesetzten Schritt steht er in der Zeile. */
export const ERZAEHL_SCHRITT_MS = 6000;
/** So lange nach einem Aufruf ohne Schritt steht «arbeitet». */
export const ERZAEHL_AUFRUF_MS = 4000;
/** So lange steht ein Fehlschlag in der Zeile. */
export const ERZAEHL_FEHLER_MS = 8000;
/** Ein Aufruf ohne Antwort gilt danach nicht mehr als «läuft» (abgerissene Verbindung). */
export const ERZAEHL_LAUF_MAX_MS = 30000;

/** Die jüngste Tätigkeit von Claude, Form wie `ClaudeTaetigkeit` (R37). */
export interface ErzaehlTaetigkeit {
  werkzeug: string;
  beginn: number;
  ende?: number;
  fehler?: string;
  versuch?: number;
}

export interface ErzaehlEingang {
  jetzt: number;
  /** Offene Claude-Karten (älteste zuerst). */
  offeneKarten: readonly { kennung: string; zusammenfassung: string }[];
  /** Jüngster Coop-Schritt, falls vorhanden. */
  letzterSchritt: { urheber: Urheber; zusammenfassung: string; zeit: number; zurueckgenommen: boolean } | null;
  /** Zeit (ms) des letzten Werkzeugaufrufs von Claude. */
  zuletztAktiv: number | null;
  /** Jüngste Tätigkeit von Claude aus dem Tätigkeitsstrom (fehlt in alten Proben). */
  taetigkeit?: ErzaehlTaetigkeit | null;
}

export type Erzaehlung =
  | { art: 'wartet'; urheber: Urheber; text: string; zusatz: string; kennung: string }
  | { art: 'schritt'; urheber: Urheber; text: string }
  | { art: 'arbeitet'; urheber: Urheber; text: string }
  | { art: 'fehler'; urheber: Urheber; text: string; zusatz: string };

/**
 * Werkzeugname lesbar: der Namensraum vor dem ersten Unterstrich fällt weg (`design_wandZeichnen`
 * → «wand zeichnen», `toolNameFor`), camelCase und Unterstriche werden Wörter.
 */
export function werkzeugText(name: string): string {
  const i = name.indexOf('_');
  const aktion = i > 0 && i < name.length - 1 ? name.slice(i + 1) : name;
  return aktion
    .replace(/([a-zäöü0-9])([A-ZÄÖÜ])/g, '$1 $2')
    .replace(/[_.]+/g, ' ')
    .trim()
    .toLowerCase();
}

export function erzaehlungAus(e: ErzaehlEingang): Erzaehlung | null {
  const karte = e.offeneKarten[0];
  if (karte) {
    const weitere = e.offeneKarten.length - 1;
    return {
      art: 'wartet',
      urheber: 'claude',
      text: 'Claude wartet auf dich',
      zusatz: weitere > 0 ? `${karte.zusammenfassung} · und ${weitere} weitere` : karte.zusammenfassung,
      kennung: karte.kennung,
    };
  }
  const s = e.letzterSchritt;
  const schrittZeit = s && !s.zurueckgenommen ? s.zeit : -Infinity;
  const t = e.taetigkeit ?? null;
  // Was jünger ist als der letzte Schritt, erzählt zuerst: ein laufender Aufruf, dann ein Fehlschlag.
  if (t && t.ende === undefined && t.beginn >= schrittZeit && e.jetzt - t.beginn >= 0 && e.jetzt - t.beginn < ERZAEHL_LAUF_MAX_MS) {
    const versuch = t.versuch !== undefined && t.versuch >= 2 ? ` · Versuch ${t.versuch}` : '';
    return { art: 'arbeitet', urheber: 'claude', text: `Claude · ${werkzeugText(t.werkzeug)}${versuch} …` };
  }
  if (t && t.fehler !== undefined && t.ende !== undefined && t.ende >= schrittZeit && e.jetzt - t.ende >= 0 && e.jetzt - t.ende < ERZAEHL_FEHLER_MS) {
    return { art: 'fehler', urheber: 'claude', text: `Claude · ${werkzeugText(t.werkzeug)} ging nicht`, zusatz: t.fehler };
  }
  if (s && !s.zurueckgenommen && e.jetzt - s.zeit >= 0 && e.jetzt - s.zeit < ERZAEHL_SCHRITT_MS) {
    return { art: 'schritt', urheber: s.urheber, text: `${NAME[s.urheber]} · ${s.zusammenfassung}` };
  }
  if (e.zuletztAktiv !== null && e.jetzt - e.zuletztAktiv >= 0 && e.jetzt - e.zuletztAktiv < ERZAEHL_AUFRUF_MS) {
    const was = t && t.beginn >= e.zuletztAktiv - 1000 ? ` · ${werkzeugText(t.werkzeug)}` : ' …';
    return { art: 'arbeitet', urheber: 'claude', text: `Claude arbeitet${was}` };
  }
  return null;
}

/** Wann die Zeile von selbst wechselt (für den Takt der Anzeige), `null` = nie. */
export function naechsterWechsel(e: ErzaehlEingang): number | null {
  const kandidaten: number[] = [];
  if (e.letzterSchritt) kandidaten.push(e.letzterSchritt.zeit + ERZAEHL_SCHRITT_MS);
  if (e.zuletztAktiv !== null) kandidaten.push(e.zuletztAktiv + ERZAEHL_AUFRUF_MS);
  const t = e.taetigkeit;
  if (t && t.ende === undefined) kandidaten.push(t.beginn + ERZAEHL_LAUF_MAX_MS);
  if (t && t.ende !== undefined && t.fehler !== undefined) kandidaten.push(t.ende + ERZAEHL_FEHLER_MS);
  const kuenftig = kandidaten.filter((t) => t > e.jetzt);
  return kuenftig.length ? Math.min(...kuenftig) : null;
}

export interface LageKasten {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

/** Bedienteile oben, denen die Zeile ausweicht (nur gelesen; Würfel/Regler von KosmoDraw, Kopf-Pillen der Inseln). */
export const ERZAEHL_HINDERNISSE = [
  '[data-testid="c1-wuerfel"]',
  '[data-testid="d5-schnitt-regler"]',
  '[data-testid="island-ansicht-root"]',
  '[data-testid="island-kopf-zweitgruppe"]',
  '.isl-buehnenkopf',
];

const RAND = 16;
const LUFT = 8;

/**
 * Lage der Zeile im Fenster: so mittig wie möglich auf der Wunschhöhe; liegt dort ein
 * Bedienteil (Ansichtswürfel, Schnitt-Regler in der geteilten Ansicht), rückt sie in
 * die breiteste freie Strecke daneben, und reicht keine, unter die Teile dieses
 * Bandes. Dasselbe Verfahren wie `modules/design/hinweis-lage.ts`, aber mit der
 * eigenen Breite der Zeile statt einer Wunschbreite.
 */
export function erzaehlLage(
  fensterBreite: number,
  wunschOben: number,
  breite: number,
  hoehe: number,
  hindernisse: readonly LageKasten[],
): { left: number; top: number } {
  const von0 = RAND;
  const bis0 = fensterBreite - RAND;
  const mitte = fensterBreite / 2;
  let oben = wunschOben;
  for (let versuch = 0; versuch < 4; versuch++) {
    const imBand = hindernisse.filter((h) => h.top < oben + hoehe + LUFT && h.bottom > oben - LUFT && h.right > von0 && h.left < bis0);
    const strecken: { von: number; bis: number }[] = [];
    let von = von0;
    for (const h of [...imBand].sort((a, b) => a.left - b.left)) {
      if (h.left - LUFT > von) strecken.push({ von, bis: h.left - LUFT });
      von = Math.max(von, h.right + LUFT);
    }
    if (bis0 > von) strecken.push({ von, bis: bis0 });
    // Unter den Strecken, die die Zeile fassen, die mit dem kleinsten Weg zur Mitte.
    const passend = strecken.filter((s) => s.bis - s.von >= breite);
    if (passend.length > 0) {
      const lage = passend.map((s) => Math.min(Math.max(mitte - breite / 2, s.von), s.bis - breite));
      const left = lage.reduce((a, b) => (Math.abs(b + breite / 2 - mitte) < Math.abs(a + breite / 2 - mitte) ? b : a));
      return { left, top: oben };
    }
    oben = Math.max(...imBand.map((h) => h.bottom)) + LUFT;
  }
  return { left: Math.max(von0, mitte - breite / 2), top: oben };
}
