/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/derive/kamera.ts` (KosmoOrbit).
 *
 * Warum (E26, 24.09.2026): Das Original leitet Standpunkte aus dem Bauwerksmodell von
 * KosmoOrbit ab (Hüllbox über Wände, Decken, Dach …) und zieht damit den Architekturkern
 * nach. In Visbox gibt es dieses Modell nicht. Darum:
 *
 * * Die Typen `KameraReferenzpunkt`, `AutoKameraStandpunkt` und `KamerahoeheBefund` sind
 *   WÖRTLICH übernommen.
 * * `projektKameras` übernimmt die Kameras aus `doc.settings.uebernommeneKameras` WÖRTLICH
 *   wie das Original — die aus dem Modell abgeleiteten Vorschläge fehlen hier (leere Liste),
 *   bis Visbox sie aus der Mappe liefert.
 * * `augeImModell` antwortet `null` («keine Box bekannt») — im Original die dritte Antwort
 *   für ein Modell ohne Geometrie, ausdrücklich KEIN «nein».
 * * `pruefeKamerahoehen` findet nichts zu beanstanden, weil es keine abgeleiteten
 *   Standpunkte gibt, die es prüfen könnte.
 */
import type { KosmoDoc } from '../model/doc';

export type KameraReferenzpunkt = 'terrain_an_kamera' | 'okff' | 'huellbox_unterkante' | 'weltnull';

export interface AutoKameraStandpunkt {
  name: string;
  /** Meter, glTF-Konvention (x, y-oben, z). */
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
  /** Ehrliche Kurzbegründung fürs UI — nie «KI», immer «aus dem Modell». */
  begruendung: string;
  /**
   * N1 (ROADMAP 1331, `auf-20260901-68` R2) — additiv, optional, KEIN
   * Vorgabewert: der Bodenbezug, von dem die Augenhöhe dieses Standpunkts
   * (`position`) tatsächlich gerechnet ist. Fehlt das Feld, heisst das «kein
   * Bezugspunkt genannt» — nicht `huellbox_unterkante` (derselbe Grundsatz
   * wie am Vertragsfeld selbst, `render-scene.ts:52-54`). Zuordnung je
   * Standpunkt unten an der jeweiligen `out.push`-Stelle begründet;
   * Gesamtnachweis: `test/n1-kamera-referenzpunkt.test.ts`.
   */
  referenzpunkt?: KameraReferenzpunkt;
}

export interface KamerahoeheBefund {
  standpunkt: string;
  text: string;
}

/** Visbox: noch keine aus dem Modell abgeleiteten Standpunkte. */
export function deriveAutoKameras(_doc: KosmoDoc): AutoKameraStandpunkt[] {
  return [];
}

export function projektKameras(doc: KosmoDoc): AutoKameraStandpunkt[] {
  const uebernommen = doc.settings.uebernommeneKameras ?? [];
  const aus: AutoKameraStandpunkt[] = uebernommen.map((k) => ({
    name: k.name,
    position: [k.position[0], k.position[1], k.position[2]],
    target: [k.target[0], k.target[1], k.target[2]],
    fov: k.fov,
    // «Vorschlag aus dem Modell» wäre hier GELOGEN — nichts an dieser Kamera
    // ist abgeleitet. Der Text sagt darum, woher sie wirklich kommt.
    begruendung:
      `Von Hand gesetzt und aus «${k.quelle.datei}» (${k.quelle.art.toUpperCase()}) übernommen — ` +
      `Brennweite ${k.brennweiteMm.toFixed(1)} mm, Bildwinkel ${k.fov.toFixed(1)}°. Kein Vorschlag.`,
    // KEIN `referenzpunkt`: die Quelldatei nennt keinen Bodenbezug, und
    // einen zu behaupten wäre dieselbe Lüge, gegen die das Feld gebaut
    // wurde (`CameraSpec.referenzpunkt`, `kosmo-contracts`). Dieselbe
    // Entscheidung wie bei «Übersicht» oben.
  }));
  return [...aus, ...deriveAutoKameras(doc)];
}

export function augeImModell(
  _doc: KosmoDoc,
  _positionM: readonly [number, number, number],
  _randM = 0,
): boolean | null {
  return null;
}

export function pruefeKamerahoehen(_doc: KosmoDoc): KamerahoeheBefund[] {
  return [];
}
