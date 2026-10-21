import type { KosmoDoc, EbenenKombination } from '../model/doc';
import type { VisGraph, VisNode } from '../model/entities';
import { projektKameras, type AutoKameraStandpunkt } from './kamera';
import {
  BESTELLFORMAT_VORGABE,
  FOV_GRENZEN_GRAD,
  KAMERA_AUS_3D_TYP,
  kameraAus3dAusParams,
  kameraAus3dStandpunkt,
  seitenverhaeltnisAus,
} from './kamera-aus-3d';

/**
 * **«Varianten mit einem Klick»** (Owner-Entscheide 92/92a/92b der Visbox, 14.10.2026, Blatt 23;
 * Posten «L24 Bildweg Varianten (E246)» fuer Demoauftrag 01).
 *
 * Ein Knoten «Varianten» haengt hinter einem Render-Knoten und bestellt dessen Einstellung in
 * allen Kombinationen dreier Achsen:
 *
 *  - **Standpunkte** — woher geblickt wird: die Kamera aus der 3D-Ansicht, die von Hand
 *    gesicherten Blicke und die Standpunkte aus dem Modell (Auto-Kamera samt uebernommenen
 *    Kameras, `projektKameras`).
 *  - **Stimmungen** — der Stimmungs-Katalog (`VIS_STIMMUNGEN`, acht seit Entscheid 110 B).
 *  - **Entwuerfe** — welches Modell: das aktuelle Modell oder eine Ebenenkombination
 *    (E222, `doc.settings.ebenenKombinationen`). Eine Kombination zeigt nur ihre sichtbaren
 *    Ebenen — so liegen Volumenvarianten nebeneinander im Dokument und werden je fuer sich
 *    gerechnet (`docFuerEbenen`).
 *
 * Alle Kombinationen mit Zaehler, einmal freigeben (92); Vorgabe 3 × 1 (Abend) × 1 (92a);
 * Warnung ab 12 Bildern mit ungefaehrer Dauer, kein hartes Limit (92b).
 *
 * **Ein Auftrag je Stimmung und Entwurf, mit allen Standpunkten:** ein Render-Auftrag traegt
 * genau EINEN Prompt und EINE Szene, aber eine Liste von Kameras (der Abholer rechnet je Kamera
 * ein Bild). Die Anzahl der Auftraege ist darum Stimmungen × Entwuerfe, die der Bilder
 * Standpunkte × Stimmungen × Entwuerfe.
 *
 * Diese Datei rechnet nur (Kern, kein Store, keine Bruecke). Senden, Freigeben und das Raster
 * lebt in der App (`modules/vis/varianten.ts`).
 */

/** Katalog-Typ des Knotens (`VIS_NODE_KATALOG`). */
export const VARIANTEN_TYP = 'varianten';

/** Entscheid 92a: so viele Standpunkte sind beim Oeffnen gewaehlt (die ersten in der Liste). */
export const VARIANTEN_VORGABE_STANDPUNKTE = 3;
/** Entscheid 92a: die eine Stimmung beim Oeffnen. */
export const VARIANTEN_VORGABE_STIMMUNG = 'abend';
/** Entscheid 92b: ab so vielen Bildern warnt der Knoten (mit ungefaehrer Dauer), sperrt aber nichts. */
export const VARIANTEN_WARNUNG_AB = 12;

/** Entwurf «das aktuelle Modell», wie der Render-Knoten es ohne Varianten sendet. */
export const ENTWURF_AKTUELL = 'aktuell';
export const ENTWURF_AKTUELL_NAME = 'Aktuelles Modell';

/** Woher ein Standpunkt kommt — fuer die Anzeige am Knoten. */
export type StandpunktQuelle = 'kamera3d' | 'blick' | 'modell';

export interface VariantenStandpunkt {
  name: string;
  quelle: StandpunktQuelle;
  kamera: AutoKameraStandpunkt;
}

export interface VariantenEntwurf {
  id: string;
  name: string;
  kombination?: EbenenKombination;
}

/** Die gewaehlten Achsen, wie sie im Knoten stehen (Namen bzw. Kennungen). */
export interface VariantenAchsen {
  standpunkte: string[];
  stimmungen: string[];
  entwuerfe: string[];
}

