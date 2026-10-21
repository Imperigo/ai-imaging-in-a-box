import { VIS_NODE_KATALOG } from '@kosmo/kernel';

/**
 * K36 (Owner-Korrekturen 2026-07, S.14: «legende ist gut, erweitere sie an
 * infos und was der jeweilige node alles kann (infos)») — Fähigkeits-Infos
 * je Node-Typ für die Insel-Legende (`legende.tsx`, ANSICHT-Insel).
 *
 * Zweck/Eingänge/Ausgänge kommen DIREKT aus dem Kernel-Katalog
 * (`VIS_NODE_KATALOG`, `derive/visgraph.ts` — `hilfe`/`inputs`/`outputs`),
 * hier steht nur, was der Katalog NICHT trägt: knappe, ehrliche Sätze zu den
 * Parametern, fachlich geprüft am tatsächlichen Verhalten laut Code
 * (`evaluiereGraph` in `derive/visgraph.ts` + `vis-jobs.ts`). Eigene
 * Hilfsdatei im selben Ordner (K36-Dateikreis) statt Anbau am TABU-Kernel.
 *
 * Invariante (s. `test/vis-legende-infos.test.ts`): JEDER Katalog-Typ hat
 * hier einen Eintrag (ggf. leer), und jeder Eintrag zeigt auf einen echten
 * Katalog-Typ — kein Node bleibt ohne Info, keine Karteileiche.
 */

export interface NodeParameterInfo {
  /** Parameter-Name, wie er in `node.params` liegt (`vis.nodeParametrieren`). */
  name: string;
  /** Knapper, ehrlicher Satz zum tatsächlichen Verhalten laut Code. */
  info: string;
}

/**
 * Parameter-Infos je Node-Typ. Quelle je Zeile im Kommentar — Verhalten
 * NICHT erfunden, sondern aus `evaluiereGraph` (`derive/visgraph.ts`
 * Z.297ff) bzw. `vis-jobs.ts` abgelesen.
 */
