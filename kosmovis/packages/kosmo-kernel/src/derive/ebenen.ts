import { KosmoDoc, type Ebene, type EbenenKombination } from '../model/doc';
import type { Aussparung, Dachfenster, Entity, EntityKind, Opening } from '../model/entities';

/**
 * E222 (Owner-Entscheid 13.10.2026, Paket 05 WB-Ebenen) — volles Ebenen-
 * System wie in ArchiCAD. Revidiert die v0.8.9-Rahmung E2 «kein
 * Sichtbarkeits-Panel»: Ebenen blenden aus, sperren, zeigen das Drahtmodell
 * und trennen Verschneidungen.
 *
 * Bauform nach `derive/umbau.ts`: eine gefilterte SICHT auf das Dokument,
 * vor jeder Ableitung angewandt. Ohne angelegte Ebenen kommt das Original
 * zurueck (keine Kopie), darum bleiben alle Goldens byte-gleich.
 *
 * DIE REGELN, an genau dieser einen Stelle:
 *  - Jedes Bauteil liegt auf einer Ebene (`EntityMeta.ebeneId`). Fehlt sie,
 *    gilt die Standardebene seiner Bauteilart `std:<kind>`; die
 *    Standardebenen werden nicht gespeichert, sondern aus den Arten im
 *    Dokument abgeleitet. Ein Eintrag mit `std:`-Id in `settings.ebenen`
 *    haelt nur ihren Zustand fest.
 *  - Eine haengende `ebeneId` faellt GEMELDET auf die Standardebene zurueck
 *    (`ebeneVon` traegt `rueckfall`, `ebenenMeldungen` sammelt), kein Wurf.
 *  - Kombination: eine nicht aufgefuehrte Ebene gilt als sichtbar; fehlt
 *    `gesperrt`/`drahtmodell` im Eintrag, gilt der Wert der Ebene.
 *  - Verschneidungsgruppe 0 verbindet nie; sonst verbinden nur gleiche
 *    Gruppen, danach gelten die Baustoffprioritaeten.
 *  - Kinder folgen dem Wirt: eine Oeffnung, Aussparung oder ein Dachfenster
 *    ist verborgen, wenn ihr Wirt verborgen ist (wie im Umbau-Filter).
 */

export const STD_EBENE_PRAEFIX = 'std:';

/** Vorgabe beim Anlegen und fuer jede Ebene ohne gespeicherten Zustand. */
export const EBENE_VORGABE = { sichtbar: true, gesperrt: false, drahtmodell: false, verschneidungsgruppe: 1 } as const;

export interface EbenenZustand {
  sichtbar: boolean;
  gesperrt: boolean;
  drahtmodell: boolean;
  verschneidungsgruppe: number;
}

/**
 * Name der Standardebene je Bauteilart; `null` = die Art liegt auf keiner
 * Ebene (Verwaltungsdaten, keine Zeichnung). Als `Record<EntityKind, …>`
 * vollstaendig: eine neue Bauteilart ohne Eintrag bricht den Typecheck.
 */
export const STANDARDEBENEN_NAMEN: Record<EntityKind, string | null> = {
  storey: null,
  grid: 'Achsen',
  column: 'Stützen',
  beam: 'Unterzüge',
  etikett: 'Etiketten',
  profil: null,
  assembly: null,
  wall: 'Wände',
  slab: 'Decken',
  opening: 'Öffnungen',
  zone: 'Zonen',
  stair: 'Treppen',
  ramp: 'Rampen',
  gelaender: 'Geländer',
  roof: 'Dächer',
  boundary: 'Baugrenzen',
  mass: 'Volumen',
  freemesh: 'Freie Körper',
  sheet: null,
  imageasset: null,
  furniture: 'Möbel',
  zonentuer: 'Zonentüren',
  terrain: 'Gelände',
  aussparung: 'Aussparungen',
  mangel: 'Mängel',
  kommentar: 'Kommentare',
  masskette: 'Masse',
  hoehenkote: 'Höhenkoten',
  winkelmass: 'Winkelmasse',
  radialmass: 'Radialmasse',
  detail: 'Details',
  visgraph: null,
  annotation: 'Zeichnung',
  skizze: 'Skizzen',
  leuchte: 'Leuchten',
  preparegraph: null,
  dachfenster: 'Dachfenster',
  // E216 Paket 07: eine Beziehung, kein Bauteil. Sie liegt auf keiner Ebene
  // und bleibt darum in jeder gefilterten Sicht; ihr Operator darf verborgen
  // sein und wirkt weiter (`geometry/solid.ts`).
  solidoperation: null,
  // Paket 08 WB-Schnitt (E220): ein benannter Schnitt ist eine Ansicht, kein
  // Bauteil; er liegt auf keiner Ebene (Integrator-Festlegung Runde 25).
  schnitt: null,
};

