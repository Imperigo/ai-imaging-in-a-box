import type { KosmoDoc } from '../model/doc';
import type { VisEdge, VisGraph, VisNode, VisPortTyp } from '../model/entities';
import { finalerRenderPrompt, renderPromptBausteine } from './renderprompt';
import { projektKameras, type AutoKameraStandpunkt } from './kamera';
import {
  BESTELLFORMAT_VORGABE,
  FOV_GRENZEN_GRAD,
  KAMERA_AUS_3D_TYP,
  kameraAus3dAusParams,
  kameraAus3dStandpunkt,
  seitenverhaeltnisAus,
} from './kamera-aus-3d';
import { isVisPresetId, visPresetById, type VisPresetId } from './render-presets';
import { liesListe, schreibeListe, VARIANTEN_TYP, vorfahren } from './varianten';

/**
 * Render-Graph-Maschine (V1-Finish P2) — das Herz des KosmoVis-Node-Trees.
 * Pull-basierte, topologische Auswertung: pure Nodes (Prompt, Stimmung,
 * Kombinierer, Zahl, Material) rechnen hier synchron; Render bleibt ein
 * expliziter Auftrag (die App schickt ihn an die Bridge, nie automatisch).
 * Bild-Werte existieren nur zur Laufzeit — der Graph kennt sie als Typ,
 * aber nie als Daten.
 */

export interface VisPort {
  name: string;
  typ: VisPortTyp;
  label: string;
  /**
   * Owner-Entscheid 96 (Visbox, 15.10.2026): NUR diese Knotenarten duerfen in
   * diesen Eingang. Fehlt das Feld, gilt allein der Porttyp (wie bisher). Der
   * Eingang «Skizze» am Render-Knoten ist vom Typ `bild`, nimmt aber nur die
   * «Skizze vom iPad»: die Bestellung kann eine Skizze der Mappe nennen
   * (`RenderScene.skizze`), kein beliebiges Bild aus dem Graphen.
   */
  nurVon?: readonly string[];
}

/**
 * Node-Kategorie (W1, UI-KONZEPT-065 §5) — reine Katalog-Metadaten für die
 * Kopf-Gestaltung im Node-Editor (KIcon + 2px-Tonstreifen je Kategorie).
 * Keine Auswirkung auf `evaluiereGraph`/Entities — rein visuelle Gruppierung.
 */
export type VisKategorie = 'quelle' | 'wandler' | 'render' | 'ausgabe';

export interface VisNodeTyp {
  typ: string;
  label: string;
  /** Kurzbeschrieb für Palette + Kosmo. */
  hilfe: string;
  /** W1: Quelle/Wandler/Render/Ausgabe — steuert Kopf-Icon + Tonstreifen. */
  kategorie: VisKategorie;
  inputs: VisPort[];
  outputs: VisPort[];
  /** Default-Parameter beim Setzen. */
  defaults: Record<string, string | number | boolean>;
}

/**
 * Zurückhaltende Kategorie-Hue-Zuordnung (W1) — bewusst bestehende
 * `--k-mod-*`-Tokens aus `aura.css` wiederverwendet (keine neuen Farbwerte),
 * je Kategorie EIN Ton für den 2px-Tonstreifen unter dem Node-Kopf.
 *
 * Kritik-065 Runde 1, Befund 6: `--k-mod-prepare` (#7d5e78, Violett) lag zu
 * nah an der Zahl-Portfarbe (`PORT_FARBE.zahl` = #7a5c9e, ebenfalls Violett)
 * — beide praktisch ununterscheidbar im Node-Kopf/-Port nebeneinander. Alle
 * übrigen `--k-mod-*`-Töne sind schon an eine Kategorie vergeben (data=Blau
 * → quelle, design=Terracotta → render, publish=Grün → ausgabe; vis=Gold
 * ist die Stationsfarbe selbst, oben im Badge/Bullet bereits sichtbar) —
 * daher hier EIN neuer, bewusst zurückhaltender Ocker/Braun-Ton, in
 * derselben Familie wie `PORT_FARBE.material` (#8a6d3b), aber eigenständig.
 */
const K_WANDLER_OCKER = '#96702f';

export const VIS_KATEGORIE_HUE: Record<VisKategorie, string> = {
  quelle: 'var(--k-mod-data)',
  wandler: K_WANDLER_OCKER,
  render: 'var(--k-mod-design)',
  ausgabe: 'var(--k-mod-publish)',
};

/**
 * Die Stimmungen. Bauplan «Neue Knoten» Schritt K (Visbox-Entscheide 110 B / 113, 20.10.2026):
 * acht statt drei, in der Reihenfolge der Visbox (`aiimaging.stimmung.STIMMUNGEN`). Der Satz ist
 * der, den der Knoten in den Prompt legt — wortgleich mit `prompt_de` dort (die Visbox-Probe
 * `test_knoten_neu_katalog.py` haelt beide gleich). Hinter jeder Stimmung liegt am Heim-PC ein
 * Himmelsbild (CC0, Poly Haven, Entscheid 107), das in Blender das Licht gibt; die App schickt
 * nur den Namen der Stimmung (`render.environment.preset`), das Bild waehlt der Heim-PC.
 */
export const VIS_STIMMUNGEN: Record<string, { label: string; prompt: string }> = {
  morgen: { label: 'Morgenlicht', prompt: 'Morgenlicht, klare lange Schatten, frische kühle Luft' },
  mittag: { label: 'Mittag', prompt: 'Mittagslicht, hohe Sonne, klarer Himmel' },
  abend: { label: 'Abendstimmung', prompt: 'Abendstimmung, warmes Licht, leuchtende Fenster' },
  'blaue-stunde': { label: 'Blaue Stunde', prompt: 'Blaue Stunde, tiefblauer Himmel, warm leuchtende Innenräume' },
  bedeckt: { label: 'Bedeckt', prompt: 'bedeckter Himmel, weiches gleichmässiges Licht' },
  nebel: { label: 'Nebel', prompt: 'Nebel, gedämpftes Licht, Tiefe im Dunst' },
  winter: { label: 'Winter', prompt: 'Winter, Schnee am Boden, kaltes klares Licht' },
  weiss: { label: 'Weissmodell', prompt: 'Weissmodell, neutrales Studiolicht, keine Materialien' },
};

/** Die Kennungen der Stimmungen in fester Reihenfolge — wie `RenderScene.render.environment.preset`. */
export const VIS_STIMMUNG_IDS = ['morgen', 'mittag', 'abend', 'blaue-stunde', 'bedeckt', 'nebel', 'winter', 'weiss'] as const;
export type VisStimmungId = (typeof VIS_STIMMUNG_IDS)[number];

export function istVisStimmung(x: unknown): x is VisStimmungId {
  return typeof x === 'string' && (VIS_STIMMUNG_IDS as readonly string[]).includes(x);
}

