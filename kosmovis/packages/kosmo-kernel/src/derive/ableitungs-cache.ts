import type { Entity } from '../model/entities';
import type { KosmoDoc } from '../model/doc';

/**
 * R35 / Owner-Entscheid E256 — Ableitungs-Cache je Bauteil.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * WAS ER LOEST
 *
 * `deriveArbeitsansicht` leitete bei jeder Aenderung das ganze Dokument neu
 * ab (Lastprobe `apps/kosmo-orbit/test/r34-lasttest-100-aenderungen.test.ts`):
 * der alte Cache in `scene.ts` war an `(Dokument, Revision)` gebunden, und
 * jede Aenderung erhoeht die Revision. Am Demohaus waren je Aenderung 2 von
 * 406 Geometrien neu, abgeleitet wurden alle.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * WIE ER DIE ABHAENGIGKEITEN KENNT — aufgezeichnet, nicht aufgezaehlt
 *
 * Eine Ableitung (ein Bauteil, eine Gruppe, ein Teil einer Gruppe) bekommt
 * statt des Dokuments ein PROTOKOLL-Dokument (`Proxy`). Jeder Lesezugriff
 * wird festgehalten:
 *
 * - `get(id)` / `storeyTop(id)` → die Id samt dem gelesenen Objekt;
 * - `byKind(art)` / `storeysOrdered()` / `openingsOf()` → die ganze Art
 *   (ein Generationszaehler je Art, s. `abgleichen`);
 * - `entities` / `inStorey()` / jede unbekannte Methode → das ganze Dokument;
 * - `settings` → das Einstellungsobjekt (Identitaet);
 * - `revision` → die Revision (dann gilt der Eintrag nur in ihr).
 *
 * Damit sind Wandanschluesse (Gehrung/T-Stoss lesen alle Waende → Art
 * `wall`), Oeffnungen im Wirt (`openingsOf` → Art `opening`), Geschoss-
 * und Ebenenbezug (`get(storeyId)`, `settings`) und Daecher an Waenden
 * (`dachDerWand` → was immer es liest) ohne eine Liste erfasst, die beim
 * naechsten Feature veraltet. Was nicht sauber bestimmbar ist, faellt
 * KONSERVATIV aus: eine Art- oder Gesamtabhaengigkeit macht den Eintrag bei
 * jeder Aenderung dieser Art (bzw. jeder Aenderung ueberhaupt) ungueltig.
 *
 * Verschachtelte Ableitungen (`deriveEntity` in einer anderen Ableitung)
 * laufen selbst ueber den Cache und reichen ihre Abhaengigkeiten an die
 * aeussere weiter.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * WIE ER ERKENNT, WAS SICH GEAENDERT HAT
 *
 * Entitaeten sind unveraenderlich: `KosmoDoc.apply` setzt je Patch das
 * `after`-Objekt (Undo setzt das `before`-Objekt zurueck). Die Identitaet
 * eines Objekts ist darum sein Versionsstempel — das Doc-Modell und die
 * Speicherform bleiben unberuehrt. `abgleichen` vergleicht je Art die
 * Folge der Objekte mit dem letzten Stand (Identitaet UND Reihenfolge, denn
 * `byKind` liefert in Einfuegereihenfolge, und ein Undo nach Loeschen fuegt
 * hinten wieder ein) und zaehlt bei einer Abweichung die Generation der Art
 * hoch. Id-Abhaengigkeiten werden direkt an der Identitaet geprueft.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * GRENZEN (benannt)
 *
 * - Wer eine Entitaet AN ORT UND STELLE veraendert (statt per Patch ein
 *   neues Objekt zu setzen), wird nicht erkannt. Das bricht schon Undo und
 *   Journal; die Korrektheitsprobe faehrt darum echte Befehle.
 * - Ableitungen duerfen nur vom Dokument abhaengen. Globale Zustaende (der
 *   manifold-Kern) wirken nur in `solidOperationenAnwenden`, und das liegt
 *   bewusst AUSSERHALB des Caches.
 * - Ein Ergebnis wird als dasselbe Objekt wiedergegeben. Wer Artefakte
 *   veraendert oder ihre Puffer transferiert, darf das nur mit einem
 *   frischen Dokument tun (der Derive-Worker baut je Nachricht eines aus
 *   `fromJSON` — fremde Objekte, also nie ein Treffer).
 *
 * Schalter: `ableitungsCacheSchalten(false)` — fuer die Vergleichsprobe und
 * als Notbremse. Aus heisst: der Stand vor R35, Bit fuer Bit.
 *
 * Proben: `test/r35-ableitungs-cache.test.ts`.
 */

let cacheAn = true;