/**
 * Liest eine Liste aus einem Knoten-Parameter. Parameter sind Zeichen, Zahl oder Wahrheitswert
 * (`VisNode.params`); eine Liste steht darum als JSON-Text darin. Fehlt der Parameter oder ist
 * er kein Text einer Liste aus Zeichen, heisst das «nichts gewaehlt» — dann gilt die Vorgabe.
 */
export function liesListe(wert: unknown): string[] | undefined {
  if (typeof wert !== 'string' || wert.trim() === '') return undefined;
  try {
    const roh: unknown = JSON.parse(wert);
    if (!Array.isArray(roh) || !roh.every((x) => typeof x === 'string')) return undefined;
    return [...new Set(roh as string[])];
  } catch {
    return undefined;
  }
}

/** Gegenstueck zu `liesListe`. */
export function schreibeListe(liste: readonly string[]): string {
  return JSON.stringify([...new Set(liste)]);
}

/** Der Render-Knoten, hinter dem dieser Varianten-Knoten haengt (Linie an den Eingang «Render»). */
export function variantenRenderKnoten(graph: VisGraph, variantenId: string): VisNode | undefined {
  const kante = graph.edges.find((e) => e.to === variantenId && e.toPort === 'render');
  const quelle = kante ? graph.nodes.find((n) => n.id === kante.from) : undefined;
  return quelle?.typ === 'render' ? quelle : undefined;
}

function fovImVertragGrad(fov: number): boolean {
  return Number.isFinite(fov) && fov >= FOV_GRENZEN_GRAD[0] && fov <= FOV_GRENZEN_GRAD[1];
}

/**
 * Alle Standpunkte, aus denen der Knoten waehlen kann, in fester Reihenfolge: zuerst die Kamera
 * aus der 3D-Ansicht (wenn ein solcher Knoten eine Kamera traegt; der am Render-Knoten haengende
 * zuerst), dann die gesicherten Blicke, dann die Standpunkte aus dem Modell. Die Vorgabe sind
 * die ersten drei.
 *
 * Ein Name kommt nur einmal vor: ein gesicherter Blick, der wie ein Modell-Standpunkt heisst,
 * bekommt «(Blick)» angehaengt — sonst waere im Raster nicht zu sagen, welche Zeile welche ist.
 *
 * Leer ist die Liste, wenn das Dokument weder Blicke noch Geometrie hat — in Visbox ist das der
 * Normalfall: dort rechnet der Heim-PC seine eigenen Richtungen (`cameras: 'auto'`), und die
 * App ergaenzt deren Namen (`heim-standpunkte.ts`).
 */
export function verfuegbareStandpunkte(doc: KosmoDoc, graph: VisGraph, renderId?: string): VariantenStandpunkt[] {
  const out: VariantenStandpunkt[] = [];
  const belegt = new Set<string>();
  const dazu = (name: string, quelle: StandpunktQuelle, kamera: AutoKameraStandpunkt) => {
    let n = name;
    if (belegt.has(n)) n = `${name} (${quelle === 'blick' ? 'Blick' : quelle === 'kamera3d' ? '3D-Ansicht' : 'Modell'})`;
    if (belegt.has(n)) return;
    belegt.add(n);
    out.push({ name: n, quelle, kamera: n === kamera.name ? kamera : { ...kamera, name: n } });
  };

  const kameraKante = renderId ? graph.edges.find((e) => e.to === renderId && e.toPort === 'kameras') : undefined;
  const k3dKnoten = graph.nodes
    .filter((n) => n.typ === KAMERA_AUS_3D_TYP)
    .sort((a, b) => Number(b.id === kameraKante?.from) - Number(a.id === kameraKante?.from));
  for (const knoten of k3dKnoten) {
    const k = kameraAus3dAusParams(knoten.params);
    if (!k) continue;
    dazu('Kamera aus 3D-Ansicht', 'kamera3d', kameraAus3dStandpunkt(k, seitenverhaeltnisAus(BESTELLFORMAT_VORGABE)));
    break;
  }
  for (const b of doc.settings.gespeicherteBlicke ?? []) {
    if (!fovImVertragGrad(b.fovGrad)) continue;
    dazu(b.name, 'blick', {
      name: b.name,
      position: [b.position[0], b.position[1], b.position[2]],
      target: [b.ziel[0], b.ziel[1], b.ziel[2]],
      fov: b.fovGrad,
      begruendung: `Von Hand gesicherter Blick «${b.name}» — Bildwinkel ${b.fovGrad.toFixed(1)}°. Kein Vorschlag.`,
    });
  }
  for (const k of projektKameras(doc)) dazu(k.name, 'modell', k);
  return out;
}

