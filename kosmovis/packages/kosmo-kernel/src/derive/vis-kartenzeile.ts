import type { VisEdge, VisGraph, VisNode } from '../model/entities';
import { liesListe } from './varianten';
import { isVisPresetId, visPresetById } from './render-presets';
import { BESTELLFORMAT_VORGABE } from './kamera-aus-3d';
import { KAMERA_AUTO_VORGABEN, KAMERA_RICHTUNGEN, stimmungAufruf, stimmungAusParams, visPort, VIS_NODE_KATALOG, VIS_STIMMUNGEN } from './visgraph';

/**
 * **Kartenzeile** der Vis-Befehle — Owner-Entscheid der Visbox vom 22.10.2026 (Mac-Test 0.3.33,
 * Karte K-10): «die Karte zeigt WERTE statt Feldnamen». Bis dahin stand auf der Karte «Vorschlag von
 * Claude» der Satz `Node-Parameter (preset, presets)`; der Architekt sah, DASS etwas geändert werden
 * soll, aber nicht WAS. Jetzt: «Stimmung: Morgenlicht → Abendstimmung».
 *
 * Regeln (eine je Zeile, pur, ohne Zeit und Zufall — die Doppellauf-Probe in `vis-render.test.ts`):
 *  - Knoten heissen wie im Katalog (`VIS_NODE_KATALOG[typ].label`), der Render-Knoten «Render-Knoten».
 *  - Felder heissen in Alltagswörtern (`FELDER`); ein Feld ohne Eintrag heisst «weitere Einstellung»,
 *    NIE mit seinem Rohnamen.
 *  - Werte stehen in ihren Anzeigenamen (Stimmungen, Himmelsrichtungen, Güte, Auflösung «1600 × 1000»,
 *    Bildwerkzeug); ein freier Text steht gekürzt in «».
 *  - **Vorher → Nachher**, wenn der Vorher-Wert bekannt ist und sich unterscheidet; sonst nur der
 *    neue Wert. Der Vorher-Wert kommt aus dem Dokument VOR dem Lauf: `execute()` ruft `summarize`
 *    erst NACH `doc.apply` (Journal, Paket-Probelauf auf der Kopie) — darum merkt sich `vis.ts` den
 *    Graphen beim Lesen (`merkeGraph`) und reicht ihn hier herein.
 */

type Wert = string | number | boolean;
type Params = Record<string, Wert>;

/** Anzeige-Namen der Bildwerkzeuge — wortgleich `BILDWERKZEUG_TEXTE[…].name` der App (`vis-jobs.ts`);
 *  die Probe `kv-kartenzeile.test.ts` hält beide gleich (der Kern darf die App nicht einbinden). */
export const BILDWERKZEUG_NAMEN: Readonly<Record<string, string>> = {
  'z-image-turbo': 'Z-Image Turbo',
  sdxl: 'SDXL / Juggernaut',
  'flux2-klein': 'FLUX.2 [klein]',
  qwen: 'Qwen-Image-Edit',
  'flux-krea': 'FLUX.1-Krea-dev',
  'qwen-image-2.1': 'Qwen-Image 2.1',
};

/** Güte am Render-Knoten — wortgleich `GUETE_TEXTE[…].name` der App (`guete.ts`), Probe wie oben. */
export const GUETE_NAMEN: Readonly<Record<string, string>> = { vorschau: 'Vorschau', voll: 'Voll' };

const KURZ = 40;

function zahl(n: number): string {
  return String(Math.round(n * 100) / 100).replace('.', ',');
}

function kurzText(s: string): string {
  const t = s.replace(/\s+/g, ' ').trim();
  if (t === '') return 'leer';
  return `«${t.length > KURZ ? `${t.slice(0, KURZ - 1).trimEnd()}…` : t}»`;
}

function anAus(v: Wert): string {
  return v === true || v === 'true' ? 'an' : 'aus';
}

function stimmungName(id: string): string {
  return VIS_STIMMUNGEN[id]?.label ?? 'eine unbekannte Stimmung';
}

function richtungen(v: Wert): string {
  const l = liesListe(v) ?? [];
  const namen = KAMERA_RICHTUNGEN.filter((r) => l.includes(r.kuerzel)).map((r) => r.name);
  return namen.length ? namen.join(', ') : 'keine';
}