export const NODE_PARAMETER_INFOS: Readonly<Record<string, readonly NodeParameterInfo[]>> = {
  // modell/material/kamera: reine Quellen ohne Parameter (defaults: {}) —
  // 'material' liest die Wandschichten/Fassadenmodule live aus dem Projekt
  // (`renderPromptBausteine(doc)`), 'kamera' leitet Standpunkte live aus den
  // Modell-Bounds ab (`deriveAutoKameras(doc)`) — nichts einzustellen.
  modell: [],
  // Bauplan «Neue Knoten» (Blatt 33): «Oberfläche» stellt nichts ein — sie ordnet über ihre fünf
  // Eingänge zu (Fassade, Dach, Fenster, Boden, Übrige; Türen zählen zu Übrige).
  material: [],
  materialTextur: [
    { name: 'bibliothek', info: 'Welches Material der Bibliothek (elf, Texturen CC0 am Heim-PC).' },
    { name: 'massstab', info: 'Wie gross ein Bild der Textur auf dem Bauteil wird, in Metern (Vorgabe 1 m).' },
    { name: 'drehung', info: 'Drehung der Textur in Grad (Vorgabe 0°).' },
    { name: 'relief', info: 'Wie plastisch die Höhenkarte die Fläche macht, 0 bis 1 (Vorgabe 0,6).' },
    { name: 'vorschau', info: 'Nur die Vorschau am Knoten: Kugel, Würfel oder Fläche.' },
  ],
  farbpalette: [
    { name: 'farben', info: 'Bis vier Farben — sie gehen als Satz ans Bildmodell.' },
    { name: 'leitfarbe', info: 'Welche der Farben das angehängte Material tönt.' },
    { name: 'staerke', info: 'Wie stark sie tönt, 0 bis 1.' },
  ],
  // Bauplan «Neue Knoten» (Blatt 31): Auto rechnet der Heim-PC, Manuell sind eingefrorene Standpunkte.
  kamera: [
    { name: 'art', info: 'Auto (der Heim-PC rechnet), Manuell (von Hand gestellt) — ohne Wahl die Standpunkte aus dem Modell.' },
    { name: 'richtungen', info: 'Auto: aus welchen Himmelsrichtungen (Vorgabe Süd, Südost, Nordwest).' },
    { name: 'augenhoehe', info: 'Auto: Augenhöhe über dem Gelände in Metern (Vorgabe 1,70).' },
    { name: 'brennweite', info: 'Auto: 24, 35 oder 50 mm (Vorgabe 35).' },
    { name: 'fuellt', info: 'Auto: so viel der Bildbreite füllt das Haus (Vorgabe 70 %) — oder fester Abstand in Metern.' },
    { name: 'perspektive', info: 'Senkrechte gerade (Vorgabe) oder frei gekippt.' },
    { name: 'kameras', info: 'Manuell: die eingefrorenen Standpunkte mit Auge und Blickpunkt.' },
  ],
  // kombinierer/vergleich: arbeiten rein über ihre Eingänge, keine Parameter.
  kombinierer: [],
  vergleich: [],
  // «Skizze vom iPad» (Entscheide 95/95a): defaults `{ skizze: 'neueste' }` — gewählt am Knoten
  // (`SkizzeKnoten.tsx`); welche Skizzen es gibt, meldet der Wirt (`skizze-quelle.ts`).
  skizzeIpad: [
    { name: 'skizze', info: 'Welche Skizze der Mappe gilt — «neueste» nimmt von selbst die zuletzt gelegte, sonst eine bestimmte ältere.' },
  ],
  prompt: [
    // `evaluiereGraph` case 'prompt': `String(params['text'] ?? '')`.
    { name: 'text', info: 'Freier Stil-Text — geht wortgleich als Prompt-Ausgang in den Graphen.' },
  ],
  stimmung: [
    // Bauplan «Neue Knoten» (Blatt 32): `stimmungAusParams` — Liste vor Einzelwert.
    { name: 'presets', info: 'Gewählte Stimmungen (acht, mit Himmelsbild) — die erste bestellt der Render-Knoten.' },
    { name: 'drehung', info: 'Himmel fest drehen, in Grad — ohne Wert stellt der Heim-PC die Sonne zur Kamera.' },
    { name: 'wirkung', info: 'Licht in Blender, Satz fürs Bildmodell, oder beides (Vorgabe).' },
  ],
  zahl: [
    // `evaluiereGraph` case 'zahl': `Number(params['wert'] ?? 0)`; min/max/
    // schritt (defaults 0–1, 0.05) sind die Regler-Grenzen dieses Werts.
    { name: 'wert', info: 'Regler-Wert zwischen Min und Max (Standard 0–1 in 0.05er-Schritten).' },
  ],
  render: [
    // `evaluiereGraph` case 'render': `preset` (nur wirksam wenn gesetzt,
    // sonst 128-Samples-Default) + `nurCycles` (striktes `=== true` →
    // `vis.skip`, reines Cycles ohne KI-Veredelung, `vis-jobs.ts`).
    { name: 'preset', info: 'Optionales Cycles-Preset (Auflösung, Sonne, Samples) — ohne Preset gilt der 128-Samples-Standard.' },
    // Nr. 85 Paket 2 (Entscheid 98): das Haekchen ist am Knoten der Knopf «Grundlage rendern»
    // geworden; der Parameter wirkt nur noch auf den Wegen ohne die zwei Stufen (Kosmo, Insel).
    { name: 'nurCycles', info: 'Altes Häkchen «nur Cycles» — am Knoten heute «Grundlage rendern»; wirkt nur noch beim Senden über Kosmo oder die Insel.' },
  ],
  blatt: [
    // defaults `{ titel: 'Visualisierung' }` — Titel des Blatt-Bürgers in
    // KosmoPublish (Katalog-`hilfe`, ein Undo-Schritt).
    { name: 'titel', info: 'Titel, unter dem das Bild als Blatt in KosmoPublish abgelegt wird.' },
  ],
  referenz: [
    // defaults `{ url: '' }` — Bild-Quelle für Stil-Referenz/Vergleich.
    { name: 'url', info: 'Adresse des Referenzbilds (Stil-Referenz oder Vergleichsbild).' },
  ],
  // «Kamera aus 3D-Ansicht» (14.10.2026): keine einstellbaren Parameter — die Kamera setzt der
  // Knopf «Kamera übernehmen» (und das Anlegen), nicht die Hand (`derive/kamera-aus-3d.ts`).
  kameraAus3d: [],
  // «Varianten» (L24 Bildweg Varianten, E246): die drei Achsen hakt man am Knoten an; ohne Wahl
  // gilt die Vorgabe 3 Standpunkte × Abend × aktuelles Modell (`derive/varianten.ts`).
  varianten: [
    { name: 'standpunkte', info: 'Gewählte Standpunkte (Zeilen des Rasters); ohne Wahl die ersten drei.' },
    { name: 'stimmungen', info: 'Gewählte Stimmungen (Spalten des Rasters); ohne Wahl die Abendstimmung.' },
    { name: 'entwuerfe', info: 'Gewählte Entwürfe (Reiter des Rasters): aktuelles Modell oder eine Ebenenkombination.' },
  ],
  aufnahme: [
    // defaults `{ kamera: 'aktuell' }` — laut Katalog-Kommentar rein
    // dokumentarisch, der Knopf nimmt IMMER den aktuellen Viewport-Stand auf.
    { name: 'kamera', info: 'Nur Beschriftung des Standpunkts — aufgenommen wird immer der aktuelle Viewport-Stand.' },
  ],
};

/** Parameter-Infos eines Typs — leer statt undefined für unbekannte Typen
 *  (Fremd-Graph-Robustheit, Muster `evaluiereGraph`s `?? {}`). */
export function nodeParameterInfos(typ: string): readonly NodeParameterInfo[] {
  return NODE_PARAMETER_INFOS[typ] ?? [];
}

/** Fallback-Zweck, falls ein Katalog-Eintrag ohne `hilfe` auftaucht — heute
 *  tragen alle 14 Typen eine (`test/vis-legende-infos.test.ts` beweist es),
 *  der ehrliche Satz bleibt als Netz für künftige Katalog-Zugänge. */
export function nodeZweck(typ: string): string {
  const k = VIS_NODE_KATALOG[typ];
  if (!k) return 'Unbekannter Node-Typ — nicht im Katalog.';
  return k.hilfe || `${k.label} — noch ohne Kurzbeschrieb im Katalog.`;
}