/** Die waehlbaren Stimmungen (Kennung und Anzeigename), aus dem Stimmungs-Katalog. */
export function verfuegbareStimmungen(katalog: Record<string, { label: string; prompt: string }>): { id: string; label: string }[] {
  return Object.entries(katalog).map(([id, s]) => ({ id, label: s.label }));
}

/** Die waehlbaren Entwuerfe: das aktuelle Modell und jede Ebenenkombination (E222). */
export function verfuegbareEntwuerfe(doc: KosmoDoc): VariantenEntwurf[] {
  return [
    { id: ENTWURF_AKTUELL, name: ENTWURF_AKTUELL_NAME },
    ...(doc.settings.ebenenKombinationen ?? []).map((k) => ({ id: k.id, name: k.name, kombination: k })),
  ];
}

/**
 * Die gewaehlten Achsen eines Knotens, gegen das Verfuegbare gehalten: ein Name, den es nicht
 * (mehr) gibt (gesicherter Blick geloescht, Kombination umbenannt), faellt heraus. Ohne Wahl gilt
 * die Vorgabe 3 × Abend × aktuelles Modell (92a).
 *
 * `standpunkteVerfuegbar` leer heisst: der Kern kennt keine Standpunkte (Visbox, Heim-PC) — dann
 * bleibt auch die Wahl leer, und gerechnet wird, was die Gegenseite von sich aus rechnet.
 */
export function gewaehlteAchsen(
  params: VisNode['params'] | undefined,
  standpunkteVerfuegbar: readonly string[],
  stimmungenVerfuegbar: readonly string[],
  entwuerfeVerfuegbar: readonly string[],
): VariantenAchsen {
  const p = params ?? {};
  const gefiltert = (wahl: string[] | undefined, da: readonly string[], vorgabe: string[]) =>
    wahl === undefined ? vorgabe : da.filter((x) => wahl.includes(x));
  return {
    standpunkte: gefiltert(
      liesListe(p['standpunkte']),
      standpunkteVerfuegbar,
      standpunkteVerfuegbar.slice(0, VARIANTEN_VORGABE_STANDPUNKTE),
    ),
    stimmungen: gefiltert(
      liesListe(p['stimmungen']),
      stimmungenVerfuegbar,
      stimmungenVerfuegbar.includes(VARIANTEN_VORGABE_STIMMUNG) ? [VARIANTEN_VORGABE_STIMMUNG] : stimmungenVerfuegbar.slice(0, 1),
    ),
    entwuerfe: gefiltert(liesListe(p['entwuerfe']), entwuerfeVerfuegbar, entwuerfeVerfuegbar.slice(0, 1)),
  };
}

/** Anzahl Bilder: Standpunkte × Stimmungen × Entwuerfe. */
export function variantenAnzahl(s: number, st: number, e: number): number {
  return Math.max(0, s) * Math.max(0, st) * Math.max(0, e);
}

/** Der Zaehler am Knoten, z. B. «3 Bilder (3 × 1 × 1)». */
export function variantenZaehlerSatz(s: number, st: number, e: number): string {
  const n = variantenAnzahl(s, st, e);
  return `${n} ${n === 1 ? 'Bild' : 'Bilder'} (${s} × ${st} × ${e})`;
}

/** Ausgeschrieben, fuer Kurzhilfe und Kosmo: «3 Standpunkte × 1 Stimmung × 1 Entwurf». */
export function variantenAchsenSatz(s: number, st: number, e: number): string {
  return (
    `${s} ${s === 1 ? 'Standpunkt' : 'Standpunkte'} × ${st} ${st === 1 ? 'Stimmung' : 'Stimmungen'} × ` +
    `${e} ${e === 1 ? 'Entwurf' : 'Entwürfe'}`
  );
}

/** Entscheid 92b: warnt der Knoten bei dieser Anzahl? */
export function variantenWarnt(anzahl: number): boolean {
  return anzahl >= VARIANTEN_WARNUNG_AB;
}