function liste(v: Wert, einzeln: (s: string) => string): string {
  const l = liesListe(v);
  if (!l) return kurzText(String(v));
  return l.length ? l.map(einzeln).join(', ') : 'keine';
}

function aufloesung(v: Wert): string {
  const m = /^(\d+)\s*[x×]\s*(\d+)$/.exec(String(v));
  return m ? `${m[1]} × ${m[2]}` : kurzText(String(v));
}

function wort(s: string): string {
  const t = s.replace(/[-_]+/g, ' ').trim();
  return t ? `«${t.charAt(0).toUpperCase()}${t.slice(1)}»` : 'leer';
}

interface Feld {
  readonly wort: string;
  readonly wert?: (v: Wert) => string;
  /** Was gilt, solange am Knoten nichts steht — dann ist das der Vorher-Wert («Süd, Südost, Nordwest»). */
  readonly vorgabe?: Wert;
}

/** Alltagswörter der Felder, je Knotenart (`*` gilt für alle). Was fehlt, heisst «weitere Einstellung». */
const FELDER: Readonly<Record<string, Readonly<Record<string, Feld>>>> = {
  '*': {
    text: { wort: 'Text', wert: (v) => kurzText(String(v)) },
    titel: { wort: 'Titel', wert: (v) => kurzText(String(v)) },
  },
  prompt: { text: { wort: 'Stil-Text', wert: (v) => kurzText(String(v)) } },
  stimmung: {
    drehung: { wort: 'Himmel gedreht', wert: (v) => `${zahl(Number(v))}°` },
    wirkung: { wort: 'Wirkung', wert: (v) => ({ licht: 'nur Licht', prompt: 'nur Satz fürs Bild', 'licht+prompt': 'Licht und Satz' } as Record<string, string>)[String(v)] ?? wort(String(v)) },
  },
  zahl: {
    wert: { wort: 'Wert', wert: (v) => zahl(Number(v)) },
    min: { wort: 'Untergrenze', wert: (v) => zahl(Number(v)) },
    max: { wort: 'Obergrenze', wert: (v) => zahl(Number(v)) },
    schritt: { wort: 'Schrittweite', wert: (v) => zahl(Number(v)) },
  },
  render: {
    // Entscheid 143: der Schalter am Render-Knoten waehlt die Güte von «Variante erzeugen» — ohne Wahl Voll
    // (`gueteAmKnoten(params, 'variante')` der App); so steht es als «vorher» auf der Karte.
    guete: { wort: 'Güte', wert: (v) => GUETE_NAMEN[String(v)] ?? wort(String(v)), vorgabe: 'voll' },
    aufloesung: { wort: 'Auflösung', wert: aufloesung, vorgabe: BESTELLFORMAT_VORGABE.join('x') },
    abtastungen: { wort: 'Abtastungen', wert: (v) => zahl(Number(v)) },
    backbone: { wort: 'Bildwerkzeug', wert: (v) => BILDWERKZEUG_NAMEN[String(v)] ?? wort(String(v)) },
    preset: { wort: 'Licht-Vorlage', wert: (v) => (isVisPresetId(v) ? `«${visPresetById(v).name}»` : 'keine') },
    lineart: { wort: 'Strichzeichnung', wert: anAus },
    nurCycles: { wort: 'nur Grundlage', wert: anAus },
    seed: { wort: 'Startwert', wert: (v) => String(v) },
    himmel: { wort: 'Himmel', wert: (v) => (String(v) ? wort(String(v).toLowerCase()) : 'aus der Stimmung') },
    umgebungDrehungGrad: { wort: 'Himmel gedreht', wert: (v) => `${zahl(Number(v))}°` },
    formSzene: { wort: 'Szene', wert: (v) => kurzText(String(v)) },
    formJahreszeit: { wort: 'Jahreszeit', wert: (v) => kurzText(String(v)) },
    formPersonen: { wort: 'Personen', wert: (v) => kurzText(String(v)) },
    formFassade: { wort: 'Fassade', wert: (v) => kurzText(String(v)) },
    formFreitext: { wort: 'Zusatz', wert: (v) => kurzText(String(v)) },
    verlaufOffen: { wort: 'Verlauf', wert: (v) => (v === true ? 'offen' : 'zu') },
  },
  kamera: {
    art: { wort: 'Art', wert: (v) => ({ auto: 'Auto', manuell: 'Manuell', blick: 'Blick' } as Record<string, string>)[String(v)] ?? 'aus dem Modell' },
    richtungen: { wort: 'Richtungen', wert: richtungen, vorgabe: JSON.stringify(KAMERA_AUTO_VORGABEN.richtungen) },
    augenhoehe: { wort: 'Augenhöhe', wert: (v) => `${zahl(Number(v))} m` },
    brennweite: { wort: 'Brennweite', wert: (v) => `${zahl(Number(v))} mm` },
    fuellt: { wort: 'Haus füllt', wert: (v) => `${Math.round(Number(v) * 100)} %` },
    abstandM: { wort: 'Abstand', wert: (v) => `${zahl(Number(v))} m` },
    perspektive: { wort: 'Senkrechte', wert: (v) => (v === 'frei' ? 'frei gekippt' : 'gerade') },
    kameras: { wort: 'Standpunkte', wert: (v) => { const l = liesListe(v); return l ? `${l.length} von Hand` : 'von Hand'; } },
  },
  skizzeIpad: { skizze: { wort: 'Skizze', wert: (v) => (v === 'neueste' ? 'die neueste' : kurzText(String(v))) } },
  referenz: { url: { wort: 'Bildadresse', wert: (v) => kurzText(String(v)) } },
  aufnahme: { kamera: { wort: 'Standpunkt', wert: (v) => (v === 'aktuell' ? 'der aktuelle' : kurzText(String(v))) } },
  materialTextur: {
    bibliothek: { wort: 'Material', wert: (v) => wort(String(v)) },
    massstab: { wort: 'Massstab', wert: (v) => `${zahl(Number(v))} m` },
    drehung: { wort: 'Drehung', wert: (v) => `${zahl(Number(v))}°` },
    relief: { wort: 'Relief', wert: (v) => zahl(Number(v)) },
  },
  farbpalette: {
    farben: { wort: 'Farben', wert: (v) => { const l = liesListe(v); return l ? `${l.length}` : 'eigene'; } },
    leitfarbe: { wort: 'Leitfarbe', wert: (v) => `Nr. ${Number(v) + 1}` },
    staerke: { wort: 'Stärke', wert: (v) => `${Math.round(Number(v) * 100)} %` },
  },
  varianten: {
    standpunkte: { wort: 'Standpunkte', wert: (v) => liste(v, (s) => `«${s}»`) },
    stimmungen: { wort: 'Stimmungen', wert: (v) => liste(v, stimmungName) },
    entwuerfe: { wort: 'Entwürfe', wert: (v) => liste(v, (s) => (s === 'aktuell' ? 'aktuelles Modell' : `«${s}»`)) },
    // Entscheid 143: Varianten rechnen ohne Wahl voll; eine Vorschau wird ausdruecklich gesetzt.
    guete: { wort: 'Güte', wert: (v) => GUETE_NAMEN[String(v)] ?? wort(String(v)), vorgabe: 'voll' },
  },
};

