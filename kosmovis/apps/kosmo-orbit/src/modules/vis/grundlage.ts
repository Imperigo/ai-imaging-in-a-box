import { BESTELLFORMAT_VORGABE, type AutoKameraStandpunkt, type KosmoDoc } from '@kosmo/kernel';
import type { RenderJob } from '@kosmo/contracts';
import { melde, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import type { NodeLauf } from './vis-runtime';

/**
 * Nr. 85 Paket 2 — «Eine Grundlage, mehrere Varianten» (Owner-Entscheide 98, 98a, 98b,
 * 20.10.2026; Entwurfsflaeche Blatt 26).
 *
 * Der Render-Knoten arbeitet IMMER in zwei Schritten:
 *  1. «Grundlage rendern» bestellt nur Blender (`vis.skip: true`, `render.passes: 'alle'`). Der
 *     Heim-PC legt die Grundlage ab und meldet ihre Kennung (`result.grundlage.id`).
 *  2. «Variante erzeugen» bestellt den KI-Schritt auf DIESER Grundlage (`vis.grundlage`) mit
 *     EINEM Startwert (`vis.seed`) — jede Variante hat dieselbe Kamera und dieselbe Geometrie.
 *
 * WAS IM DOKUMENT STEHT (und warum dort): Kennung, Startwert, Stand, Zahl der Kameras und die
 * gelieferten Ebenen liegen als flache Parameter am Render-Knoten (`vis.nodeParametrieren`) —
 * sie ueberleben ein Neuladen, wie die Grundlage auf dem Heim-PC, und «neu würfeln» ist damit
 * rueckgaengig machbar wie jeder Parameter. Bilder bleiben Laufzeit (`vis-runtime.ts`).
 *
 * WAS «VERALTET» HEISST (98b): Modell, Kamera(s), Sonne/Himmel, Aufloesung oder Samples weichen
 * von dem ab, womit die Grundlage gerechnet wurde. Der Stand ist ein Streuwert ueber genau diese
 * Eingaben (`grundlageStand`); der Prompt gehoert NICHT dazu — ihn zu aendern ist der Sinn
 * einer Variante.
 */

/** Die Parameter am Render-Knoten, unter denen die Grundlage steht. */
export const GRUNDLAGE_PARAM = {
  id: 'grundlageId',
  seed: 'grundlageSeed',
  stand: 'grundlageStand',
  kameras: 'grundlageKameras',
  ebenen: 'grundlageEbenen',
} as const;

/** Form der Kennung, wie im Vertrag (`RenderScene.vis.grundlage`). */
export const GRUNDLAGE_KENNUNG = /^gl-[0-9a-f]{16}$/;

/** Groesster Startwert des Vertrags (`vis.seed`, 0..2147483647). */
export const STARTWERT_MAX = 2147483647;

export const GRUNDLAGE_VERALTET_SATZ = 'Grundlage veraltet — erst neu rendern, dann Varianten';
export const KEINE_GRUNDLAGE_SATZ = 'Noch keine Grundlage — zuerst «Grundlage rendern», dann Varianten mit derselben Kamera.';
/** Entscheid 104: dieselbe Aussage in zwei Zeilen am Knoten — die dritte traegt die Guete; der
 *  ganze Satz steht in der Kurzhilfe und am gesperrten Knopf. */
export const KEINE_GRUNDLAGE_KURZ = 'Noch keine Grundlage — zuerst «Grundlage rendern».';
export const GRUNDLAGE_FEHLT_KENNUNG_SATZ =
  'Das Cycles-Bild ist da, aber der Heim-PC hat keine Grundlage gemeldet — Varianten gehen erst, wenn er Grundlagen ablegt.';
export const STRICHZEICHNUNG_OHNE_VARIANTE_SATZ =
  'Eine Strichzeichnung hat keinen KI-Schritt — «Grundlage rendern» liefert sie, Varianten gibt es dafür nicht.';
export const SKIZZE_OHNE_GRUNDLAGE_SATZ =
  'Mit Skizze entsteht das Bild aus der Skizze — dafür gibt es keine Grundlage. Skizze lösen oder «Grundlage rendern» ohne Skizze.';

/** Lesbare Namen der Ebenen (Vertrag `EbenenArt`). Unbekannte bleiben, wie sie kamen. */
const EBENE_NAME: Record<string, string> = {
  schoenbild: 'Schönbild',
  tiefe: 'Tiefe',
  'material-id': 'Material-ID',
};

export function ebenenName(art: string): string {
  return EBENE_NAME[art] ?? art;
}

/** «gl-74896f…» — die Kennung kurz, wie am Knoten gezeigt. */
export function kurzKennung(id: string): string {
  return id.length > 9 ? `${id.slice(0, 9)}…` : id;
}

/**
 * 98a: EIN Startwert je Grundlage, beim Eintreffen gezogen. Gezogen wird aus der Kennung selbst
 * (die ersten acht Hex-Zeichen), damit derselbe Eingang immer denselben Wert gibt — kein Zufall
 * im Poll, und zwei Rechner, die dieselbe Grundlage sehen, zeigen denselben Startwert.
 */
export function startwertAusKennung(id: string): number {
  const hex = id.startsWith('gl-') ? id.slice(3, 11) : '';
  const n = Number.parseInt(hex, 16);
  return Number.isFinite(n) ? n % (STARTWERT_MAX + 1) : 0;
}

/** «neu würfeln»: ein frischer Startwert im Vertragsbereich. `zufall` ist fuer die Probe. */
export function neuerStartwert(zufall: () => number = Math.random, bisher?: number): number {
  for (let i = 0; i < 4; i++) {
    const n = Math.floor(zufall() * (STARTWERT_MAX + 1)) % (STARTWERT_MAX + 1);
    if (n !== bisher) return n;
  }
  return ((bisher ?? 0) + 1) % (STARTWERT_MAX + 1);
}

// ---- Stand (98b) ----------------------------------------------------------------------------

function kanonisch(wert: unknown): unknown {
  if (Array.isArray(wert)) return wert.map(kanonisch);
  if (wert !== null && typeof wert === 'object') {
    const ziel: Record<string, unknown> = {};
    for (const k of Object.keys(wert as Record<string, unknown>).sort()) {
      ziel[k] = kanonisch((wert as Record<string, unknown>)[k]);
    }
    return ziel;
  }
  return wert;
}

/** FNV-1a, zweimal mit verschiedenem Anfang — 64 bit als 16 Hex-Zeichen. Kein Sicherheitsziel. */
function streuwert(text: string): string {
  const lauf = (seed: number): string => {
    let h = seed >>> 0;
    for (let i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return (h >>> 0).toString(16).padStart(8, '0');
  };
  return lauf(0x811c9dc5) + lauf(0x9e3779b9);
}

const modellStandCache = new WeakMap<KosmoDoc, { revision: number; stand: string }>();

/**
 * Streuwert je Bauteil, an der IDENTITAET des Objekts gemerkt — dasselbe Prinzip wie der
 * Ableitungs-Cache des Kerns (R35/E256, `derive/ableitungs-cache.ts`): Entitaeten sind
 * unveraenderlich, `KosmoDoc.apply` setzt je Patch ein neues Objekt. Nach einer Aenderung wird
 * darum nur das geaenderte Bauteil neu gestreut, nicht das ganze Dokument.
 */
const bauteilStreuwert = new WeakMap<object, string>();

function streuwertVon(e: object): string {
  const alt = bauteilStreuwert.get(e);
  if (alt !== undefined) return alt;
  const neu = streuwert(JSON.stringify(kanonisch(e)));
  bauteilStreuwert.set(e, neu);
  return neu;
}

/**
 * Stand des MODELLS: alles im Dokument ausser den Render-Graphen selbst (ein verschobener Knoten
 * aendert kein Bild). Gelesen wird nur ueber das Dokument (`doc.entities`), wie es der Kern fuer
 * Ableitungen verlangt (R35); kanonisch und nach Kennung sortiert, damit derselbe Inhalt nach dem
 * Neuladen denselben Stand hat. Je Dokument-Revision einmal zusammengesetzt, je Bauteil-Objekt
 * einmal gestreut.
 */
export function modellStand(doc: KosmoDoc): string {
  const alt = modellStandCache.get(doc);
  if (alt && alt.revision === doc.revision) return alt.stand;
  const teile: string[] = [];
  for (const e of doc.entities.values()) {
    if (e.kind !== 'visgraph') teile.push(`${e.id}:${streuwertVon(e)}`);
  }
  teile.sort();
  const stand = streuwert(teile.join('|'));
  modellStandCache.set(doc, { revision: doc.revision, stand });
  return stand;
}

/** Was eine Grundlage festlegt — genau die Eingaben aus 98b, sonst nichts. */
export interface GrundlageEingaben {
  samples: number;
  resolution?: readonly [number, number] | undefined;
  sun?: unknown;
  himmel?: unknown;
  kameras?: readonly AutoKameraStandpunkt[] | undefined;
  kameraWahl?: 'auto' | 'saved' | undefined;
}

/**
 * Der Stand einer Grundlage: Modell, Kameras, Sonne und Himmel, Aufloesung, Samples. Der Himmel
 * zaehlt mit, weil er in der Bedienung das Sonnenlicht ist (Zeile 47/48) — ein anderer Himmel
 * ist ein anderes Cycles-Bild. Fehlt die Aufloesung, gilt die Vorgabe des Senders; das ist an
 * beiden Enden dieselbe Zahl (`BESTELLFORMAT_VORGABE`) — sie wird eingesetzt, damit eine von
 * Hand gewaehlte Vorgabe-Aufloesung nicht als «andere» zaehlt.
 */
export function grundlageStand(doc: KosmoDoc, e: GrundlageEingaben): string {
  return streuwert(
    JSON.stringify(
      kanonisch({
        modell: modellStand(doc),
        samples: e.samples,
        aufloesung: e.resolution ?? BESTELLFORMAT_VORGABE,
        sonne: e.sun ?? null,
        himmel: e.himmel ?? null,
        kameras: e.kameras && e.kameras.length > 0 ? e.kameras : (e.kameraWahl ?? 'auto'),
      }),
    ),
  );
}

// ---- Am Knoten ------------------------------------------------------------------------------

export interface GrundlageAmKnoten {
  id: string;
  seed: number;
  stand: string;
  kameras: number;
  ebenen: string[];
}

/** Die Grundlage aus den Knoten-Parametern, oder `null`, wenn keine (gueltige) da ist. */
export function grundlageAmKnoten(params: Record<string, unknown> | undefined): GrundlageAmKnoten | null {
  const p = params ?? {};
  const id = p[GRUNDLAGE_PARAM.id];
  if (typeof id !== 'string' || !GRUNDLAGE_KENNUNG.test(id)) return null;
  const seedRoh = p[GRUNDLAGE_PARAM.seed];
  const seed =
    typeof seedRoh === 'number' && Number.isInteger(seedRoh) && seedRoh >= 0 && seedRoh <= STARTWERT_MAX
      ? seedRoh
      : startwertAusKennung(id);
  const stand = typeof p[GRUNDLAGE_PARAM.stand] === 'string' ? (p[GRUNDLAGE_PARAM.stand] as string) : '';
  const kamerasRoh = p[GRUNDLAGE_PARAM.kameras];
  const kameras = typeof kamerasRoh === 'number' && kamerasRoh >= 0 ? kamerasRoh : 0;
  const ebenenRoh = p[GRUNDLAGE_PARAM.ebenen];
  const ebenen = typeof ebenenRoh === 'string' && ebenenRoh ? ebenenRoh.split(',') : [];
  return { id, seed, stand, kameras, ebenen };
}

export type GrundlageZustand = 'keine' | 'aktuell' | 'veraltet';

/** 98b: aktuell nur, wenn der Stand der Grundlage dem heutigen gleicht. */
export function grundlageZustand(g: GrundlageAmKnoten | null, standJetzt: string | undefined): GrundlageZustand {
  if (!g) return 'keine';
  return standJetzt !== undefined && g.stand === standJetzt ? 'aktuell' : 'veraltet';
}

// ---- Aus dem Ergebnis -----------------------------------------------------------------------

type Ergebnis = NonNullable<RenderJob['result']>;

export interface GrundlageImErgebnis {
  id: string;
  wiederverwendet: boolean;
  kameras: number;
  /** Arten der gelieferten Ebenen (mit Datei), in der Reihenfolge des Ergebnisses, ohne Doppel. */
  ebenen: string[];
}

/** Was ein Ergebnis ueber seine Grundlage sagt — `null`, wenn es keine meldet. */
export function grundlageAusErgebnis(r: Ergebnis): GrundlageImErgebnis | null {
  if (!r.grundlage) return null;
  const ebenen: string[] = [];
  const kamerasAusEbenen = new Set<string>();
  for (const e of r.ebenen ?? []) {
    kamerasAusEbenen.add(e.kamera);
    if (e.datei !== null && !ebenen.includes(e.art)) ebenen.push(e.art);
  }
  const kameras = r.qa_je_kamera?.length ?? (kamerasAusEbenen.size || r.images.length);
  return { id: r.grundlage.id, wiederverwendet: r.grundlage.wiederverwendet, kameras, ebenen };
}

/**
 * Laeufe-Felder aus einem Ergebnis (`vis-runtime` `laeufe`): die Kennung der Grundlage, auf der
 * das Bild steht, und ob sie wiederverwendet wurde. Immer ausdruecklich gesetzt (auch als
 * `undefined`): `patchLauf` mischt, und eine Angabe vom vorigen Lauf darf nicht stehen bleiben.
 * Die Startwerte und Posen je Kamera reisen in `qaJeKamera` mit (Vertrag, Paket 1).
 */
export function grundlageLaufFelder(
  r: Ergebnis,
  gesendet?: string,
): { grundlageId: string | undefined; grundlageWiederverwendet: boolean | undefined } {
  return {
    grundlageId: r.grundlage?.id ?? gesendet,
    grundlageWiederverwendet: r.grundlage ? r.grundlage.wiederverwendet : undefined,
  };
}

/**
 * Legt die Grundlage am Knoten ab (ein Undo-Schritt), sobald das Ergebnis eines
 * «Grundlage rendern»-Laufs da ist. Der Startwert wird HIER gezogen (98a) — aus der Kennung,
 * nicht im Kernel-Befehl, der deterministisch bleibt.
 */
export function merkeGrundlage(graphId: string, nodeId: string, g: GrundlageImErgebnis, stand: string): void {
  try {
    useProject.getState().runCommand('vis.nodeParametrieren', {
      graphId,
      nodeId,
      params: {
        [GRUNDLAGE_PARAM.id]: g.id,
        [GRUNDLAGE_PARAM.seed]: startwertAusKennung(g.id),
        [GRUNDLAGE_PARAM.stand]: stand,
        [GRUNDLAGE_PARAM.kameras]: g.kameras,
        [GRUNDLAGE_PARAM.ebenen]: g.ebenen.join(','),
      },
    });
  } catch (err) {
    // Der Knoten kann inzwischen geloescht sein — dann gibt es nichts abzulegen, und das wird
    // gesagt statt verschluckt.
    meldeFehler(err);
  }
}

/**
 * Der Poll ruft das, sobald ein Ergebnis mit Bild da ist: war der Lauf «Grundlage rendern»,
 * wird die gemeldete Grundlage am Knoten abgelegt. Meldet die Gegenseite keine Kennung (ein
 * Heim-PC-Stand vor Nr. 85), bleibt das Cycles-Bild stehen, und der Satz sagt, warum
 * «Variante erzeugen» gesperrt bleibt.
 */
export function grundlageNachErgebnis(
  nodeId: string,
  lauf: Pick<NodeLauf, 'stufe' | 'graphId' | 'grundlageStand'>,
  r: Ergebnis,
): 'abgelegt' | 'ohne-kennung' | 'nichts' {
  if (lauf.stufe !== 'grundlage' || r.images.length === 0) return 'nichts';
  const g = grundlageAusErgebnis(r);
  if (!g || lauf.graphId === undefined || lauf.grundlageStand === undefined) {
    melde(GRUNDLAGE_FEHLT_KENNUNG_SATZ, { ton: 'info' });
    return 'ohne-kennung';
  }
  merkeGrundlage(lauf.graphId, nodeId, g, lauf.grundlageStand);
  return 'abgelegt';
}

/** Verlauf (grosse Ansicht): auf welcher Grundlage ein Lauf steht. */
export function grundlageText(l: Pick<NodeLauf, 'stufe' | 'grundlageId' | 'grundlageWiederverwendet'>): string {
  if (l.stufe === 'grundlage') return l.grundlageId ? `${kurzKennung(l.grundlageId)} — die Grundlage selbst` : 'die Grundlage selbst';
  if (!l.grundlageId) return 'keine — eigener Blender-Lauf';
  return l.grundlageWiederverwendet === false ? `${kurzKennung(l.grundlageId)} (neu gerechnet)` : kurzKennung(l.grundlageId);
}

/** Verlauf (grosse Ansicht): der Startwert — bestellt, sonst je Kamera gemeldet. */
export function startwertText(l: Pick<NodeLauf, 'seed' | 'qaJeKamera'>): string {
  if (l.seed !== undefined) return String(l.seed);
  const gemeldet = [...new Set((l.qaJeKamera ?? []).map((k) => k.seed).filter((s): s is number => s !== undefined))];
  return gemeldet.length > 0 ? gemeldet.join(', ') : 'nicht festgelegt';
}