export function standardEbeneId(kind: EntityKind): string {
  return `${STD_EBENE_PRAEFIX}${kind}`;
}

export function istStandardEbeneId(id: string): boolean {
  return id.startsWith(STD_EBENE_PRAEFIX);
}

/** Liegt diese Art auf einer Ebene? */
export function hatEbene(kind: EntityKind): boolean {
  return STANDARDEBENEN_NAMEN[kind] !== null;
}

/** Die Bauteilart hinter einer `std:`-Id, oder `undefined`, wenn es keine solche Art gibt. */
export function artDerStandardebene(id: string): EntityKind | undefined {
  if (!istStandardEbeneId(id)) return undefined;
  const kind = id.slice(STD_EBENE_PRAEFIX.length);
  return Object.prototype.hasOwnProperty.call(STANDARDEBENEN_NAMEN, kind) &&
    STANDARDEBENEN_NAMEN[kind as EntityKind] !== null
    ? (kind as EntityKind)
    : undefined;
}

function gespeicherteEbene(doc: KosmoDoc, id: string): Ebene | undefined {
  return doc.settings.ebenen?.find((e) => e.id === id);
}

/** Ebene nach Id, auch eine ungespeicherte Standardebene; sonst `undefined`. */
export function ebeneFinden(doc: KosmoDoc, id: string): Ebene | undefined {
  const g = gespeicherteEbene(doc, id);
  if (g) return g;
  const kind = artDerStandardebene(id);
  if (!kind) return undefined;
  return { id, name: STANDARDEBENEN_NAMEN[kind]!, ...EBENE_VORGABE };
}

export interface EbeneBezug {
  ebeneId: string;
  /** Die haengende Id, wenn auf die Standardebene zurueckgefallen wurde. */
  rueckfall?: string;
}

/** Ebene eines Bauteils: `meta.ebeneId`, sonst `std:<kind>`; haengend gemeldet zurueck. */
export function ebeneVon(entity: Entity, doc: KosmoDoc): EbeneBezug {
  const std = standardEbeneId(entity.kind);
  const eigen = entity.meta?.ebeneId;
  if (eigen === undefined) return { ebeneId: std };
  if (ebeneFinden(doc, eigen)) return { ebeneId: eigen };
  return { ebeneId: std, rueckfall: eigen };
}

/**
 * Alle Ebenen des Dokuments: zuerst die Standardebenen der Arten, die im
 * Dokument vorkommen oder deren Zustand gespeichert ist (in der Reihenfolge
 * von `STANDARDEBENEN_NAMEN`), dann die angelegten in ihrer Reihenfolge.
 */
export function ebenenListe(doc: KosmoDoc): Ebene[] {
  const arten = new Set<string>();
  for (const e of doc.entities.values()) if (hatEbene(e.kind)) arten.add(e.kind);
  for (const g of doc.settings.ebenen ?? []) {
    const k = artDerStandardebene(g.id);
    if (k) arten.add(k);
  }
  const out: Ebene[] = [];
  for (const kind of Object.keys(STANDARDEBENEN_NAMEN) as EntityKind[]) {
    if (!arten.has(kind)) continue;
    out.push(ebeneFinden(doc, standardEbeneId(kind))!);
  }
  for (const g of doc.settings.ebenen ?? []) if (!istStandardEbeneId(g.id)) out.push(g);
  return out;
}