/** Ableitungs-Cache ein- oder ausschalten (Notbremse, Vergleichsprobe). Aus = Stand vor R35. */
export function ableitungsCacheSchalten(an: boolean): void {
  cacheAn = an;
}

export function ableitungsCacheAn(): boolean {
  return cacheAn;
}

const NICHT_GELESEN = -1;
const KEINE_EINSTELLUNG: unique symbol = Symbol('nicht gelesen');

/**
 * Eine Art, von der die Ableitung nur die NACHBARN braucht (Gehrung,
 * T-Stoss, Oeffnungen im Wirt): `relevant` sagt fuer ein Objekt dieser Art,
 * ob es das Ergebnis beeinflussen KANN. Es wird fuer die alte UND die neue
 * Fassung jedes geaenderten Objekts gefragt; im Zweifel muss es `true`
 * sagen. `doc` ist das aktuelle Dokument (fuer Nachschlagen, z.B. Dicke).
 */
export type Relevanz = (e: Entity, doc: KosmoDoc) => boolean;

interface GefilterteArt {
  art: string;
  gen: number;
  relevant: Relevanz;
}

interface Abhaengigkeiten {
  ids: Map<string, Entity | undefined>;
  arten: Map<string, number>;
  gefiltert: GefilterteArt[];
  alle: number;
  settings: unknown;
  revision: number;
  /** Die Ableitung hat ins Dokument geschrieben — nie wiederverwenden. */
  unbrauchbar: boolean;
}

function neueAbhaengigkeiten(): Abhaengigkeiten {
  return { ids: new Map(), arten: new Map(), gefiltert: [], alle: NICHT_GELESEN, settings: KEINE_EINSTELLUNG, revision: NICHT_GELESEN, unbrauchbar: false };
}

function vereinen(ziel: Abhaengigkeiten, q: Abhaengigkeiten): void {
  for (const [id, e] of q.ids) ziel.ids.set(id, e);
  for (const [k, g] of q.arten) ziel.arten.set(k, g);
  for (const f of q.gefiltert) ziel.gefiltert.push(f);
  if (q.alle !== NICHT_GELESEN) ziel.alle = q.alle;
  if (q.settings !== KEINE_EINSTELLUNG) ziel.settings = q.settings;
  if (q.revision !== NICHT_GELESEN) ziel.revision = q.revision;
  if (q.unbrauchbar) ziel.unbrauchbar = true;
}

interface Eintrag {
  wert: unknown;
  ab: Abhaengigkeiten;
}

interface Zustand {
  doc: KosmoDoc | null;
  revision: number;
  voll: Entity[];
  jeArt: Map<string, Entity[]>;
  gen: Map<string, number>;
  alleGen: number;
  eintraege: Map<string, Eintrag>;
  /**
   * Aenderungsbuch je Art: welche Objekte (alte und neue Fassungen) mit
   * welcher Generation dazu- oder weggekommen sind; `null` = nur die
   * Reihenfolge hat sich geaendert (gilt fuer jede gefilterte Abhaengigkeit).
   */
  buch: Map<string, { takt: number; e: Entity | null }[]>;
  /** Bis zu diesem Takt ist das Buch gekuerzt — aeltere Eintraege gelten als ungueltig. */
  buchAb: Map<string, number>;
}

let takt = 0;

const ZUSTAND = new WeakMap<KosmoDoc, Zustand>();
const SICHT_ZUSTAND = new WeakMap<KosmoDoc, Zustand>();
const SICHT_QUELLE = new WeakMap<KosmoDoc, KosmoDoc>();

/**
 * `docFuerArbeitsansicht` baut bei aktiven Ebenen je Revision eine neue
 * Sicht (geteilte Entitaeten). Ohne diese Verknuepfung haette jede Sicht
 * einen eigenen, leeren Cache. Nur Leistung: die Gueltigkeit haengt nie
 * an der Dokument-Identitaet, nur an den gelesenen Objekten.
 */
export function ableitungsSichtVerknuepfen(sicht: KosmoDoc, quelle: KosmoDoc): void {
  if (sicht !== quelle) SICHT_QUELLE.set(sicht, quelle);
}

function zustandFuer(doc: KosmoDoc): Zustand {
  const quelle = SICHT_QUELLE.get(doc);
  const tabelle = quelle ? SICHT_ZUSTAND : ZUSTAND;
  const schluessel = quelle ?? doc;
  let z = tabelle.get(schluessel);
  if (!z) {
    z = { doc: null, revision: NICHT_GELESEN, voll: [], jeArt: new Map(), gen: new Map(), alleGen: 0, eintraege: new Map(), buch: new Map(), buchAb: new Map() };
    tabelle.set(schluessel, z);
  }
  return z;
}

