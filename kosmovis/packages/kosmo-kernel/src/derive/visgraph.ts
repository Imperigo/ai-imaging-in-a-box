import type { KosmoDoc } from '../model/doc';
import type { VisEdge, VisGraph, VisNode, VisPortTyp } from '../model/entities';
import { finalerRenderPrompt, renderPromptBausteine } from './renderprompt';
import { projektKameras, type AutoKameraStandpunkt } from './kamera';
import { isVisPresetId, visPresetById, type VisPresetId } from './render-presets';

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

/** Die Stimmungs-Presets — identisch mit der bisherigen Serien-Logik. */
export const VIS_STIMMUNGEN: Record<string, { label: string; prompt: string }> = {
  morgen: { label: 'Morgenlicht', prompt: 'Morgenlicht, klare lange Schatten, frische kühle Luft' },
  abend: { label: 'Abendstimmung', prompt: 'Abendstimmung, warmes Licht, leuchtende Fenster' },
  weiss: { label: 'Weissmodell', prompt: 'Weissmodell, neutrales Studiolicht, keine Materialien' },
};

/** Katalog der 12 Node-Typen — deckt alle heutigen KosmoVis-Fähigkeiten. */
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
  material: {
    typ: 'material',
    label: 'Material-Bausteine',
    hilfe: 'Liest die äussersten Wandschichten + Fassadenmodule als Prompt-Phrasen (V8).',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'material', typ: 'material', label: 'Material' }],
    defaults: {},
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
    hilfe: 'Preset Morgenlicht / Abendstimmung / Weissmodell.',
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
    ],
    outputs: [{ name: 'bild', typ: 'bild', label: 'Bild' }],
    defaults: {},
  },
  kamera: {
    typ: 'kamera',
    label: 'Auto-Kamera',
    // P-DREISTANDPUNKTE (HomeStation-Befund, auftraege/von-homestation/
    // auf-orbit-20260821-01.md, Auftrag 3): der Text nannte «ggf. Innenraum»
    // ohne zu sagen, dass er nie ankommt — genau das Versprechen, das der
    // Befund beanstandet hat. `deriveAutoKameras` leitet ihn weiterhin ab
    // (bei vorhandenen Zonen), aber `postRenderJob` (vis-jobs.ts) filtert
    // ihn vor dem Senden heraus: Innenansichten sind seit P-INTERIOR
    // (ROADMAP 1071) an `interior`/IFC gebunden, dieser Weg sendet immer
    // glb. Der Zusatz macht das jetzt ehrlich, statt es nur zu verschweigen.
    hilfe:
      'Leitet benannte Standpunkte (Eingang/Übersicht/ggf. Innenraum) regelbasiert aus den Modell-Bounds ab — Vorschlag aus dem Modell, keine KI-Wahl. Mit dem Render-Node verbinden. Bestellt wird nur Eingang/Übersicht: eine Innenansicht ist an interior/IFC gebunden, dieser Weg sendet nur glb-Geometrie.',
    kategorie: 'quelle',
    inputs: [],
    outputs: [{ name: 'kameras', typ: 'kameras', label: 'Kamera-Standpunkte' }],
    defaults: {},
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
};

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
        const preset = VIS_STIMMUNGEN[String(params['preset'] ?? 'morgen')];
        werte.set(n.id, { prompt: preset?.prompt ?? '' });
        break;
      }
      case 'material':
        werte.set(n.id, { material: renderPromptBausteine(doc).join(', ') });
        break;
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
        const hatKameras = graph.edges.some((e) => e.to === n.id && e.toPort === 'kameras');
        const kameras = hatKameras ? projektKameras(doc) : [];
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
        });
        break;
      }
      case 'kamera':
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