/** Zustand einer Ebene, wahlweise unter einer Kombination. Unbekannte Id: Vorgabe. */
export function ebeneZustand(doc: KosmoDoc, ebeneId: string, kombination?: EbenenKombination): EbenenZustand {
  const e = ebeneFinden(doc, ebeneId);
  const basis: EbenenZustand = e
    ? { sichtbar: e.sichtbar, gesperrt: e.gesperrt, drahtmodell: e.drahtmodell, verschneidungsgruppe: e.verschneidungsgruppe }
    : { ...EBENE_VORGABE };
  if (!kombination) return basis;
  const k = kombination.ebenen[ebeneId];
  return {
    sichtbar: k ? k.sichtbar : true,
    gesperrt: k?.gesperrt ?? basis.gesperrt,
    drahtmodell: k?.drahtmodell ?? basis.drahtmodell,
    verschneidungsgruppe: basis.verschneidungsgruppe,
  };
}

/** Die Kombination der Arbeitsansicht; eine haengende Id faellt gemeldet auf keine zurueck. */
export function arbeitsKombination(doc: KosmoDoc): { kombination?: EbenenKombination; rueckfall?: string } {
  const id = doc.settings.arbeitsKombinationId;
  if (id === undefined || id === null) return {};
  const k = doc.settings.ebenenKombinationen?.find((x) => x.id === id);
  return k ? { kombination: k } : { rueckfall: id };
}

/** Zustand der Ebene eines Bauteils (Arbeitsansicht, wenn keine Kombination gegeben ist). */
export function zustandVon(entity: Entity, doc: KosmoDoc, kombination?: EbenenKombination | null): EbenenZustand {
  const k = kombination === undefined ? arbeitsKombination(doc).kombination : (kombination ?? undefined);
  return ebeneZustand(doc, ebeneVon(entity, doc).ebeneId, k);
}

/** Ist das Bauteil in der Arbeitsansicht durch seine Ebene gesperrt? Wie `meta.locked`. */
export function istAufGesperrterEbene(doc: KosmoDoc, id: string): boolean {
  const e = doc.get(id);
  if (!e || !hatEbene(e.kind)) return false;
  return zustandVon(e, doc).gesperrt;
}

/**
 * Verbinden sich zwei Bauteile (Verschneidung im Schnitt, Poché-Join im
 * Grundriss)? Gruppe 0 verbindet nie, sonst nur gleiche Gruppe. Ob dann
 * das eine das andere schneidet, entscheiden weiterhin die
 * Baustoffprioritaeten.
 */
export function verbindenSich(doc: KosmoDoc, a: Entity, b: Entity): boolean {
  const ga = verschneidungsgruppeVon(doc, a);
  const gb = verschneidungsgruppeVon(doc, b);
  return ga !== 0 && ga === gb;
}

export function verschneidungsgruppeVon(doc: KosmoDoc, e: Entity): number {
  return ebeneZustand(doc, ebeneVon(e, doc).ebeneId).verschneidungsgruppe;
}

/** Gibt es im Dokument ueberhaupt eine Abweichung von der Vorgabe? Schneller Ausgang fuer alle Ableitungen. */
function ebenenAktiv(doc: KosmoDoc): boolean {
  return (doc.settings.ebenen?.length ?? 0) > 0 || (doc.settings.arbeitsKombinationId ?? null) !== null;
}

/** Wirt eines Kindbauteils, dessen Sichtbarkeit es teilt. */
function wirtVon(e: Entity): string | undefined {
  if (e.kind === 'opening') return (e as Opening).wallId;
  if (e.kind === 'aussparung') return (e as Aussparung).hostId;
  if (e.kind === 'dachfenster') return (e as Dachfenster).roofId;
  return undefined;
}

/** Sichten, deren Ebenenfilter schon gilt — eine Ableitung darauf filtert nicht noch einmal. */
const GEFILTERT = new WeakSet<KosmoDoc>();