/** Ein Knoten in Alltagswort: der Name aus dem Katalog, der Render-Knoten «Render-Knoten». */
export function knotenWort(typ: string | undefined): string {
  if (typ === 'render') return 'Render-Knoten';
  return (typ && VIS_NODE_KATALOG[typ]?.label) || 'Knoten';
}

function inAnfuehrung(typ: string | undefined): string {
  return typ === 'render' ? 'Render-Knoten' : `«${knotenWort(typ)}»`;
}

/** Stimmung eines Knotens als Anzeige: die gewählten Namen (Liste vor Einzelwert, wie gerendert). */
function stimmungAnzeige(params: Params | undefined): string {
  const w = stimmungAusParams(params ?? {});
  return w.presets.length ? w.presets.map(stimmungName).join(', ') : 'keine';
}

function feldText(f: { wort: string; vorher?: string; nachher: string }): string {
  return f.vorher !== undefined && f.vorher !== f.nachher ? `${f.wort}: ${f.vorher} → ${f.nachher}` : `${f.wort}: ${f.nachher}`;
}

/**
 * Die Felder einer Änderung als Zeilenteile. `vorher` = Parameter des Knotens vor dem Lauf (fehlt beim
 * Anlegen). Am Stimmung-Knoten sind `preset` und `presets` EIN Feld «Stimmung» (sie werden zusammen
 * gesetzt, und gerendert wird die Liste vor dem Einzelwert).
 */
