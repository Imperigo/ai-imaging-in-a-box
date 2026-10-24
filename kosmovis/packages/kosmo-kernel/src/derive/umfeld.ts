import type { VisGraph, VisNode } from '../model/entities';

/**
 * Knoten «Umfeld» (Visbox-Owner-Wunsch 24.10.2026, Blatt 57 der Entwurfsfläche): Bäume, Büsche,
 * Wiese, Strasse und Autos um das Haus — aus freien 3D-Modellen (nur CC0), geladen und gestellt am
 * Heim-PC. Der Knoten sitzt zwischen «Modell» und Render (Szene hinein, Szene mit Umfeld hinaus) und
 * bestellt nur den WUNSCH: was, wie dicht, welche Anordnung. Welche Stücke wo stehen, rechnet der
 * Heim-PC am Modell (`aiimaging.umfeld.plane_fuer_glb`): nie im Haus, nie im Blick der Kameras auf das
 * Haus. Die Bestellung ist `vis.umfeld` (`render-scene.ts`).
 *
 * Der Katalog unten ist eine Kopie des Katalogs des Heim-PC (`aiimaging.umfeld.ASSETS`, Anzeige-Felder);
 * die Visbox-Probe `tests/test_umfeld_katalog.py` haelt beide gleich. Er dient nur der Anzeige am
 * Knoten (was geladen wuerde, woher, unter welcher Lizenz) — gewaehlt wird am Heim-PC.
 */

export const UMFELD_TYP = 'umfeld';

export const VIS_UMFELD_KATEGORIEN = [
  { id: 'baeume', label: 'Bäume' },
  { id: 'buesche', label: 'Büsche' },
  { id: 'wiese', label: 'Wiese' },
  { id: 'strasse', label: 'Strasse' },
  { id: 'autos', label: 'Autos' },
] as const;
export type UmfeldKategorie = (typeof VIS_UMFELD_KATEGORIEN)[number]['id'];

export const VIS_UMFELD_DICHTEN = ['wenig', 'mittel', 'viel'] as const;
export type UmfeldDichte = (typeof VIS_UMFELD_DICHTEN)[number];
export const UMFELD_DICHTE_VORGABE: UmfeldDichte = 'mittel';
/** Höchstzahl je Kategorie, die eine Bestellung ausdrücklich nennen darf (`anzahl`). */
export const UMFELD_ANZAHL_HOECHSTENS = 30;
export const UMFELD_ZAEHLBAR = ['baeume', 'buesche', 'autos'] as const;
export type UmfeldZaehlbar = (typeof UMFELD_ZAEHLBAR)[number];

export interface UmfeldAsset {
  id: string;
  kategorie: UmfeldKategorie;
  label: string;
  quelle: string;
  lizenz: 'CC0-1.0';
  seite: string;
  mb: number;
  vorgabe: boolean;
}