/**
 * Gefilterte Sicht: Bauteile auf verborgenen Ebenen fehlen, ihre Kinder mit.
 * Ohne Abweichung kommt das Original zurueck. Die Sicht teilt Entities und
 * Settings mit dem Original — NUR fuer Ableitungen, nie mutieren. Sie ist
 * als «gefiltert» markiert: `docFuerArbeitsansicht` laesst sie unberuehrt,
 * damit ein Blatt (Folgeposten `derive/sheet.ts`) seine eigene Kombination
 * vorgeben kann.
 *
 * `kombination`: `undefined` = die der Arbeitsansicht, `null` = keine.
 */
export function docFuerEbenen(doc: KosmoDoc, kombination?: EbenenKombination | null): KosmoDoc {
  if (GEFILTERT.has(doc)) return doc;
  if (!ebenenAktiv(doc) && !kombination) return doc;
  const k = kombination === undefined ? arbeitsKombination(doc).kombination : (kombination ?? undefined);
  const weg = new Set<string>();
  for (const [id, e] of doc.entities) {
    if (!hatEbene(e.kind)) continue;
    if (!ebeneZustand(doc, ebeneVon(e, doc).ebeneId, k).sichtbar) weg.add(id);
  }
  if (weg.size === 0) return doc;
  const sicht = new KosmoDoc();
  sicht.settings = doc.settings;
  sicht.revision = doc.revision;
  for (const [id, e] of doc.entities) {
    if (weg.has(id)) continue;
    const wirt = wirtVon(e);
    if (wirt !== undefined && weg.has(wirt)) continue;
    sicht.entities.set(id, e);
  }
  GEFILTERT.add(sicht);
  return sicht;
}

const ARBEITSANSICHT = new WeakMap<KosmoDoc, { revision: number; settings: unknown; sicht: KosmoDoc }>();

/**
 * Die Sicht der Arbeitsansicht (Grundriss, Schnitt, 3D, Treffer am
 * Bildschirm), je Dokument und Revision gemerkt: der Treffertest laeuft bei
 * jeder Mausbewegung.
 */
export function docFuerArbeitsansicht(doc: KosmoDoc): KosmoDoc {
  if (GEFILTERT.has(doc) || !ebenenAktiv(doc)) return doc;
  const m = ARBEITSANSICHT.get(doc);
  if (m && m.revision === doc.revision && m.settings === doc.settings) return m.sicht;
  const sicht = docFuerEbenen(doc);
  ARBEITSANSICHT.set(doc, { revision: doc.revision, settings: doc.settings, sicht });
  return sicht;
}

/** Ist das Bauteil in der Arbeitsansicht verborgen (eigene Ebene oder die seines Wirts)? */
export function istVerborgen(doc: KosmoDoc, id: string): boolean {
  if (!ebenenAktiv(doc)) return false;
  return doc.get(id) !== undefined && docFuerArbeitsansicht(doc).get(id) === undefined;
}

/** Gemeldete Rueckfaelle: haengende Ebenen an Bauteilen, haengende Arbeitskombination. */
export function ebenenMeldungen(doc: KosmoDoc): string[] {
  const out: string[] = [];
  const haengend = new Map<string, number>();
  for (const e of doc.entities.values()) {
    const r = ebeneVon(e, doc).rueckfall;
    if (r !== undefined) haengend.set(r, (haengend.get(r) ?? 0) + 1);
  }
  for (const [id, n] of haengend) {
    out.push(`Ebene «${id}» fehlt: ${n} Bauteil${n === 1 ? '' : 'e'} auf die Standardebene zurückgefallen`);
  }
  const r = arbeitsKombination(doc).rueckfall;
  if (r !== undefined) out.push(`Kombination «${r}» fehlt: Arbeitsansicht ohne Kombination`);
  return out;
}

/**
 * Wirksamer Zustand aller Ebenen unter der Arbeitskombination — Grundlage
 * fuer «Kombination speichern» und fuer das Loslassen einer Kombination,
 * wenn eine Ebene von Hand umgeschaltet wird.
 */
export function wirksameEbenen(doc: KosmoDoc): Ebene[] {
  const k = arbeitsKombination(doc).kombination;
  return ebenenListe(doc).map((e) => ({ ...e, ...ebeneZustand(doc, e.id, k) }));
}