function felder(typ: string | undefined, neu: Params, vorher: Params | undefined): string[] {
  const teile: string[] = [];
  let weitere = 0;
  const schluessel = Object.keys(neu);
  if (typ === 'stimmung' && (schluessel.includes('preset') || schluessel.includes('presets'))) {
    // Der Neu-Wert nach DERSELBEN Regel, die der Befehl schreibt (`stimmungAufruf`: presets gewinnt,
    // sonst ersetzt preset die Wahl). Vorher stand hier `{ ...vorher, ...neu }` — bei einem Aufruf mit
    // nur `preset` gewann so die ALTE Liste `presets` aus dem Graphen, und die Karte sagte
    // «Stimmung: Abendstimmung», obwohl Morgenlicht angewendet wurde (Visbox-Mac-Befund 0.3.35).
    const regel = stimmungAufruf(neu);
    const nachher = stimmungAnzeige({ ...(vorher ?? {}), ...('fehler' in regel ? neu : regel.params) });
    teile.push(feldText({ wort: 'Stimmung', nachher, ...(vorher ? { vorher: stimmungAnzeige(vorher) } : {}) }));
  }
  for (const k of schluessel) {
    if (typ === 'stimmung' && (k === 'preset' || k === 'presets')) continue;
    const f = FELDER[typ ?? '']?.[k] ?? FELDER['*']![k];
    if (!f) {
      weitere++;
      continue;
    }
    const zeig = f.wert ?? ((v: Wert) => String(v));
    // Beim Ändern (vorher bekannt) gilt ohne Eintrag die Vorgabe des Knotens; beim Anlegen nicht.
    const alt = vorher ? (vorher[k] ?? f.vorgabe) : undefined;
    teile.push(feldText({ wort: f.wort, nachher: zeig(neu[k]!), ...(alt !== undefined ? { vorher: zeig(alt) } : {}) }));
  }
  if (weitere > 0) teile.push(weitere === 1 ? 'eine weitere Einstellung' : `${weitere} weitere Einstellungen`);
  return teile;
}

/** `vis.nodeParametrieren`: «Stimmung: Morgenlicht → Abendstimmung», «Render-Knoten · Güte: Voll → Vorschau». */
export function parameterZeile(node: VisNode | undefined, neu: Params, vorher: Params | undefined): string {
  const typ = node?.typ;
  const teile = felder(typ, neu, vorher);
  if (teile.length === 0) return `${knotenWort(typ)}: keine Änderung`;
  const knoten = knotenWort(typ);
  // Heisst das einzige Feld wie der Knoten («Stimmung»), steht der Knoten nicht doppelt da.
  if (teile.length === 1 && teile[0]!.startsWith(`${knoten}:`)) return teile[0]!;
  return `${knoten} · ${teile.join(' · ')}`;
}

/** `vis.nodeSetzen`: «Neuer Knoten «Stimmung» · Stimmung: Abendstimmung». */
export function neuerKnotenZeile(typ: string, params: Params | undefined): string {
  const kopf = VIS_NODE_KATALOG[typ] ? `Neuer Knoten ${inAnfuehrung(typ)}` : 'Neuer Knoten';
  const teile = params && Object.keys(params).length ? felder(typ, params, undefined) : [];
  return teile.length ? `${kopf} · ${teile.join(' · ')}` : kopf;
}

function portWort(typ: string | undefined, port: string, richtung: 'in' | 'out'): string {
  const p = typ ? visPort(typ, port, richtung) : undefined;
  return p ? `«${p.label}»` : 'einen Anschluss';
}

/** `vis.verbinden`: «Verbinden: «Stimmung» an «Prompt-Kombinierer», Eingang «Stimmung»». */
export function verbindenZeile(von: VisNode | undefined, zu: VisNode | undefined, toPort: string): string {
  return `Verbinden: ${inAnfuehrung(von?.typ)} an ${inAnfuehrung(zu?.typ)}, Eingang ${portWort(zu?.typ, toPort, 'in')}`;
}