/** Kopie von `aiimaging.umfeld.katalog_fuer_anzeige()` — gleich gehalten von der Visbox-Probe. */
export const VIS_UMFELD_KATALOG: readonly UmfeldAsset[] = [
  { id: 'tree_small_02', kategorie: 'baeume', label: 'Laubbaum', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/tree_small_02', mb: 101.0, vorgabe: true },
  { id: 'island_tree_02', kategorie: 'baeume', label: 'Laubbaum, licht', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/island_tree_02', mb: 46.2, vorgabe: true },
  { id: 'jacaranda_tree', kategorie: 'baeume', label: 'Grosser Laubbaum', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/jacaranda_tree', mb: 214.6, vorgabe: false },
  { id: 'searsia_lucida', kategorie: 'buesche', label: 'Busch', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/searsia_lucida', mb: 19.8, vorgabe: true },
  { id: 'shrub_02', kategorie: 'buesche', label: 'Strauch', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/shrub_02', mb: 2.0, vorgabe: true },
  { id: 'kenney-sedan', kategorie: 'autos', label: 'Limousine', quelle: 'Kenney', lizenz: 'CC0-1.0', seite: 'https://kenney.nl/assets/car-kit', mb: 4.8, vorgabe: true },
  { id: 'kenney-suv', kategorie: 'autos', label: 'Geländewagen', quelle: 'Kenney', lizenz: 'CC0-1.0', seite: 'https://kenney.nl/assets/car-kit', mb: 4.8, vorgabe: true },
  { id: 'kenney-van', kategorie: 'autos', label: 'Lieferwagen', quelle: 'Kenney', lizenz: 'CC0-1.0', seite: 'https://kenney.nl/assets/car-kit', mb: 4.8, vorgabe: false },
  { id: 'covered_car', kategorie: 'autos', label: 'Abgedecktes Auto', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/covered_car', mb: 2.3, vorgabe: false },
  { id: 'Grass004', kategorie: 'wiese', label: 'Rasen', quelle: 'ambientCG', lizenz: 'CC0-1.0', seite: 'https://ambientcg.com/view?id=Grass004', mb: 11.0, vorgabe: true },
  { id: 'asphalt_02', kategorie: 'strasse', label: 'Asphalt', quelle: 'Poly Haven', lizenz: 'CC0-1.0', seite: 'https://polyhaven.com/a/asphalt_02', mb: 2.9, vorgabe: true },
];

/**
 * Der Satz zur Lizenz am Knoten. Visbox-Owner-Entscheid 147 (24.10.2026): CC0 gilt auch für 3D-Modelle, wie für
 * Texturen — am Heim-PC geladen, nie ausgeliefert; Modelle nur aus Poly Haven, Kenney und Quaternius (kein CC-BY,
 * kein Sketchfab). Der Heim-PC lädt darum von sich aus; er kann es mit einem Schalter abstellen.
 */
export const UMFELD_SATZ_LIZENZ = 'Nur gemeinfreie Modelle (CC0) aus Poly Haven, Kenney und Quaternius — nichts davon wird ausgeliefert.';

/** Der Wunsch, wie er bestellt wird (`RenderScene.vis.umfeld`). */
export interface UmfeldWahl {
  kategorien: UmfeldKategorie[];
  dichte: UmfeldDichte;
  seed: number;
  anzahl?: Partial<Record<UmfeldZaehlbar, number>>;
}

type Params = Record<string, string | number | boolean>;

function liesJson(roh: unknown): unknown {
  if (typeof roh !== 'string' || !roh.trim()) return undefined;
  try {
    return JSON.parse(roh);
  } catch {
    return undefined;
  }
}

/** Die gewählten Kategorien am Knoten — in fester Reihenfolge, Unbekanntes fällt weg. */
export function umfeldKategorien(params: Params | undefined): UmfeldKategorie[] {
  const roh = liesJson(params?.['kategorien']);
  const liste = Array.isArray(roh) ? roh.filter((x): x is string => typeof x === 'string') : [];
  return VIS_UMFELD_KATEGORIEN.map((k) => k.id).filter((id) => liste.includes(id));
}

/** Der Wunsch aus den Parametern — `null`, wenn keine Kategorie gewählt ist (dann bestellt der Knoten nichts). */
export function umfeldAusParams(params: Params | undefined): UmfeldWahl | null {
  const kategorien = umfeldKategorien(params);
  if (kategorien.length === 0) return null;
  const dichteRoh = params?.['dichte'];
  const dichte = (VIS_UMFELD_DICHTEN as readonly string[]).includes(String(dichteRoh)) ? (dichteRoh as UmfeldDichte) : UMFELD_DICHTE_VORGABE;
  const seedRoh = Number(params?.['seed'] ?? 0);
  const seed = Number.isInteger(seedRoh) && seedRoh >= 0 && seedRoh <= 2147483647 ? seedRoh : 0;
  const anzahlRoh = liesJson(params?.['anzahl']);
  const anzahl: Partial<Record<UmfeldZaehlbar, number>> = {};
  if (anzahlRoh && typeof anzahlRoh === 'object' && !Array.isArray(anzahlRoh)) {
    for (const k of UMFELD_ZAEHLBAR) {
      const v = (anzahlRoh as Record<string, unknown>)[k];
      if (typeof v === 'number' && Number.isInteger(v) && v >= 0 && v <= UMFELD_ANZAHL_HOECHSTENS && kategorien.includes(k)) anzahl[k] = v;
    }
  }
  return { kategorien, dichte, seed, ...(Object.keys(anzahl).length > 0 ? { anzahl } : {}) };
}

/** Parameter aus einem Wunsch — für `vis.nodeParametrieren` und `vis.umfeldSetzen`. */
export function umfeldParams(w: {
  kategorien: readonly string[];
  dichte?: string | undefined;
  seed?: number | undefined;
  anzahl?: Partial<Record<string, number | undefined>> | undefined;
}): Params {
  const kategorien = VIS_UMFELD_KATEGORIEN.map((k) => k.id).filter((id) => w.kategorien.includes(id));
  return {
    kategorien: JSON.stringify(kategorien),
    dichte: (VIS_UMFELD_DICHTEN as readonly string[]).includes(String(w.dichte)) ? String(w.dichte) : UMFELD_DICHTE_VORGABE,
    seed: Number.isInteger(w.seed) && (w.seed as number) >= 0 ? (w.seed as number) : 0,
    anzahl: (() => {
      const fest = Object.fromEntries(Object.entries(w.anzahl ?? {}).filter(([, v]) => typeof v === 'number'));
      return Object.keys(fest).length > 0 ? JSON.stringify(fest) : '';
    })(),
  };
}

/** Was der Heim-PC für diesen Wunsch laden würde (die Vorgaben je Kategorie) — für die Liste am Knoten. */
export function umfeldAssets(w: UmfeldWahl | null): UmfeldAsset[] {
  if (!w) return [];
  return VIS_UMFELD_KATALOG.filter((a) => a.vorgabe && w.kategorien.includes(a.kategorie));
}

/** Rund so viele MB lädt der Heim-PC einmal (ein Paket zählt einmal, auch für zwei Autos). */
export function umfeldLadeMb(w: UmfeldWahl | null): number {
  const gesehen = new Set<string>();
  let mb = 0;
  for (const a of umfeldAssets(w)) {
    const schluessel = a.quelle === 'Kenney' ? 'kenney-car-kit' : a.id;
    if (gesehen.has(schluessel)) continue;
    gesehen.add(schluessel);
    mb += a.mb;
  }
  return Math.round(mb);
}

/** Die Kategorien als Wort für Karten und Satz: «Bäume, Autos (2), Strasse». */
export function umfeldWort(w: UmfeldWahl | null): string {
  if (!w) return 'nichts gewählt';
  return w.kategorien
    .map((k) => {
      const label = VIS_UMFELD_KATEGORIEN.find((x) => x.id === k)?.label ?? k;
      const n = w.anzahl?.[k as UmfeldZaehlbar];
      return n !== undefined ? `${label} (${n})` : label;
    })
    .join(', ');
}

/** Der Satz, was geladen würde: «Lädt einmal am Heim-PC, rund 190 MB, alles gemeinfrei (CC0).» */
export function umfeldLadeSatz(w: UmfeldWahl | null): string {
  const assets = umfeldAssets(w);
  if (assets.length === 0) return 'Nichts gewählt — der Knoten lässt die Szene, wie sie ist.';
  const quellen = [...new Set(assets.map((a) => a.quelle))].join(', ');
  return `Lädt einmal am Heim-PC von ${quellen}, rund ${umfeldLadeMb(w)} MB, alles gemeinfrei (CC0). Danach ohne Netz.`;
}

/** Der Umfeld-Knoten, dessen Szene in den Render-Knoten fliesst — direkt vor ihm am Eingang «Szene». */
export function umfeldVorRender(graph: VisGraph, renderId: string): VisNode | undefined {
  const kante = graph.edges.find((e) => e.to === renderId && e.toPort === 'szene');
  const quelle = kante ? graph.nodes.find((n) => n.id === kante.from) : undefined;
  return quelle?.typ === UMFELD_TYP ? quelle : undefined;
}