/** Katalog der 17 Node-Typen — deckt alle heutigen KosmoVis-Fähigkeiten (seit 21.10.2026 mit Material und Farbpalette). */
export const VIS_NODE_KATALOG: Record<string, VisNodeTyp> = {
  modell: {
    typ: 'modell',
    label: 'Modell',
    hilfe: 'Das aktuelle Projekt als GLB-Szene — der Startpunkt jedes Renders.',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'szene', typ: 'szene', label: 'Szene' }],
    defaults: {},
  },
  // Bauplan «Neue Knoten» F4 (Entscheid 111): «Material-Bausteine» heisst «Oberfläche» und ordnet
  // Materialien den Bauteil-Arten zu. Der SCHLUESSEL bleibt `material` — alte Kanten
  // `material` → `kombinierer.material` bleiben gueltig, keine Uebernahme alter Graphen noetig.
  // Die fuenf Eingaenge nehmen nur den neuen Knoten «Material» (`nurVon`); kein neuer Porttyp.
  material: {
    typ: 'material',
    label: 'Oberfläche',
    hilfe: 'Ordnet Materialien den Bauteil-Arten zu (Fassade, Dach, Fenster, Boden, Übrige); liest dazu die Wandschichten als Prompt-Phrasen.',
    kategorie: 'wandler',
    inputs: [
      { name: 'fassade', typ: 'material', label: 'Fassade', nurVon: ['materialTextur'] },
      { name: 'dach', typ: 'material', label: 'Dach', nurVon: ['materialTextur'] },
      { name: 'fenster', typ: 'material', label: 'Fenster', nurVon: ['materialTextur'] },
      { name: 'boden', typ: 'material', label: 'Boden', nurVon: ['materialTextur'] },
      { name: 'uebrige', typ: 'material', label: 'Übrige', nurVon: ['materialTextur'] },
    ],
    outputs: [{ name: 'material', typ: 'material', label: 'Material' }],
    defaults: {},
  },
  // F4 (Entscheid 111 B): ein Material der Bibliothek (Texturen CC0, ambientCG, Entscheid 107) —
  // die Karten liegen am Heim-PC, die App kennt nur die Kennung.
  materialTextur: {
    typ: 'materialTextur',
    label: 'Material',
    hilfe: 'Ein Material aus der Bibliothek (Texturen am Heim-PC) mit Massstab, Drehung und Relief — an einen Eingang der Oberfläche.',
    kategorie: 'quelle',
    inputs: [{ name: 'palette', typ: 'material', label: 'Palette', nurVon: ['farbpalette'] }],
    outputs: [{ name: 'material', typ: 'material', label: 'Material' }],
    defaults: { bibliothek: 'sichtbeton-sandgestrahlt' },
  },
  // F4 (Entscheid 111 C): tönt das angehängte Material und geht als Satz ans Bildmodell.
  farbpalette: {
    typ: 'farbpalette',
    label: 'Farbpalette',
    hilfe: 'Bis vier Farben: die gewählte tönt das Material, alle gehen als Satz ans Bildmodell.',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'palette', typ: 'material', label: 'Palette' }],
    defaults: { farben: '["#e9e2d4","#b8a58a","#6f7d6a","#3d4650"]', leitfarbe: 0, staerke: 0.4 },
  },
  prompt: {
    typ: 'prompt',
    label: 'Prompt',
    hilfe: 'Freier Stil-Text, z.B. «Sichtbeton, warmes Licht».',
    kategorie: 'wandler',
    inputs: [],
    outputs: [{ name: 'prompt', typ: 'prompt', label: 'Prompt' }],
    defaults: { text: '' },
  },
  stimmung: {
    typ: 'stimmung',
    label: 'Stimmung',
    hilfe: 'Acht Stimmungen mit Himmelsbild: Licht in Blender und Satz fürs Bildmodell. Mehrfachwahl: ein Bild je Stimmung.',
    kategorie: 'wandler',
    inputs: [],
    outputs: [{ name: 'prompt', typ: 'prompt', label: 'Prompt' }],
    defaults: { preset: 'morgen' },
  },
  kombinierer: {
    typ: 'kombinierer',
    label: 'Prompt-Kombinierer',
    hilfe: 'Fügt Stimmung + Stil + Material zum finalen Prompt — live sichtbar am Node.',
    kategorie: 'wandler',
    inputs: [
      { name: 'stimmung', typ: 'prompt', label: 'Stimmung' },
      { name: 'stil', typ: 'prompt', label: 'Stil' },
      { name: 'material', typ: 'material', label: 'Material' },
    ],
    outputs: [{ name: 'prompt', typ: 'prompt', label: 'Finaler Prompt' }],
    defaults: {},
  },
  zahl: {
    typ: 'zahl',
    label: 'Zahl',
    hilfe: 'Regler-Wert, z.B. Geometrie-Treue 0–1 oder Samples.',
    kategorie: 'wandler',
    inputs: [],
    outputs: [{ name: 'zahl', typ: 'zahl', label: 'Wert' }],
    defaults: { wert: 0.8, min: 0, max: 1, schritt: 0.05 },
  },
  render: {
    typ: 'render',
    label: 'Render',
    hilfe: 'Schickt Szene + Prompt an die HomeStation — nur auf «Ausführen», nie automatisch.',
    kategorie: 'render',
    inputs: [
      { name: 'szene', typ: 'szene', label: 'Szene' },
      { name: 'prompt', typ: 'prompt', label: 'Prompt' },
      { name: 'treue', typ: 'zahl', label: 'Geometrie-Treue' },
      { name: 'samples', typ: 'zahl', label: 'Samples' },
      { name: 'kameras', typ: 'kameras', label: 'Kamera-Standpunkte' },
      // Owner-Entscheid 96 (Visbox, 15.10.2026): die Skizze vom iPad fuehrt das Bild. Typ `bild`
      // wie der Ausgang des Skizzen-Knotens, aber nur von ihm (`nurVon`). Der Eingang steht als
      // letzter, damit die Lage der fuenf bisherigen Ports gleich bleibt; die Knotenansicht
      // zeigt ihn nur, wo ein Wirt Skizzen anbietet (Visbox), s. `NodeCanvas.tsx`.
      { name: 'skizze', typ: 'bild', label: 'Skizze', nurVon: ['skizzeIpad'] },
    ],
    outputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
    defaults: {},
  },
  kamera: {
    typ: 'kamera',
    label: 'Kamera',
    // P-DREISTANDPUNKTE (HomeStation-Befund, auftraege/von-homestation/
    // auf-orbit-20260821-01.md, Auftrag 3): der Text nannte «ggf. Innenraum»
    // ohne zu sagen, dass er nie ankommt — genau das Versprechen, das der
    // Befund beanstandet hat. `deriveAutoKameras` leitet ihn weiterhin ab
    // (bei vorhandenen Zonen), aber `postRenderJob` (vis-jobs.ts) filtert
    // ihn vor dem Senden heraus: Innenansichten sind seit P-INTERIOR
    // (ROADMAP 1071) an `interior`/IFC gebunden, dieser Weg sendet immer
    // glb. Der Zusatz macht das jetzt ehrlich, statt es nur zu verschweigen.
    //
    // KV-STARTGRAPH (14.10.2026, Visbox-Plan «Was die Knoten tun»): Seit B117
    // Schritt 2 stimmte der Zusatz nicht mehr. `istUeberDiesenWegBestellbar`
    // laesst «Innenraum» durch, sobald `interiorFaehrt(doc)` wahr ist (Zonen im
    // Dokument) — dann sendet `postRenderJob` IFC statt glb und bestellt die
    // Innenansicht mit. Der Text sagt jetzt beides, statt «nur glb» zu behaupten.
    //
    // Bauplan «Neue Knoten» F2 (Entscheide 109/113 (3), 20.10.2026): drei Arten im Parameter `art`.
    // «auto»: der Heim-PC rechnet die Standpunkte mit den Einstellungen des Knotens
    // (`cameras: 'auto'` + `cameras_auto`); «manuell»: eingefrorene Standpunkte (`kameras`, JSON);
    // ohne `art` wie bisher die Standpunkte aus dem Modell (`projektKameras`) — alte Graphen und
    // KosmoOrbit-Proben bleiben Zahl fuer Zahl.
    hilfe:
      'Standpunkte für den Render. Auto: der Heim-PC rechnet sie aus Richtungen, Augenhöhe, Brennweite und Abstand. Blick: ein gesicherter Blick. Manuell: eingefroren und von Hand gestellt. Ohne Wahl: Eingang/Übersicht aus dem Modell (bei Räumen auch Innenraum, dann als IFC).',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'kameras', typ: 'kameras', label: 'Kamera-Standpunkte' }],
    // Integrator-Folgeauftrag (21.10.2026, Entscheid 113 (3)): NEU angelegte Kamera-Knoten stehen auf
    // «Auto» (der Heim-PC rechnet). `defaults` gelten nur beim Anlegen (`vis.nodeSetzen`) — ein
    // gespeicherter Knoten ohne `art` bleibt «Modell» und wird nie still umgestellt.
    defaults: { art: 'auto' },
  },
  vergleich: {
    typ: 'vergleich',
    label: 'Bildvergleich',
    hilfe: 'Bilder nebeneinander mit QA-Verdikt — die heutige Varianten-Serie als Node.',
    kategorie: 'ausgabe',
    inputs: [
      { name: 'bild1', typ: 'bild', label: 'Bild 1' },
      { name: 'bild2', typ: 'bild', label: 'Bild 2' },
      { name: 'bild3', typ: 'bild', label: 'Bild 3' },
    ],
    outputs: [],
    defaults: {},
  },
  blatt: {
    typ: 'blatt',
    label: 'Aufs Blatt',
    hilfe: 'Legt das Bild als Blatt-Bürger in KosmoPublish ab (ein Undo-Schritt).',
    kategorie: 'ausgabe',
    inputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
    outputs: [],
    defaults: { titel: 'Visualisierung' },
  },
  referenz: {
    typ: 'referenz',
    label: 'Bild-Referenz',
    hilfe: 'Referenzbild oder Splat-Ansicht als Bild-Quelle (Stil-Referenz, Vergleich).',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
    defaults: { url: '' },
  },
  // Owner-Entscheide 95/95a (14.10.2026, Blatt 25 der Visbox): die Skizzen, die man am iPad in
  // die Mappe legt, kommen als Zulieferer in die Knotenansicht. Welche es gibt, weiss nur der
  // WIRT (`registriereSkizzenQuelle`, App `modules/vis/skizze-quelle.ts`) — der Katalog kennt
  // nur den Porttyp. `skizze` ist «neueste» (Vorgabe: von selbst die zuletzt gelegte) oder der
  // Dateiname einer älteren. Seit Entscheid 96 (15.10.2026) geht der Ausgang auch an den Eingang
  // «Skizze» des Render-Knotens und fuehrt dort das Bild; daneben in Bildvergleich und «Aufs Blatt».
  skizzeIpad: {
    typ: 'skizzeIpad',
    label: 'Skizze vom iPad',
    hilfe:
      'Die Skizze, die am iPad in die Mappe gelegt wurde — von selbst die neueste, eine ältere ist am Knoten wählbar. An «Skizze» des Render-Knotens: die Skizze führt das Bild — ihre Bemerkung ist die Anweisung, und es entsteht vom Standpunkt des Bildes, auf das gezeichnet wurde. Auch an Bildvergleich und «Aufs Blatt». Gibt es nur in Visbox.',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
    defaults: { skizze: 'neueste' },
  },
  aufnahme: {
    typ: 'aufnahme',
    label: 'Viewport-Aufnahme',
    hilfe:
      'Echte lokale Bildquelle: ein Schnappschuss des 3D-Viewports («Für Vis aufnehmen» in KosmoDesign) — kein Rendering, funktioniert ohne HomeStation.',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
    // kamera: rein dokumentarisch, welcher Standpunkt gemeint ist — der
    // Viewport-Knopf selbst bewegt/wählt keine Kamera (kein Renderloop-
    // Eingriff), er nimmt IMMER den aktuellen Viewport-Stand auf.
    defaults: { kamera: 'aktuell' },
  },
  // Owner-Entscheid 14.10.2026 (über die Zentrale): die Knotenansicht ist die einzige
  // Arbeitsfläche zum Rendern; die 3D-Ansicht liefert ihren Blick hierher zu. Die Kamera liegt
  // als Parameter im Knoten (`derive/kamera-aus-3d.ts`), gesetzt beim Anlegen und auf
  // «Kamera übernehmen» — darum keine `defaults`: ohne Übernahme trägt er keine Kamera.
  [KAMERA_AUS_3D_TYP]: {
    typ: KAMERA_AUS_3D_TYP,
    label: 'Kamera aus 3D-Ansicht',
    hilfe:
      'Übernimmt den Blick, den du in der 3D-Ansicht eingestellt hast — beim Anlegen und auf «Kamera übernehmen», nicht laufend. Mit dem Render-Knoten verbinden. Ohne Objektiv-Shift.',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'kameras', typ: 'kameras', label: 'Kamera-Standpunkte' }],
    defaults: {},
  },
  // «Varianten mit einem Klick» (Owner-Entscheide 92/92a/92b der Visbox, Blatt 23; L24 Bildweg
  // Varianten, E246): haengt hinter einem Render-Knoten und bestellt dessen Einstellung fuer alle
  // Kombinationen aus Standpunkten, Stimmungen und Entwuerfen (`derive/varianten.ts`). Die drei
  // Achsen stehen als Parameter im Knoten (Listen als JSON-Text); leer heisst «nichts gewaehlt»,
  // dann gilt die Vorgabe 3 × Abend × aktuelles Modell (92a). Der Ausgang geht in den Bildvergleich,
  // der die Bilder dann als Raster zeigt.
  [VARIANTEN_TYP]: {
    typ: VARIANTEN_TYP,
    label: 'Varianten',
    hilfe:
      'Bestellt die Einstellung des Render-Knotens in allen Kombinationen aus Standpunkten, Stimmungen und Entwürfen — mit Zähler, eine Freigabe für alle. Hinter den Render-Knoten hängen, den Ausgang in den Bildvergleich (Raster).',
    kategorie: 'render',
    inputs: [{ name: 'render', typ: 'bild', label: 'Render' }],
    outputs: [{ name: 'bilder', typ: 'bild', label: 'Bilder' }],
    defaults: { standpunkte: '', stimmungen: '', entwuerfe: '' },
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Bauplan «Neue Knoten» (Schritt K, 21.10.2026): Stimmung, Kamera, Oberfläche/Material/
// Farbpalette. Reine Lesefunktionen ueber die Knoten-Parameter — dieselben fuer Auswertung,
// Knoten-Koerper und Kosmo. Listen stehen als JSON-Text in den Parametern (wie `varianten`).
// ─────────────────────────────────────────────────────────────────────────────

type Params = VisNode['params'] | undefined;

/** Worauf eine Stimmung wirkt (Entscheid 110 A): Himmelsbild in Blender, Satz fuers Bildmodell, oder beides. */
export type StimmungWirkung = 'licht+prompt' | 'licht' | 'prompt';
export const STIMMUNG_WIRKUNGEN: readonly StimmungWirkung[] = ['licht+prompt', 'licht', 'prompt'];

export interface StimmungWahl {
  /** Gewaehlte Stimmungen in Katalog-Reihenfolge, mindestens eine. Die erste fuehrt den Render-Knoten. */
  presets: VisStimmungId[];
  /** Drehung des Himmels um die Hochachse in Grad [0, 360). Fehlt: der Heim-PC dreht zur Kamera. */
  drehungGrad?: number;
  wirkung: StimmungWirkung;
}

/**
 * Die Wahl am Stimmung-Knoten. Zuerst die Liste `presets` (Mehrfachwahl, Entscheid 113 (4)), sonst
 * der alte Einzelwert `preset` (alte Graphen), sonst Morgen. Unbekanntes faellt still heraus.
 */
export function stimmungAusParams(params: Params): StimmungWahl {
  const p = params ?? {};
  const liste = liesListe(p['presets']);
  const roh = liste ?? (typeof p['preset'] === 'string' ? [p['preset']] : []);
  const presets = VIS_STIMMUNG_IDS.filter((id) => roh.includes(id));
  const d = p['drehung'];
  const wirkungRoh = p['wirkung'];
  const wirkung = STIMMUNG_WIRKUNGEN.includes(wirkungRoh as StimmungWirkung) ? (wirkungRoh as StimmungWirkung) : 'licht+prompt';
  return {
    presets: presets.length > 0 ? presets : ['morgen'],
    ...(typeof d === 'number' && Number.isFinite(d) ? { drehungGrad: ((Math.round(d) % 360) + 360) % 360 } : {}),
    wirkung,
  };
}

/** Parameter, die eine neue Stimmungs-Wahl schreibt — Liste UND erster Wert (fuer alte Leser). */
export function stimmungParams(presets: readonly VisStimmungId[]): { presets: string; preset: string } {
  const geordnet = VIS_STIMMUNG_IDS.filter((id) => presets.includes(id));
  const liste = geordnet.length > 0 ? geordnet : (['morgen'] as VisStimmungId[]);
  return { presets: schreibeListe(liste), preset: liste[0]! };
}

/**
 * Kamera-Arten im Parameter `art` (s. Katalog `kamera`). Ohne `art`: «modell» (wie bisher).
 * «blick» (Video-Befund L4-4, 21.10.2026): ein gesicherter Blick ist die Kamera — s. `kameraBlickAusParams`.
 */
export type KameraArt = 'modell' | 'auto' | 'manuell' | 'blick';

/** Die acht Richtungen am Knoten und ihre Kuerzel am Heim-PC (`aiimaging.kameras.RICHTUNGEN`). */
export const KAMERA_RICHTUNGEN: readonly { chip: string; kuerzel: string; name: string }[] = [
  { chip: 'N', kuerzel: 'n', name: 'Nord' },
  { chip: 'NO', kuerzel: 'nNE', name: 'Nordost' },
  { chip: 'O', kuerzel: 'e', name: 'Ost' },
  { chip: 'SO', kuerzel: 'sSE', name: 'Südost' },
  { chip: 'S', kuerzel: 's', name: 'Süd' },
  { chip: 'SW', kuerzel: 'sSW', name: 'Südwest' },
  { chip: 'W', kuerzel: 'w', name: 'West' },
  { chip: 'NW', kuerzel: 'nNW', name: 'Nordwest' },
];

/** Die Vorgaben des Heim-PCs (Entscheide 109 C, 113 (5)): gezeigt, wenn am Knoten nichts steht. */
export const KAMERA_AUTO_VORGABEN = {
  richtungen: ['s', 'sSE', 'nNW'] as readonly string[],
  augenhoehe_m: 1.7,
  brennweite_mm: 35 as 24 | 35 | 50,
  fuellt: 0.7,
  perspektive: 'senkrecht' as 'senkrecht' | 'frei',
};

export const KAMERA_BRENNWEITEN = [24, 35, 50] as const;

/** Was der Knoten «Kamera» im Modus Auto bestellt — die Form von `RenderScene.cameras_auto`. */
export interface KameraAutoWahl {
  richtungen: string[];
  augenhoehe_m?: number;
  brennweite_mm?: 24 | 35 | 50;
  abstand?: { art: 'auto'; fuellt?: number } | { art: 'fest'; meter: number };
  perspektive?: 'senkrecht' | 'frei';
}

export function kameraArtAusParams(params: Params): KameraArt {
  const a = params?.['art'];
  return a === 'auto' || a === 'manuell' || a === 'blick' ? a : 'modell';
}

function zahlIn(wert: unknown, min: number, max: number): number | undefined {
  return typeof wert === 'number' && Number.isFinite(wert) && wert >= min && wert <= max ? wert : undefined;
}

/**
 * Die Einstellungen der Auto-Kamera. Nur, was am Knoten steht, geht mit — den Rest setzt der
 * Heim-PC (`KAMERA_AUTO_VORGABEN`) und nennt ihn im Ergebnis. Richtungen sind Pflicht im Vertrag:
 * ohne Wahl gelten die drei der Vorgabe.
 */
export function kameraAutoAusParams(params: Params): KameraAutoWahl {
  const p = params ?? {};
  const bekannt = KAMERA_RICHTUNGEN.map((r) => r.kuerzel);
  const gewaehlt = (liesListe(p['richtungen']) ?? []).filter((r) => bekannt.includes(r));
  const richtungen = gewaehlt.length > 0 ? bekannt.filter((r) => gewaehlt.includes(r)) : [...KAMERA_AUTO_VORGABEN.richtungen];
  const auge = zahlIn(p['augenhoehe'], 0.5, 50);
  const bw = p['brennweite'];
  const brennweite = bw === 24 || bw === 35 || bw === 50 ? bw : undefined;
  const fuellt = zahlIn(p['fuellt'], 0.2, 0.95);
  const meter = zahlIn(p['abstandM'], 2, 2000);
  const abstand: KameraAutoWahl['abstand'] =
    p['abstandArt'] === 'fest' && meter !== undefined
      ? { art: 'fest', meter }
      : fuellt !== undefined
        ? { art: 'auto', fuellt }
        : undefined;
  const persp = p['perspektive'];
  return {
    richtungen: richtungen.slice(0, 8),
    ...(auge !== undefined ? { augenhoehe_m: auge } : {}),
    ...(brennweite !== undefined ? { brennweite_mm: brennweite } : {}),
    ...(abstand ? { abstand } : {}),
    ...(persp === 'senkrecht' || persp === 'frei' ? { perspektive: persp } : {}),
  };
}

/** Waagrechter Bildwinkel aus der Brennweite (Kleinbild, 36 mm breit — wie Blender). */
export function fovAusBrennweiteGrad(brennweiteMm: number): number {
  return (2 * Math.atan(36 / (2 * brennweiteMm)) * 180) / Math.PI;
}

/** Ein eingefrorener Standpunkt am Knoten (Modus Manuell), glTF-Achsen (Y oben, Meter). */
export interface KameraManuell {
  name: string;
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
}

function istVec3(v: unknown): v is [number, number, number] {
  return Array.isArray(v) && v.length === 3 && v.every((x) => typeof x === 'number' && Number.isFinite(x));
}

/** Die eingefrorenen Standpunkte (Parameter `kameras`, JSON). Unlesbares faellt heraus. */
export function kameraManuellAusParams(params: Params): KameraManuell[] {
  const roh = params?.['kameras'];
  if (typeof roh !== 'string' || roh.trim() === '') return [];
  try {
    const liste: unknown = JSON.parse(roh);
    if (!Array.isArray(liste)) return [];
    return liste.flatMap((k): KameraManuell[] => {
      if (!k || typeof k !== 'object') return [];
      const o = k as Record<string, unknown>;
      const fov = zahlIn(o['fov'], 10, 120);
      if (!istVec3(o['position']) || !istVec3(o['target']) || fov === undefined) return [];
      return [{ name: typeof o['name'] === 'string' && o['name'] ? o['name'] : 'Kamera', position: o['position'], target: o['target'], fov }];
    });
  } catch {
    return [];
  }
}

/**
 * **Gesicherter Blick als Kamera** (Video-Befund L4-4, 21.10.2026, Blatt «Blick zur Kamera»).
 *
 * Bis dahin kam ein gesicherter Blick (`design.blickSichern`) nur über «Kamera aus 3D-Ansicht» in
 * den Graphen — und der verlangt eine offene 3D-Ansicht. Jetzt wählt man ihn direkt am Knoten
 * «Kamera» (`art: 'blick'`). Parameter:
 *
 *  - `blickId`: die Kennung des gesicherten Blicks (`GespeicherterBlick.id`; in Visbox die des
 *    Wirts) — sie hält die Verbindung, auch wenn der Blick umbenannt wird (KosmoDraw, v0.1.10);
 *  - `blick`: der Name beim Wählen — nur Anzeige-Rückfall, wenn die Kennung keinen Blick mehr findet;
 *  - `blickKamera`: Auge, Blickpunkt und waagrechter Bildwinkel, beim Wählen FESTGEHALTEN (JSON,
 *    glTF-Achsen, Meter — wie `kameras` bei «manuell»). Die Grundlage bleibt so ruhig, auch wenn
 *    der Blick später verschoben oder gelöscht wird (Blatt, Frage A).
 *
 * Fehlt `blickKamera` (ein Aufruf von aussen), gilt der gesicherte Blick des Dokuments mit dieser
 * `blickId`, sonst der EINZIGE mit diesem Namen (bei zwei gleichnamigen keiner). Gibt es weder das eine noch das andere: `null` — der
 * Render-Auftrag traegt dann `kameraBlickFehlt`, und die App sendet nicht.
 */
export interface KameraBlick {
  name: string;
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
}

function fovImVertrag(fov: unknown): fov is number {
  return typeof fov === 'number' && Number.isFinite(fov) && fov >= FOV_GRENZEN_GRAD[0] && fov <= FOV_GRENZEN_GRAD[1];
}

/** Der Name des gewählten Blicks (`blick`), leer ohne Wahl. */
export function kameraBlickName(params: Params): string {
  const n = params?.['blick'];
  return typeof n === 'string' ? n.trim() : '';
}

/** Die Kennung des gewählten Blicks (`blickId`), leer ohne Wahl. */
export function kameraBlickId(params: Params): string {
  const n = params?.['blickId'];
  return typeof n === 'string' ? n.trim() : '';
}

export function kameraBlickAusParams(params: Params, doc?: KosmoDoc): KameraBlick | null {
  const name = kameraBlickName(params);
  const roh = params?.['blickKamera'];
  if (typeof roh === 'string' && roh.trim() !== '') {
    try {
      const o: unknown = JSON.parse(roh);
      if (o && typeof o === 'object') {
        const k = o as Record<string, unknown>;
        if (istVec3(k['position']) && istVec3(k['target']) && fovImVertrag(k['fov'])) {
          return { name: name || 'Blick', position: k['position'], target: k['target'], fov: k['fov'] };
        }
      }
    } catch {
      // unlesbar: wie fehlend
    }
  }
  const id = kameraBlickId(params);
  if ((!name && !id) || !doc) return null;
  const alle = doc.settings.gespeicherteBlicke ?? [];
  const gleichnamig = alle.filter((x) => x.name === name);
  const b = id ? alle.find((x) => x.id === id) : gleichnamig.length === 1 ? gleichnamig[0] : undefined;
  if (!b || !fovImVertrag(b.fovGrad)) return null;
  return {
    name: b.name,
    position: [b.position[0], b.position[1], b.position[2]],
    target: [b.ziel[0], b.ziel[1], b.ziel[2]],
    fov: b.fovGrad,
  };
}

/** Die Bauteil-Arten der Oberflaeche (Visbox `materialwahl.ARTEN`); Tueren zaehlen zu «Übrige» (113 (7)). */
export const VIS_BAUTEIL_ARTEN: readonly { art: 'fassade' | 'dach' | 'fenster' | 'boden' | 'uebrige'; label: string }[] = [
  { art: 'fassade', label: 'Fassade' },
  { art: 'dach', label: 'Dach' },
  { art: 'fenster', label: 'Fenster' },
  { art: 'boden', label: 'Boden' },
  { art: 'uebrige', label: 'Übrige' },
];

/**
 * Die Material-Bibliothek (Entscheid 111, Tabelle der HomeStation vom 20.10.2026) — dieselben elf
 * Kennungen wie `aiimaging.materialwahl.BIBLIOTHEK` (Visbox-Probe haelt beide gleich). Die Texturen
 * (CC0, ambientCG) liegen nur am Heim-PC; `farbe` ist der Grundton fuer die Vorschau am Knoten,
 * solange keine Vorschaubilder ausgeliefert sind.
 */
export const VIS_MATERIAL_BIBLIOTHEK: readonly { id: string; label: string; farbe: string }[] = [
  { id: 'sichtbeton-sandgestrahlt', label: 'Sichtbeton, sandgestrahlt', farbe: '#b9b6b0' },
  { id: 'sichtbeton-schalungsglatt', label: 'Sichtbeton, schalungsglatt', farbe: '#c8c5bf' },
  { id: 'fichte', label: 'Fichte', farbe: '#d9b98a' },
  { id: 'backstein', label: 'Backstein', farbe: '#a8553a' },
  { id: 'klinker', label: 'Klinker', farbe: '#7a3b2a' },
  { id: 'sandstein', label: 'Sandstein', farbe: '#cdb58a' },
  { id: 'stampflehm', label: 'Stampflehm', farbe: '#a88660' },
  { id: 'verputz-weiss-glatt', label: 'Verputz weiss, glatt', farbe: '#f2f0ec' },
  { id: 'verputz-weiss-rau', label: 'Verputz weiss, rau', farbe: '#e8e5df' },
  { id: 'holzlattung-fichte', label: 'Holzlattung Fichte', farbe: '#cfa874' },
  { id: 'dreischichtplatte', label: 'Dreischichtplatte', farbe: '#dcc49a' },
];

/** Die Vorgaben des Heim-PCs, wenn am Material nichts steht (`materialwahl.VORGABE_*`). */
export const MATERIAL_VORGABEN = { massstab_m: 1, drehungGrad: 0, relief: 0.6 } as const;

/** Was eine Bauteil-Art bestellt — die Form von `RenderScene.render.materialien.<art>`. */
export interface MaterialWahlAuftrag {
  id: string;
  massstab_m?: number;
  drehungGrad?: number;
  relief?: number;
  toenung?: { farbe: string; staerke: number };
}

export interface PaletteWahl {
  farben: string[];
  leitfarbe: number;
  staerke: number;
}

const FARBE = /^#[0-9a-fA-F]{6}$/;

/** Die Farbpalette am Knoten: bis vier Farben, die gewaehlte (Leitfarbe) toent, Staerke 0..1. */
export function paletteAusParams(params: Params): PaletteWahl {
  const p = params ?? {};
  const farben = (liesListe(p['farben']) ?? []).filter((f) => FARBE.test(f)).slice(0, 4);
  const leit = typeof p['leitfarbe'] === 'number' && Number.isInteger(p['leitfarbe']) ? p['leitfarbe'] : 0;
  const staerke = zahlIn(p['staerke'], 0, 1) ?? 0.4;
  return { farben, leitfarbe: Math.min(Math.max(0, leit), Math.max(0, farben.length - 1)), staerke };
}

/** Ein Farbwort fuer einen Menschen und das Bildmodell — grob nach Farbton, Helligkeit, Saettigung. */
export function farbWort(hex: string): string {
  if (!FARBE.test(hex)) return hex;
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  const d = max - min;
  const sat = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  let h = 0;
  if (d !== 0) {
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h = (h * 60 + 360) % 360;
  }
  const hell = l > 0.8 ? 'helles ' : l < 0.3 ? 'dunkles ' : '';
  if (sat < 0.12) return l > 0.85 ? 'Weiss' : l < 0.15 ? 'Schwarz' : `${hell}Grau`.replace(/^./, (c) => c.toUpperCase());
  const ton =
    h < 15 || h >= 345 ? 'Rot' : h < 40 ? (sat < 0.45 ? 'Sand' : 'Orange') : h < 65 ? (sat < 0.45 ? 'Beige' : 'Gelb') : h < 160 ? (sat < 0.3 ? 'Salbeigrün' : 'Grün') : h < 200 ? 'Türkis' : h < 255 ? (sat < 0.3 ? 'Schiefergrau' : 'Blau') : h < 300 ? 'Violett' : 'Rosa';
  return `${hell}${ton}`.replace(/^./, (c) => c.toUpperCase());
}

/** Der Satz der Palette fuer das Bildmodell (Entscheid 111 C). Leer ohne Farben. */
export function paletteSatz(farben: readonly string[]): string {
  return farben.length > 0 ? `Farbpalette: ${farben.map(farbWort).join(', ')}` : '';
}

/** Das Material am Knoten «Material» (Typ `materialTextur`), samt Toenung aus einer Palette. */
export function materialAusParams(params: Params, palette?: PaletteWahl): MaterialWahlAuftrag | null {
  const p = params ?? {};
  const id = p['bibliothek'];
  if (typeof id !== 'string' || !VIS_MATERIAL_BIBLIOTHEK.some((m) => m.id === id)) return null;
  const massstab = zahlIn(p['massstab'], 0.05, 20);
  const drehung = zahlIn(p['drehung'], 0, 360);
  const relief = zahlIn(p['relief'], 0, 1);
  const farbe = palette?.farben[palette.leitfarbe];
  return {
    id,
    ...(massstab !== undefined ? { massstab_m: massstab } : {}),
    ...(drehung !== undefined ? { drehungGrad: drehung } : {}),
    ...(relief !== undefined ? { relief } : {}),
    ...(farbe && palette && palette.staerke > 0 ? { toenung: { farbe, staerke: palette.staerke } } : {}),
  };
}

/** Die erste Quelle eines Eingangs. */
function quelleAm(graph: VisGraph, nodeId: string, port: string): VisNode | undefined {
  const e = graph.edges.find((k) => k.to === nodeId && k.toPort === port);
  return e ? graph.nodes.find((n) => n.id === e.from) : undefined;
}

/** Die Materialwahl eines Oberflaeche-Knotens: je verbundene Art ein Material. Leer: `null`. */
export function oberflaecheMaterialien(graph: VisGraph, oberflaecheId: string): Partial<Record<string, MaterialWahlAuftrag>> | null {
  const aus: Partial<Record<string, MaterialWahlAuftrag>> = {};
  for (const { art } of VIS_BAUTEIL_ARTEN) {
    const m = quelleAm(graph, oberflaecheId, art);
    if (m?.typ !== 'materialTextur') continue;
    const pal = quelleAm(graph, m.id, 'palette');
    const wahl = materialAusParams(m.params, pal?.typ === 'farbpalette' ? paletteAusParams(pal.params) : undefined);
    if (wahl) aus[art] = wahl;
  }
  return Object.keys(aus).length > 0 ? aus : null;
}

/** Die Knoten einer Art, die (mittelbar) in den Render-Knoten fliessen — in Graph-Reihenfolge. */
export function vorgeschaltet(graph: VisGraph, renderId: string, typ: string): VisNode[] {
  const davor = vorfahren(graph, renderId);
  return graph.nodes.filter((n) => n.typ === typ && davor.has(n.id));
}

export function visPort(typ: string, port: string, richtung: 'in' | 'out'): VisPort | undefined {
  const kat = VIS_NODE_KATALOG[typ];
  if (!kat) return undefined;
  return (richtung === 'in' ? kat.inputs : kat.outputs).find((p) => p.name === port);
}

/** Prüft, ob der Graph (optional mit einer Zusatzkante) einen Zyklus hätte. */
export function hatZyklus(nodes: VisNode[], edges: VisEdge[], extra?: Pick<VisEdge, 'from' | 'to'>): boolean {
  const alle = extra ? [...edges, { ...extra, id: '', fromPort: '', toPort: '' }] : edges;
  const nach = new Map<string, string[]>();
  for (const e of alle) nach.set(e.from, [...(nach.get(e.from) ?? []), e.to]);
  const farbe = new Map<string, 1 | 2>(); // 1 = auf dem Pfad, 2 = fertig
  const besuch = (id: string): boolean => {
    if (farbe.get(id) === 1) return true;
    if (farbe.get(id) === 2) return false;
    farbe.set(id, 1);
    for (const n of nach.get(id) ?? []) if (besuch(n)) return true;
    farbe.set(id, 2);
    return false;
  };
  return nodes.some((n) => besuch(n.id));
}

/**
 * Topologische Reihenfolge (Kahn). Robust gegen kaputte Stände: hängende
 * Kanten (Sync-Merge löschte einen Node) werden ignoriert, und bei einem
 * Zyklus in Fremddaten fallen nur die Zyklus-Nodes aus der Folge —
 * nie ein Absturz, nie eine Endlosschleife.
 */
export function topoReihenfolge(graph: VisGraph): VisNode[] {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const kanten = graph.edges.filter((e) => byId.has(e.from) && byId.has(e.to));
  const eingang = new Map<string, number>(graph.nodes.map((n) => [n.id, 0]));
  for (const e of kanten) eingang.set(e.to, (eingang.get(e.to) ?? 0) + 1);
  const frei = graph.nodes.filter((n) => (eingang.get(n.id) ?? 0) === 0);
  const folge: VisNode[] = [];
  while (frei.length > 0) {
    const n = frei.shift()!;
    folge.push(n);
    for (const e of kanten.filter((e) => e.from === n.id)) {
      const rest = (eingang.get(e.to) ?? 0) - 1;
      eingang.set(e.to, rest);
      if (rest === 0) frei.push(byId.get(e.to)!);
    }
  }
  return folge;
}

/**
 * Fertig zusammengezogene Job-Parameter eines Render-Nodes. `presetId`/
 * `resolution`/`sun`/`komposition` (Owner-Befund K20/A10) erscheinen NUR, wenn
 * der Node-Param `preset` gesetzt ist — ohne Preset bleibt das Verhalten
 * byte-identisch zum bisherigen Stand (Default-Samples 128 etc.). `kameras`
 * erscheint NUR, wenn ein Auto-Kamera-Node am `kameras`-Port hängt.
 */
export interface VisRenderAuftrag {
  prompt: string;
  faithful: number;
  samples: number;
  hatSzene: boolean;
  nurCycles: boolean;
  presetId?: VisPresetId;
  resolution?: readonly [number, number];
  sun?: { azimuth: number; elevation: number };
  komposition?: { seitenverhaeltnis: number; brennweiteMm: number; horizontlinie: number };
  kameras?: AutoKameraStandpunkt[];
  /**
   * Am Eingang «Kamera-Standpunkte» hängt «Kamera aus 3D-Ansicht», aber der Knoten trägt noch
   * keine Kamera. Die App sendet dann NICHT (sonst rechnete die Gegenseite still ihre eigenen
   * Standpunkte, also ein anderes Bild als bestellt). Fehlt das Feld, ist alles wie bisher.
   */
  kameraAus3dFehlt?: true;
  /**
   * Der Knoten «Kamera» steht auf «Blick», aber es ist keiner gewählt (oder der Name ist keinem
   * gesicherten Blick mehr zugeordnet und nichts festgehalten). Die App sendet dann NICHT — wie
   * bei `kameraAus3dFehlt`, aus demselben Grund. Fehlt das Feld, ist alles wie bisher.
   */
  kameraBlickFehlt?: true;
  /**
   * Owner-Entscheid 96 (Visbox, 15.10.2026): haengt eine «Skizze vom iPad» am Eingang «Skizze»,
   * steht hier ihre WAHL (Parameter `skizze`: «neueste» oder ein Dateiname) und ihr Knoten.
   * Welche Datei «neueste» ist, weiss nur der Wirt — aufgeloest wird in der App
   * (`skizze-quelle.ts`), nicht hier. Ohne Kante fehlt das Feld ganz.
   */
  skizze?: { knoten: string; wahl: string };
  /**
   * Bauplan «Neue Knoten» F3 (Entscheid 110): die Stimmung aus dem vorgeschalteten Stimmung-Knoten,
   * wenn sie aufs Licht wirkt — wird `render.environment`. Fehlt `rotationGrad`, dreht der Heim-PC
   * den Himmel zur Kamera. Ohne Stimmung-Knoten fehlt das Feld (wie bisher).
   */
  umgebung?: { preset: VisStimmungId; rotationGrad?: number };
  /** F3 (113 (4)): alle am Stimmung-Knoten gewaehlten Stimmungen — die erste fuehrt (`umgebung`). */
  stimmungen?: VisStimmungId[];
  /** F2 (109/113 (3)): Auto-Kamera am Eingang — wird `cameras: 'auto'` + `cameras_auto`. */
  kamerasAuto?: KameraAutoWahl;
  /** F2: Perspektive der von Hand gestellten Standpunkte (`CameraSpec.perspektive`). */
  kamerasPerspektive?: 'senkrecht' | 'frei';
  /** F4 (111): Materialien je Bauteil-Art aus dem vorgeschalteten Oberflaeche-Knoten. */
  materialien?: Partial<Record<string, MaterialWahlAuftrag>>;
}

/** Auswertungs-Ergebnis je Node: Ausgangswerte der puren Ports. */
export interface VisAuswertung {
  /** nodeId → Portname → Wert (string für prompt/material, number für zahl). */
  werte: Map<string, Record<string, string | number>>;
  /** Für Render-Nodes: die fertig zusammengezogenen Job-Parameter. */
  renderAuftraege: Map<string, VisRenderAuftrag>;
}

/**
 * Pull-basierte Auswertung der puren Nodes. Bild-Ports tragen keine Werte
 * (Laufzeit-Sache der App); Render-Nodes bekommen ihre Auftragsparameter
 * mit ehrlichen Defaults (treue 0.8, samples 128), wenn nichts verbunden ist.
 */
export function evaluiereGraph(doc: KosmoDoc, graph: VisGraph): VisAuswertung {
  const werte = new Map<string, Record<string, string | number>>();
  const renderAuftraege = new Map<string, VisRenderAuftrag>();
  const eingangsWert = (nodeId: string, port: string): string | number | undefined => {
    const e = graph.edges.find((e) => e.to === nodeId && e.toPort === port);
    if (!e) return undefined;
    return werte.get(e.from)?.[e.fromPort];
  };
  for (const n of topoReihenfolge(graph)) {
    // Härtetest H4c: ein Node OHNE `params` (Hand-Edit/Fremd-Tool-Import,
    // Yjs-Merge von einem anderen Stand) darf die Auswertung nie reissen —
    // fehlende Parameter zählen wie leere/Default-Werte.
    const params = n.params ?? {};
    switch (n.typ) {
      case 'prompt':
        werte.set(n.id, { prompt: String(params['text'] ?? '') });
        break;
      case 'stimmung': {
        // F3: die erste gewaehlte Stimmung fuehrt; ihr Satz geht in den Prompt, wenn sie auf den
        // Prompt wirkt (Entscheid 110 A). Alte Graphen (nur `preset`) rechnen wie bisher.
        const wahl = stimmungAusParams(params);
        werte.set(n.id, { prompt: wahl.wirkung === 'licht' ? '' : (VIS_STIMMUNGEN[wahl.presets[0]!]?.prompt ?? '') });
        break;
      }
      case 'material': {
        // F4: die Wandschichten wie bisher, dazu der Satz einer Farbpalette an einem der Materialien
        // (Entscheid 111 C). Die Materialien selbst nennt der Heim-PC im Prompt (`materialwahl.prompt_satz`).
        const saetze = new Set<string>();
        for (const { art } of VIS_BAUTEIL_ARTEN) {
          const m = quelleAm(graph, n.id, art);
          const pal = m?.typ === 'materialTextur' ? quelleAm(graph, m.id, 'palette') : undefined;
          if (pal?.typ === 'farbpalette') {
            const satz = paletteSatz(paletteAusParams(pal.params).farben);
            if (satz) saetze.add(satz);
          }
        }
        werte.set(n.id, { material: [...renderPromptBausteine(doc), ...saetze].join(', ') });
        break;
      }
      case 'farbpalette':
        werte.set(n.id, { palette: paletteSatz(paletteAusParams(params).farben) });
        break;
      case 'materialTextur': {
        const m = VIS_MATERIAL_BIBLIOTHEK.find((x) => x.id === params['bibliothek']);
        werte.set(n.id, { material: m?.label ?? '' });
        break;
      }
      case 'zahl':
        werte.set(n.id, { zahl: Number(params['wert'] ?? 0) });
        break;
      case 'kombinierer': {
        const stimmung = String(eingangsWert(n.id, 'stimmung') ?? '');
        const stil = String(eingangsWert(n.id, 'stil') ?? '');
        const material = String(eingangsWert(n.id, 'material') ?? '');
        const prompt = finalerRenderPrompt(stimmung, stil, material ? [material] : []);
        werte.set(n.id, { prompt });
        break;
      }
      case 'render': {
        const prompt = String(eingangsWert(n.id, 'prompt') ?? '');
        const treue = eingangsWert(n.id, 'treue');
        const samples = eingangsWert(n.id, 'samples');
        // K20/A10: Cycles-Preset ist ein Node-Param (wie `stimmung.preset`),
        // NUR wirksam wenn explizit gesetzt — ohne Preset bleibt der
        // 128-Samples-Default (unten) byte-identisch zum bisherigen Stand.
        const presetRoh = params['preset'];
        const presetId = isVisPresetId(presetRoh) ? presetRoh : undefined;
        const preset = presetId ? visPresetById(presetId) : undefined;
        // Ein Auto-Kamera-Node am `kameras`-Port liefert Standpunkte live aus
        // den aktuellen Modell-Bounds — wie `material` ist das eine reine
        // Ableitung, nie ein gespeicherter Wert (immer aktuell).
        //
        // 12.09.2026: `projektKameras` statt `deriveAutoKameras`. Es ist
        // dieselbe Ableitung, VORAN gestellt sind nur die von Hand gesetzten,
        // aus einer 3DS-Datei übernommenen Standpunkte
        // (`doc.settings.uebernommeneKameras`, s. `derive/kamera.ts`). Ohne
        // diese eine Zeile wäre die übernommene Kamera zwar im Dokument, aber
        // in keinem Auftrag — genau die Klasse «gebaut und nicht bestellt».
        // Hat das Projekt keine übernommene Kamera (der Normalfall und jeder
        // bestehende Golden-Fall), liefert `projektKameras` Zahl für Zahl
        // dasselbe wie zuvor.
        const kameraKante = graph.edges.find((e) => e.to === n.id && e.toPort === 'kameras');
        const kameraQuelle = kameraKante ? graph.nodes.find((q) => q.id === kameraKante.from) : undefined;
        // «Kamera aus 3D-Ansicht» (14.10.2026): hängt DIESER Knoten am Eingang, gilt seine
        // gespeicherte Kamera — und nur sie, nicht die Auto-Standpunkte. Das Blickfeld wird
        // horizontal für das Bestellformat gerechnet (Voreinstellung, sonst die Vorgabe von
        // `postRenderJob`); eine am Knoten gewählte Auflösung rechnet `postRenderJob` nach.
        // Ohne übernommene Kamera: keine Standpunkte und `kameraAus3dFehlt` — die App sendet
        // dann nicht (eine Bestellung mit `auto` wäre ein anderes Bild als versprochen).
        const kamera3d = kameraQuelle?.typ === KAMERA_AUS_3D_TYP ? kameraAus3dAusParams(kameraQuelle.params) : null;
        // F2 (Entscheide 109/113 (3)): der Knoten «Kamera» mit `art` — «auto» schickt keine Liste,
        // sondern seine Einstellungen (der Heim-PC rechnet), «manuell» die eingefrorenen Standpunkte.
        const kameraArt = kameraQuelle?.typ === 'kamera' ? kameraArtAusParams(kameraQuelle.params) : 'modell';
        const kameraParams = kameraQuelle?.params ?? {};
        // L4-4: «blick» — der gewählte gesicherte Blick, als EIN fester Standpunkt (wie «manuell»).
        const kameraBlick = kameraArt === 'blick' ? kameraBlickAusParams(kameraParams, doc) : null;
        const kameras =
          kameraQuelle?.typ === KAMERA_AUS_3D_TYP
            ? kamera3d
              ? [kameraAus3dStandpunkt(kamera3d, seitenverhaeltnisAus(preset?.render.resolution ?? BESTELLFORMAT_VORGABE))]
              : []
            : kameraArt === 'auto'
              ? []
              : kameraArt === 'blick'
                ? kameraBlick
                  ? [{ ...kameraBlick, begruendung: `gesicherter Blick «${kameraBlick.name}» am Knoten «Kamera»` }]
                  : []
              : kameraArt === 'manuell'
                ? kameraManuellAusParams(kameraParams).map((k) => ({ ...k, begruendung: 'von Hand gestellt am Knoten «Kamera»' }))
                : kameraKante
                  ? projektKameras(doc)
                  : [];
        // F3: die erste Stimmung eines vorgeschalteten Stimmung-Knotens, wenn sie aufs Licht wirkt.
        const stimmungKnoten = vorgeschaltet(graph, n.id, 'stimmung')[0];
        const stimmung = stimmungKnoten ? stimmungAusParams(stimmungKnoten.params) : undefined;
        // F4: die Materialien eines vorgeschalteten Oberflaeche-Knotens.
        const oberflaeche = vorgeschaltet(graph, n.id, 'material').find((o) => oberflaecheMaterialien(graph, o.id));
        const materialien = oberflaeche ? oberflaecheMaterialien(graph, oberflaeche.id) : null;
        // Entscheid 96: die Skizze am Eingang «Skizze» — nur von einem Skizzen-Knoten (eine
        // Fremdkante aus einem Hand-Edit zaehlt nicht, dieselbe Regel wie `vis.verbinden`).
        const skizzenKante = graph.edges.find((e) => e.to === n.id && e.toPort === 'skizze');
        const skizzenKnoten = skizzenKante ? graph.nodes.find((k) => k.id === skizzenKante.from) : undefined;
        const skizzeRoh = skizzenKnoten?.typ === 'skizzeIpad' ? skizzenKnoten.params?.['skizze'] : undefined;
        renderAuftraege.set(n.id, {
          prompt,
          faithful: typeof treue === 'number' ? Math.min(1, Math.max(0, treue)) : 0.8,
          samples:
            typeof samples === 'number' ? Math.max(1, Math.round(samples)) : (preset?.render.samples ?? 128),
          hatSzene: graph.edges.some((e) => e.to === n.id && e.toPort === 'szene'),
          // HS5: «Nur Cycles» bestellt reines Cycles (vis.skip) statt
          // KI-Veredelung — Node-Param, Default false hinter striktem `=== true`.
          nurCycles: params['nurCycles'] === true,
          ...(preset && presetId
            ? { presetId, resolution: preset.render.resolution, sun: preset.render.sun, komposition: preset.komposition }
            : {}),
          ...(kameras.length > 0 ? { kameras } : {}),
          ...(kameraQuelle?.typ === KAMERA_AUS_3D_TYP && !kamera3d ? { kameraAus3dFehlt: true as const } : {}),
          ...(kameraArt === 'auto' ? { kamerasAuto: kameraAutoAusParams(kameraParams) } : {}),
          ...(kameraArt === 'blick' && !kameraBlick ? { kameraBlickFehlt: true as const } : {}),
          ...((kameraArt === 'manuell' || kameraArt === 'blick') && kameras.length > 0
            ? { kamerasPerspektive: kameraParams['perspektive'] === 'frei' ? ('frei' as const) : ('senkrecht' as const) }
            : {}),
          ...(stimmung
            ? {
                stimmungen: stimmung.presets,
                ...(stimmung.wirkung !== 'prompt'
                  ? {
                      umgebung: {
                        preset: stimmung.presets[0]!,
                        ...(stimmung.drehungGrad !== undefined ? { rotationGrad: stimmung.drehungGrad } : {}),
                      },
                    }
                  : {}),
              }
            : {}),
          ...(materialien ? { materialien } : {}),
          ...(skizzenKnoten?.typ === 'skizzeIpad'
            ? {
                skizze: {
                  knoten: skizzenKnoten.id,
                  wahl: typeof skizzeRoh === 'string' && skizzeRoh.trim() ? skizzeRoh : 'neueste',
                },
              }
            : {}),
        });
        break;
      }
      case 'kamera':
      case KAMERA_AUS_3D_TYP:
        // Reine Quelle — konsumiert direkt im 'render'-Fall über die Kante,
        // trägt selbst keinen Ausgangswert im `werte`-Store (wie 'modell').
        break;
      default:
        // modell / vergleich / blatt / referenz / aufnahme: keine puren
        // Ausgangswerte — 'aufnahme' liefert sein 'bild' wie 'render' rein aus
        // der App-Laufzeit (vis-runtime), der Kernel bleibt pull-basiert und
        // kennt nur den Porttyp, nie die Bilddaten selbst.
        break;
    }
  }
  return { werte, renderAuftraege };
}