/** Alle Knoten, von denen der Render-Knoten (mittelbar) einen Eingang bekommt. */
/** Alle Knoten, die (mittelbar) in `zielId` fliessen. Auch fuer die neuen Knoten (`visgraph.ts`). */
export function vorfahren(graph: VisGraph, zielId: string): Set<string> {
  const gesehen = new Set<string>();
  const offen = [zielId];
  while (offen.length > 0) {
    const id = offen.pop()!;
    for (const e of graph.edges) {
      if (e.to === id && !gesehen.has(e.from)) {
        gesehen.add(e.from);
        offen.push(e.from);
      }
    }
  }
  return gesehen;
}

/**
 * Der Graph, wie er fuer EINE Stimmung ausgewertet wird: jede Stimmung, die (mittelbar) in den
 * Render-Knoten fliesst, traegt die gewaehlte. Das Dokument bleibt unberuehrt — die Kopie lebt
 * nur fuer die eine Auswertung (`evaluiereGraph`). `ohneStimmungsKnoten`: es floss keine
 * Stimmung hinein; dann setzt die App den Stimmungstext vor den Prompt.
 */
export function graphMitStimmung(
  graph: VisGraph,
  renderId: string,
  stimmung: string,
): { graph: VisGraph; ohneStimmungsKnoten: boolean } {
  const davor = vorfahren(graph, renderId);
  let getroffen = false;
  const nodes = graph.nodes.map((n) => {
    if (n.typ !== 'stimmung' || !davor.has(n.id)) return n;
    getroffen = true;
    // Bauplan «Neue Knoten» (Entscheid 110 B): der Stimmung-Knoten liest zuerst die Liste
    // `presets` (Mehrfachwahl) — sie wird mitgesetzt, sonst gewaenne die Wahl am Knoten.
    return { ...n, params: { ...(n.params ?? {}), preset: stimmung, presets: schreibeListe([stimmung]) } };
  });
  return { graph: { ...graph, nodes }, ohneStimmungsKnoten: !getroffen };
}

/** Kennung einer Zelle-Gruppe (ein Auftrag = eine Stimmung, ein Entwurf) — der Laufschluessel. */
export function variantenLaufId(variantenId: string, stimmung: string, entwurf: string): string {
  return `${variantenId}::${stimmung}::${entwurf}`;
}

/*
 * Lesen fuer Kosmo und Claude (`vis.varianten` mit `stand: true`). Was gerechnet ist, liegt nicht im Dokument,
 * sondern in der Laufzeit der App (`vis-runtime.ts`, «Laufzeit ≠ Modell»). Der Kern kann sie
 * nicht lesen; die App meldet darum hier einen Leser an (`modules/vis/varianten.ts`). Ohne Leser
 * (Kern allein, Proben ohne App) sagt der Befehl genau das.
 */
type StandLeser = (graphId: string, nodeId: string) => string;
let standLeser: StandLeser | null = null;

export function setzeVariantenStandLeser(leser: StandLeser | null): void {
  standLeser = leser;
}

export function variantenStandLesen(graphId: string, nodeId: string): string | null {
  return standLeser ? standLeser(graphId, nodeId) : null;
}

/**
 * Der Varianten-Knoten, den ein Befehl meint: mit `nodeId` genau dieser (in `graphId`, sonst in
 * jedem Graphen), ohne den ersten Varianten-Knoten (in `graphId`, sonst im ersten Graphen, der
 * einen hat). `undefined`, wenn es keinen gibt — die Befehle machen daraus ihren Satz.
 */
export function findeVariantenKnotenIn(
  doc: KosmoDoc,
  graphId?: string,
  nodeId?: string,
): { graph: VisGraph; node: VisNode } | undefined {
  const graphen =
    graphId !== undefined
      ? [doc.get<VisGraph>(graphId)].filter((g): g is VisGraph => g?.kind === 'visgraph')
      : doc.byKind<VisGraph>('visgraph');
  for (const graph of graphen) {
    const node = nodeId !== undefined ? graph.nodes.find((n) => n.id === nodeId) : graph.nodes.find((n) => n.typ === VARIANTEN_TYP);
    if (node) return { graph, node };
  }
  return undefined;
}
