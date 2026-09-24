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
  material: [],
  kamera: [],
  // kombinierer/vergleich: arbeiten rein über ihre Eingänge, keine Parameter.
  kombinierer: [],
  vergleich: [],
  prompt: [
    // `evaluiereGraph` case 'prompt': `String(params['text'] ?? '')`.
    { name: 'text', info: 'Freier Stil-Text — geht wortgleich als Prompt-Ausgang in den Graphen.' },
  ],
  stimmung: [
    // `evaluiereGraph` case 'stimmung': `VIS_STIMMUNGEN[params['preset'] ?? 'morgen']`.
    { name: 'preset', info: 'Morgenlicht, Abendstimmung oder Weissmodell — liefert die passende Prompt-Phrase.' },
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
    { name: 'nurCycles', info: 'Reines Cycles-Rendering ohne KI-Veredelung — nur wirksam, wenn eingeschaltet.' },
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
 *  tragen alle 12 Typen eine (`test/vis-legende-infos.test.ts` beweist es),
 *  der ehrliche Satz bleibt als Netz für künftige Katalog-Zugänge. */
export function nodeZweck(typ: string): string {
  const k = VIS_NODE_KATALOG[typ];
  if (!k) return 'Unbekannter Node-Typ — nicht im Katalog.';
  return k.hilfe || `${k.label} — noch ohne Kurzbeschrieb im Katalog.`;
}