function gleicheFolge(a: readonly Entity[], b: readonly Entity[] | undefined): boolean {
  if (!b || a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

/** Stand des Dokuments mit dem letzten vergleichen; geaenderte Arten bekommen eine neue Generation. */
function abgleichen(z: Zustand, doc: KosmoDoc): void {
  const voll = [...doc.entities.values()];
  const jeArt = new Map<string, Entity[]>();
  for (const e of voll) {
    const l = jeArt.get(e.kind);
    if (l) l.push(e);
    else jeArt.set(e.kind, [e]);
  }
  let geaendert = false;
  for (const [k, l] of jeArt) {
    const alt = z.jeArt.get(k);
    if (!gleicheFolge(l, alt)) {
      z.gen.set(k, ++takt);
      geaendert = true;
      if (z.doc !== null) buchen(z, k, alt ?? [], l);
    }
  }
  for (const [k, alt] of z.jeArt) {
    if (!jeArt.has(k)) {
      z.gen.set(k, ++takt);
      geaendert = true;
      buchen(z, k, alt, []);
    }
  }
  if (geaendert || !gleicheFolge(voll, z.voll)) z.alleGen = ++takt;
  z.voll = voll;
  z.jeArt = jeArt;
  z.doc = doc;
  z.revision = doc.revision;
  // Vorrat begrenzen: Eintraege geloeschter Bauteile wuerden sonst bleiben.
  if (z.eintraege.size > 4 * voll.length + 1024) z.eintraege.clear();
}

const BUCH_DECKEL = 4096;

/** Aenderungen einer Art ins Buch: weggefallene und neue Objekte, dazu ein Reihenfolge-Vermerk. */
function buchen(z: Zustand, k: string, alt: readonly Entity[], neu: readonly Entity[]): void {
  let b = z.buch.get(k);
  if (!b) {
    b = [];
    z.buch.set(k, b);
  }
  const neuMenge = new Set(neu);
  const altMenge = new Set(alt);
  const altBleibt: Entity[] = [];
  for (const e of alt) {
    if (neuMenge.has(e)) altBleibt.push(e);
    else b.push({ takt, e });
  }
  const neuBleibt: Entity[] = [];
  for (const e of neu) {
    if (altMenge.has(e)) neuBleibt.push(e);
    else b.push({ takt, e });
  }
  if (!gleicheFolge(altBleibt, neuBleibt)) b.push({ takt, e: null });
  if (b.length > BUCH_DECKEL) {
    const weg = b.splice(0, b.length - BUCH_DECKEL / 2);
    z.buchAb.set(k, weg[weg.length - 1]!.takt);
  }
}

/** Hat sich seit Generation `gen` ein fuer `relevant` erhebliches Objekt der Art geaendert? */
function gefiltertGueltig(f: GefilterteArt, doc: KosmoDoc, z: Zustand): boolean {
  if ((z.gen.get(f.art) ?? 0) === f.gen) return true;
  if ((z.buchAb.get(f.art) ?? 0) >= f.gen) return false;
  const b = z.buch.get(f.art);
  if (!b) return false;
  for (let i = b.length - 1; i >= 0; i--) {
    const x = b[i]!;
    if (x.takt <= f.gen) break;
    if (x.e === null || f.relevant(x.e, doc)) return false;
  }
  return true;
}

function gueltig(ab: Abhaengigkeiten, doc: KosmoDoc, z: Zustand): boolean {
  if (ab.unbrauchbar) return false;
  if (ab.revision !== NICHT_GELESEN && ab.revision !== doc.revision) return false;
  if (ab.settings !== KEINE_EINSTELLUNG && ab.settings !== doc.settings) return false;
  if (ab.alle !== NICHT_GELESEN && ab.alle !== z.alleGen) return false;
  for (const [k, g] of ab.arten) if ((z.gen.get(k) ?? 0) !== g) return false;
  for (const [id, e] of ab.ids) if (doc.entities.get(id) !== e) return false;
  for (const f of ab.gefiltert) if (!gefiltertGueltig(f, doc, z)) return false;
  return true;
}

interface Protokoll {
  ziel: KosmoDoc;
  ab: Abhaengigkeiten;
  z: Zustand;
}

const PROTOKOLLE = new WeakMap<object, Protokoll>();

function protokollDoc(ziel: KosmoDoc, ab: Abhaengigkeiten, z: Zustand): KosmoDoc {
  const art = (k: string): void => {
    ab.arten.set(k, z.gen.get(k) ?? 0);
  };
  const allesGelesen = (): void => {
    ab.alle = z.alleGen;
  };
  const p = new Proxy(ziel, {
    get(t, name) {
      switch (name) {
        case 'get':
          return (id: string) => {
            const e = t.entities.get(id);
            ab.ids.set(id, e);
            return e;
          };
        case 'byKind':
          return (k: string) => {
            art(k);
            return t.byKind(k as Entity['kind']);
          };
        case 'storeysOrdered':
          return () => {
            art('storey');
            return t.storeysOrdered();
          };
        case 'storeyTop':
          return (id: string) => {
            ab.ids.set(id, t.entities.get(id));
            return t.storeyTop(id);
          };
        case 'openingsOf':
          return (wallId: string) => {
            ab.gefiltert.push({ art: 'opening', gen: z.gen.get('opening') ?? 0, relevant: (o) => o.kind === 'opening' && o.wallId === wallId });
            return t.openingsOf(wallId);
          };
        case 'inStorey':
          return (storeyId: string) => {
            allesGelesen();
            return t.inStorey(storeyId);
          };
        case 'entities':
          allesGelesen();
          return t.entities;
        case 'settings':
          ab.settings = t.settings;
          return t.settings;
        case 'revision':
          ab.revision = t.revision;
          return t.revision;
        default: {
          // Unbekannt: konservativ — das ganze Dokument samt Einstellungen gilt als gelesen.
          allesGelesen();
          ab.settings = t.settings;
          const v: unknown = Reflect.get(t, name, t);
          return typeof v === 'function' ? (v as (...a: unknown[]) => unknown).bind(t) : v;
        }
      }
    },
    set(t, name, wert) {
      ab.unbrauchbar = true;
      return Reflect.set(t, name, wert, t);
    },
  });
  PROTOKOLLE.set(p, { ziel, ab, z });
  return p;
}

/**
 * `doc.byKind(art)` fuer eine Ableitung, die nur die Nachbarn dieser Art
 * braucht: im Cache wird statt der ganzen Art nur festgehalten, was
 * `relevant` als erheblich bezeichnet (alte und neue Fassung). Ausserhalb
 * einer gemerkten Ableitung (oder bei ausgeschaltetem Cache) schlicht
 * `byKind`. Die Liste ist dieselbe — die Ableitung rechnet unveraendert.
 */
export function nachbarnDerArt<T extends Entity>(doc: KosmoDoc, art: T['kind'], relevant: Relevanz): T[] {
  const p = PROTOKOLLE.get(doc);
  if (!p) return doc.byKind<T>(art);
  p.ab.gefiltert.push({ art, gen: p.z.gen.get(art) ?? 0, relevant });
  return p.ziel.byKind<T>(art);
}

/**
 * Erzwingt den Abgleich (am Anfang eines Gesamtdurchgangs wie `deriveAll`):
 * so fallen auch Aenderungen auf, die ohne `apply` (ohne neue Revision)
 * direkt an `doc.entities` gemacht wurden.
 */
export function ableitungsDurchgang(doc: KosmoDoc): void {
  if (!cacheAn || PROTOKOLLE.has(doc)) return;
  abgleichen(zustandFuer(doc), doc);
}

/**
 * Ergebnis einer Ableitung je Schluessel wiederverwenden, solange alles,
 * was sie gelesen hat, unveraendert ist. `rechne` bekommt das Protokoll-
 * Dokument und darf NUR daraus lesen. `teil`: ein Bauteil, das die Ableitung
 * von aussen bekommt (Schleife einer Gruppe) — es wird wie ein `get` erfasst.
 *
 * Bei ausgeschaltetem Cache: `rechne(doc)` ohne jedes Merken.
 */
export function gemerkt<T>(doc: KosmoDoc, schluessel: string, rechne: (d: KosmoDoc) => T, teil?: Entity): T {
  if (!cacheAn) return rechne(doc);
  const aussen = PROTOKOLLE.get(doc);
  const echt = aussen ? aussen.ziel : doc;
  const z = aussen ? aussen.z : zustandFuer(echt);
  if (!aussen && (z.doc !== echt || z.revision !== echt.revision)) abgleichen(z, echt);
  const hit = z.eintraege.get(schluessel);
  if (hit && gueltig(hit.ab, echt, z)) {
    if (aussen) vereinen(aussen.ab, hit.ab);
    return hit.wert as T;
  }
  const ab = neueAbhaengigkeiten();
  if (teil) ab.ids.set(teil.id, teil);
  const wert = rechne(protokollDoc(echt, ab, z));
  if (teil && echt.entities.get(teil.id) !== teil) ab.unbrauchbar = true;
  z.eintraege.set(schluessel, { wert, ab });
  if (aussen) vereinen(aussen.ab, ab);
  return wert;
}

/** Nur fuer Proben: wie viele Eintraege der Cache fuer dieses Dokument haelt. */
export function ableitungsCacheGroesse(doc: KosmoDoc): number {
  return zustandFuer(doc).eintraege.size;
}