/** `vis.trennen`: «Verbindung lösen: «Stimmung» von «Prompt-Kombinierer», Eingang «Stimmung»». */
export function trennenZeile(graph: VisGraph | undefined, edgeId: string): string {
  const e: VisEdge | undefined = graph?.edges.find((x) => x.id === edgeId);
  if (!e || !graph) return 'Verbindung lösen';
  const von = graph.nodes.find((n) => n.id === e.from);
  const zu = graph.nodes.find((n) => n.id === e.to);
  return `Verbindung lösen: ${inAnfuehrung(von?.typ)} von ${inAnfuehrung(zu?.typ)}, Eingang ${portWort(zu?.typ, e.toPort, 'in')}`;
}

/*
 * **Wer gibt frei?** (Geräteprobe R57, 23.10.2026). In der Vollautomatik (KosmoOrbit E178: die eigenen
 * Vorschläge der Agenten werden ohne Karte angewendet) sagten die Bestellsätze von `vis.render` und
 * `vis.varianten` weiter «Freigabe durch den Architekten» bzw. «wartet auf Freigabe», die Aufträge
 * rechneten aber sofort. Ob sie das tun, weiss nur die App, nicht der Kern — sie meldet es darum hier an
 * (`setzeOhneFreigabeLeser`, wie `setzeVariantenStandLeser`). Ohne Meldung (Kern allein, Proben ohne App,
 * Visbox: dort gibt immer ein Mensch die Grafikkarte frei, Entscheide 106b/134) bleibt der alte Satz.
 * Nur der Wortlaut hängt daran, kein Verhalten.
 */
type OhneFreigabeLeser = () => boolean;
let ohneFreigabeLeser: OhneFreigabeLeser | null = null;

/** Die App meldet, ob ein bestellter Auftrag gerade ohne Freigabe rechnet (KosmoOrbit: Vollautomatik an). */
export function setzeOhneFreigabeLeser(leser: OhneFreigabeLeser | null): void {
  ohneFreigabeLeser = leser;
}

/** Rechnet ein bestellter Auftrag ohne Freigabe? Ohne angemeldeten Leser, oder wenn er scheitert: nein. */
export function rechnetOhneFreigabe(): boolean {
  try {
    return ohneFreigabeLeser?.() === true;
  } catch {
    return false;
  }
}

/** Der Zusatz am Render-Knoten, wenn niemand freigibt — und der Satz für jeden Varianten-Auftrag. */
export const OHNE_FREIGABE_RENDER = 'rechnet ohne Freigabe, Vollautomatik';
export const OHNE_FREIGABE_VARIANTEN = 'jeder startet ohne Freigabe (Vollautomatik)';

/**
 * `vis.render`: «Vorschau rechnen am Render-Knoten (Freigabe durch den Architekten) · Stimmung: Abendstimmung»;
 * in der Vollautomatik «… am Render-Knoten (rechnet ohne Freigabe, Vollautomatik) · …».
 */
export function renderZeile(p: {
  kameraWahl: 'auto' | 'saved';
  stimmungPreset?: string | undefined;
  backbone?: string | undefined;
  guete?: string | undefined;
  aufloesung?: readonly [number, number] | undefined;
  seed?: number | undefined;
}): string {
  const was = p.guete === 'vorschau' ? 'Vorschau rechnen' : 'Bild in voller Güte rechnen';
  const teile = [`${was} am Render-Knoten (${rechnetOhneFreigabe() ? OHNE_FREIGABE_RENDER : 'Freigabe durch den Architekten'})`];
  if (p.stimmungPreset) teile.push(`Stimmung: ${stimmungName(p.stimmungPreset)}`);
  if (p.kameraWahl === 'saved') teile.push('Standpunkte: die am Heim-PC gemerkten');
  if (p.backbone) teile.push(`Bildwerkzeug: ${BILDWERKZEUG_NAMEN[p.backbone] ?? wort(p.backbone)}`);
  if (p.aufloesung) teile.push(`Auflösung: ${p.aufloesung[0]} × ${p.aufloesung[1]}`);
  if (p.seed !== undefined) teile.push(`Startwert: ${p.seed}`);
  return teile.join(' · ');
}
