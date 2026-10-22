import { z } from 'zod';
import { newId } from '../model/ids';
import type { VisEdge, VisGraph, VisNode } from '../model/entities';
import type { KosmoDoc, VisRenderWunsch } from '../model/doc';
import { hatZyklus, stimmungAufruf, visPort, VIS_NODE_KATALOG, VIS_STIMMUNG_IDS, VIS_STIMMUNGEN } from '../derive/visgraph';
import {
  findeVariantenKnotenIn,
  gewaehlteAchsen,
  schreibeListe,
  VARIANTEN_TYP,
  variantenAchsenSatz,
  variantenAnzahl,
  variantenRenderKnoten,
  variantenStandLesen,
  variantenWarnt,
  variantenZaehlerSatz,
  verfuegbareEntwuerfe,
  verfuegbareStandpunkte,
  type VariantenAchsen,
} from '../derive/varianten';
import { CommandError, registerCommand } from './core';
import { knotenWort, neuerKnotenZeile, parameterZeile, renderZeile, trennenZeile, verbindenZeile } from '../derive/vis-kartenzeile';

/**
 * Vis-Commands (V1-Finish P2) — der Render-Graph läuft über denselben
 * Command-Weg wie jedes Bauteil: Undo, Yjs, Journal, und Kosmo kann
 * Render-Graphen SPRECHEN (jedes Schema wird automatisch LLM-Tool).
 */

const ParamWert = z.union([z.string(), z.number(), z.boolean()]);

function requireGraph(doc: KosmoDoc, id: string): VisGraph {
  const e = doc.get<VisGraph>(id);
  if (!e || e.kind !== 'visgraph') throw new CommandError(`Render-Graph «${id}» existiert nicht`);
  merkeGraph(doc, e);
  return e;
}

/**
 * Kartenzeile mit Vorher → Nachher (Visbox-Owner-Entscheid 22.10.2026, `derive/vis-kartenzeile.ts`):
 * `execute()` ruft `summarize` erst NACH `doc.apply`, der Vorher-Wert steht dann nicht mehr im
 * Dokument. Darum merkt sich `requireGraph` den Graphen, den `run` gelesen hat, und `summarize`
 * nimmt ihn genau einmal (`vorherGraph`). Kein Zustand des Projekts, nur der Satz der Karte.
 */
const GELESEN = new WeakMap<KosmoDoc, Map<string, VisGraph>>();

function merkeGraph(doc: KosmoDoc, g: VisGraph): void {
  let m = GELESEN.get(doc);
  if (!m) GELESEN.set(doc, (m = new Map()));
  m.set(g.id, g);
}

/** Der Graph vor dem Lauf: der gemerkte, sonst der im Dokument (Probelauf ohne Änderung). */
function vorherGraph(doc: KosmoDoc | undefined, graphId: string): VisGraph | undefined {
  if (!doc) return undefined;
  const gemerkt = GELESEN.get(doc)?.get(graphId);
  GELESEN.get(doc)?.delete(graphId);
  const jetzt = doc.get<VisGraph>(graphId);
  return gemerkt ?? (jetzt?.kind === 'visgraph' ? jetzt : undefined);
}

function knotenIn(g: VisGraph | undefined, nodeId: string): VisNode | undefined {
  return g?.nodes.find((n) => n.id === nodeId);
}

function requireNode(graph: VisGraph, nodeId: string): VisNode {
  const n = graph.nodes.find((n) => n.id === nodeId);
  if (!n) throw new CommandError(`Node «${nodeId}» existiert nicht im Graphen`);
  return n;
}

export const createGraph = registerCommand({
  id: 'vis.graphErstellen',
  title: 'Render-Graph erstellen',
  description:
    'Erstellt einen leeren Render-Graphen (Node-Tree) in KosmoVis. Nodes kommen mit vis_nodeSetzen dazu, Verbindungen mit vis_verbinden.',
  params: z.object({ name: z.string().min(1).describe('z.B. «Wettbewerbsbilder»') }),
  summarize: (p) => `Neuer Render-Graph «${p.name}»`,
  run: (_doc, p) => {
    const graph: VisGraph = { id: newId('visgraph'), kind: 'visgraph', name: p.name, nodes: [], edges: [] };
    return [{ id: graph.id, before: null, after: graph }];
  },
});

export const addNode = registerCommand({
  id: 'vis.nodeSetzen',
  title: 'Node setzen',
  description: `Setzt einen Node in den Render-Graphen. Typen: ${Object.values(VIS_NODE_KATALOG)
    .map((t) => `${t.typ} (${t.hilfe})`)
    .join('; ')}`,
  params: z.object({
    graphId: z.string(),
    typ: z.string().describe('Node-Typ aus dem Katalog, z.B. «render»'),
    x: z.number().describe('Canvas-X'),
    y: z.number().describe('Canvas-Y'),
    params: z.record(z.string(), ParamWert).optional(),
  }),
  summarize: (p, doc) => {
    vorherGraph(doc, p.graphId);
    return neuerKnotenZeile(p.typ, p.params);
  },
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const kat = VIS_NODE_KATALOG[p.typ];
    if (!kat) {
      throw new CommandError(`Unbekannter Node-Typ «${p.typ}» — Katalog: ${Object.keys(VIS_NODE_KATALOG).join(', ')}`);
    }
    const node: VisNode = {
      id: newId('node'),
      typ: p.typ,
      x: p.x,
      y: p.y,
      params: { ...kat.defaults, ...stimmungsParams(p.typ, p.params ?? {}) },
    };
    const after: VisGraph = { ...graph, nodes: [...graph.nodes, node] };
    return [{ id: graph.id, before: graph, after }];
  },
});

/**
 * Die acht Stimmungen als Satz fuer die Werkzeugbeschreibungen (Kennung und Anzeigename), aus
 * `VIS_STIMMUNGEN` — nie doppelt gepflegt. Anlass (Visbox, erster Claude-Lauf am Mac, 21.10.2026):
 * Claude kannte nur «morgen/abend/weiss», weil die Beschreibungen die Stimmungen nicht nannten.
 */
export const STIMMUNGEN_SATZ = VIS_STIMMUNG_IDS.map((id) => `${id} (${VIS_STIMMUNGEN[id]?.label ?? id})`).join(', ');

/**
 * Der Satz zum Stimmung-Knoten an `vis.nodeParametrieren` und `vis.nodeSetzen` — er sagt, was
 * `stimmungAufruf` tut (Visbox-Mac-Befund 0.3.33: Claude setzte nur `preset`, gerendert wurde die
 * alte Liste). Eine Probe haelt Satz und Verhalten zusammen (`kv-stimmung-preset.test.ts`).
 */
export const STIMMUNG_PARAM_SATZ =
  `Stimmung-Knoten: preset = EINE Stimmung, ersetzt die ganze Wahl; presets = mehrere als Text mit JSON-Liste, z.B. '["abend","nebel"]' (gewinnt vor preset, die erste in Katalog-Reihenfolge bestellt der Render-Knoten). Beide werden immer zusammen gesetzt. Stimmungen: ${STIMMUNGEN_SATZ}.`;

/** `params` eines Aufrufs am Stimmung-Knoten durch `stimmungAufruf` — Fehler als CommandError. */
function stimmungsParams(typ: string, params: Record<string, string | number | boolean>): Record<string, string | number | boolean> {
  if (typ !== 'stimmung') return params;
  const r = stimmungAufruf(params);
  if ('fehler' in r) throw new CommandError(r.fehler);
  return r.params;
}

export const setNodeParams = registerCommand({
  id: 'vis.nodeParametrieren',
  title: 'Node parametrieren',
  description:
    `Setzt Parameter eines Nodes (mischt in die bestehenden), z.B. den Text eines Prompt-Nodes, die Stimmung eines Stimmung-Nodes oder den Wert eines Zahl-Nodes. ${STIMMUNG_PARAM_SATZ}`,
  params: z.object({
    graphId: z.string(),
    nodeId: z.string(),
    params: z.record(z.string(), ParamWert),
  }),
  summarize: (p, doc) => {
    const vorher = knotenIn(vorherGraph(doc, p.graphId), p.nodeId);
    return parameterZeile(vorher, p.params, vorher?.params);
  },
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    // Am Stimmung-Knoten setzt `preset` die Liste `presets` mit (und umgekehrt) — s. `stimmungAufruf`.
    const neu = stimmungsParams(node.typ, p.params);
    const after: VisGraph = {
      ...graph,
      // ?? {} statt n.params direkt: ein Node ohne params (Alt-Stand/Import)
      // darf hier nicht in einen halbkaputten Zustand gemischt werden.
      nodes: graph.nodes.map((n) => (n.id === node.id ? { ...n, params: { ...(n.params ?? {}), ...neu } } : n)),
    };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const moveNode = registerCommand({
  id: 'vis.nodeSchieben',
  title: 'Node schieben',
  description: 'Verschiebt einen Node auf dem Canvas (ein Schritt pro Drag, nie pro Mausbewegung).',
  params: z.object({ graphId: z.string(), nodeId: z.string(), x: z.number(), y: z.number() }),
  summarize: (p, doc) => `Knoten «${knotenWort(knotenIn(vorherGraph(doc, p.graphId), p.nodeId)?.typ)}» verschieben`,
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    const after: VisGraph = {
      ...graph,
      nodes: graph.nodes.map((n) => (n.id === node.id ? { ...n, x: p.x, y: p.y } : n)),
    };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const connect = registerCommand({
  id: 'vis.verbinden',
  title: 'Nodes verbinden',
  description:
    'Verbindet einen Ausgangs-Port mit einem Eingangs-Port (gleicher Typ: szene/bild/prompt/zahl/material). Ein belegter Eingang wird ersetzt (wie in Blender); Zyklen werden ehrlich abgelehnt.',
  params: z.object({
    graphId: z.string(),
    from: z.string().describe('Quell-Node'),
    fromPort: z.string().describe('Ausgangs-Port, z.B. «prompt»'),
    to: z.string().describe('Ziel-Node'),
    toPort: z.string().describe('Eingangs-Port, z.B. «stil»'),
  }),
  summarize: (p, doc) => {
    const g = vorherGraph(doc, p.graphId);
    return verbindenZeile(knotenIn(g, p.from), knotenIn(g, p.to), p.toPort);
  },
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const von = requireNode(graph, p.from);
    const zu = requireNode(graph, p.to);
    if (von.id === zu.id) throw new CommandError('Ein Node kann nicht mit sich selbst verbunden werden');
    const aus = visPort(von.typ, p.fromPort, 'out');
    const ein = visPort(zu.typ, p.toPort, 'in');
    if (!aus) throw new CommandError(`Node ${von.typ} hat keinen Ausgang «${p.fromPort}»`);
    if (!ein) throw new CommandError(`Node ${zu.typ} hat keinen Eingang «${p.toPort}»`);
    if (aus.typ !== ein.typ) {
      throw new CommandError(`Port-Typen passen nicht: ${p.fromPort} ist ${aus.typ}, ${p.toPort} erwartet ${ein.typ}`);
    }
    // Entscheid 96 (Visbox, 15.10.2026): ein Eingang, der nur bestimmte Knotenarten nimmt
    // (`VisPort.nurVon`, heute «Skizze» am Render-Knoten).
    if (ein.nurVon && !ein.nurVon.includes(von.typ)) {
      throw new CommandError(
        `«${ein.label}» nimmt nur ${ein.nurVon.map((t) => `«${VIS_NODE_KATALOG[t]?.label ?? t}»`).join(', ')} — nicht «${VIS_NODE_KATALOG[von.typ]?.label ?? von.typ}»`,
      );
    }
    // Belegter Eingang wird ersetzt — erst dann auf Zyklus prüfen
    const ohneAlte = graph.edges.filter((e) => !(e.to === zu.id && e.toPort === p.toPort));
    if (hatZyklus(graph.nodes, ohneAlte, { from: von.id, to: zu.id })) {
      throw new CommandError('Diese Verbindung ergäbe einen Zyklus — Render-Graphen fliessen nur vorwärts');
    }
    const edge: VisEdge = { id: newId('edge'), from: von.id, fromPort: p.fromPort, to: zu.id, toPort: p.toPort };
    const after: VisGraph = { ...graph, edges: [...ohneAlte, edge] };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const disconnect = registerCommand({
  id: 'vis.trennen',
  title: 'Verbindung trennen',
  description: 'Entfernt eine Verbindung aus dem Render-Graphen.',
  params: z.object({ graphId: z.string(), edgeId: z.string() }),
  summarize: (p, doc) => trennenZeile(vorherGraph(doc, p.graphId), p.edgeId),
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    if (!graph.edges.some((e) => e.id === p.edgeId)) {
      throw new CommandError(`Verbindung «${p.edgeId}» existiert nicht`);
    }
    const after: VisGraph = { ...graph, edges: graph.edges.filter((e) => e.id !== p.edgeId) };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const removeNode = registerCommand({
  id: 'vis.nodeLoeschen',
  title: 'Node löschen',
  description: 'Löscht einen Node samt allen seinen Verbindungen.',
  params: z.object({ graphId: z.string(), nodeId: z.string() }),
  summarize: (p, doc) => `Knoten «${knotenWort(knotenIn(vorherGraph(doc, p.graphId), p.nodeId)?.typ)}» löschen, samt seinen Verbindungen`,
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    const after: VisGraph = {
      ...graph,
      nodes: graph.nodes.filter((n) => n.id !== node.id),
      edges: graph.edges.filter((e) => e.from !== node.id && e.to !== node.id),
    };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const collapseNode = registerCommand({
  id: 'vis.nodeKollabieren',
  title: 'Node ein-/ausklappen',
  description:
    'Klappt einen Node im Render-Graphen ein (nur Kopf + Ports sichtbar, kein Körper) oder wieder aus.',
  params: z.object({ graphId: z.string(), nodeId: z.string(), collapsed: z.boolean() }),
  summarize: (p, doc) => `Knoten «${knotenWort(knotenIn(vorherGraph(doc, p.graphId), p.nodeId)?.typ)}» ${p.collapsed ? 'einklappen' : 'ausklappen'}`,
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    const after: VisGraph = {
      ...graph,
      nodes: graph.nodes.map((n) => (n.id === node.id ? { ...n, collapsed: p.collapsed } : n)),
    };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const removeGraph = registerCommand({
  id: 'vis.graphLoeschen',
  title: 'Render-Graph löschen',
  description: 'Löscht einen ganzen Render-Graphen (undo-fähig).',
  params: z.object({ graphId: z.string() }),
  summarize: (p, doc) => {
    const g = vorherGraph(doc, p.graphId);
    return g ? `Render-Graph «${g.name}» löschen` : 'Render-Graph löschen';
  },
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    return [{ id: graph.id, before: graph, after: null }];
  },
});

/**
 * v0.8.4 PC2 (`docs/V084-SPEZ.md` E6/C-18) — echter Kernel-Command für
 * «Rendern». Der Command stellt NUR den AUFTRAG (welcher Node, welche
 * Kamera-Wahl, welche Stimmung, welcher Backbone, welche Auflösung) als
 * SettingsPatch — genau wie `design.schnittSetzen`/`publish.bueroSetzen`
 * läuft das über Yjs/Undo/`.kosmo`-Export wie jede andere Mutation. Die
 * tatsächliche AUSFÜHRUNG (Bridge-Fetch, Job-Status, Bild) ist bewusst NICHT
 * hier: sie ist Laufzeit (`apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`
 * `sendeGraphRenderAuftrag()`, Status/Bild in `vis-runtime.ts` `laeufe`,
 * «Laufzeit ≠ Modell») — ein Kernel-Command darf keinen Netzwerk-Seiteneffekt
 * auslösen. `VisWorkspace.tsx` beobachtet dieses Feld (Executor) und stösst
 * `sendeGraphRenderAuftrag()` an, sobald ein frischer Auftrag erscheint.
 *
 * Weil dieser Command jetzt in der Registry steht, wird er über
 * `commandTools()` (`@kosmo/ai`) automatisch ein Kosmo-Werkzeug — Kosmo kann
 * Rendern vorschlagen/ausführen, genau wie jeden anderen Command.
 *
 * `kameraWahl` spiegelt `kosmo-contracts` `RenderScene.cameras`s
 * Literal-Modi `'auto'|'saved'` (neben dem expliziten Array, das der
 * Auto-Kamera-Node liefert) — `'saved'` bittet die HomeStation um ihre
 * eigenen gemerkten Kamera-Standpunkte, unabhängig vom App-seitigen
 * `GespeicherteAnsicht`-Konzept (Bild-Snapshots, kein Kamera-Zustand).
 * `backbone` spiegelt denselben Enum-Wortlaut wie `RenderScene.vis.backbone`.
 * Der Satz «kein Duplikat-Risiko» stand hier bis zum 19.08.2026 — und er war
 * falsch: die beiden Aufzaehlungen sind in genau diesem Punkt auseinander
 * gelaufen, bis der HomeStation-Befund 12 es sichtbar machte (`z-image-turbo`
 * fehlte in beiden, `'qwen'` war Vorgabe und konnte die Konditionierung
 * nicht). Additiv zu sein schuetzt vor Bruch, nicht vor Drift. DREI Orte
 * fuehren dieselbe Liste von Hand — hier, `model/doc.ts` (`VisRenderWunsch`)
 * und `contracts/render-scene.ts`. Sie werden jetzt gegeneinander gehalten:
 * `test/backbone-eine-liste.test.ts`.
 *
 * KEIN `Date.now()`/`Math.random()` in dieser Funktion (Determinismus/
 * Doppellauf-Test): der Auftrag trägt bewusst keinen Zeitstempel, s.
 * `VisRenderWunsch`-Kommentar in `model/doc.ts`.
 */
export const renderAuftrag = registerCommand({
  id: 'vis.render',
  title: 'Rendern',
  description:
    `Stellt einen Render-AUFTRAG für einen Render-Node: kameraWahl (auto = wie verbunden/Bridge-Default, saved = die von der HomeStation gemerkten Kamera-Standpunkte), optional Stimmungs-Preset (${STIMMUNGEN_SATZ}), KI-Backbone und Zielauflösung. Der Auftrag selbst ist Teil des Docs (undo-fähig) — die eigentliche Ausführung (Bridge-Job, Bild, Status) startet dieser Command NICHT selbst, das übernimmt die App-Laufzeit, sobald sie den Auftrag sieht.`,
  params: z.object({
    graphId: z.string(),
    nodeId: z.string().describe('Render-Node im Graphen (Typ «render»)'),
    kameraWahl: z.enum(['auto', 'saved']).default('auto'),
    // Bauplan «Neue Knoten» K (Entscheid 110 B): die acht Stimmungen, wie `VIS_STIMMUNG_IDS`.
    stimmungPreset: z.enum(VIS_STIMMUNG_IDS).optional(),
    backbone: z.enum(['z-image-turbo', 'qwen', 'flux2-klein', 'flux-krea', 'sdxl', 'qwen-image-2.1']).optional(),
    // Nr. 85/84 (Vertrag 20.10.2026, Auflage 2): zwei flache Skalare, kein Tupel.
    grundlage: z.string().optional(),
    seed: z.number().int().min(0).max(2147483647).optional(),
    // Entscheid 104 (Blatt 29): Guete des KI-Schritts, ohne Beschreibung (Werkzeug-Budget; die
    // Luft-Probe misst +19 Token an der vollen Liste, die schlimmste Auswahl bleibt gleich).
    guete: z.enum(['vorschau', 'voll']).optional(),
    aufloesung: z
      .tuple([z.number().int().positive(), z.number().int().positive()])
      .optional()
      .describe('[Breite, Höhe] in Pixeln'),
  }),
  summarize: (p, doc) => {
    vorherGraph(doc, p.graphId);
    return renderZeile(p);
  },
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    if (node.typ !== 'render') {
      throw new CommandError(`Node «${p.nodeId}» ist kein Render-Node (Typ «${node.typ}»)`);
    }
    // Nr. 85 Paket 2: eine Kennung, die keine Grundlage sein kann, wird hier abgewiesen statt erst
    // am Heim-PC — dieselbe Form wie im Vertrag (`RenderScene.vis.grundlage`).
    if (p.grundlage !== undefined && !/^gl-[0-9a-f]{16}$/.test(p.grundlage)) {
      throw new CommandError(`«${p.grundlage}» ist keine Grundlage — erwartet «gl-» und 16 Zeichen 0–9/a–f`);
    }
    const wunsch: VisRenderWunsch = {
      graphId: p.graphId,
      nodeId: p.nodeId,
      kameraWahl: p.kameraWahl,
      ...(p.stimmungPreset !== undefined ? { stimmungPreset: p.stimmungPreset } : {}),
      ...(p.backbone !== undefined ? { backbone: p.backbone } : {}),
      ...(p.aufloesung !== undefined ? { aufloesung: p.aufloesung } : {}),
      ...(p.grundlage !== undefined ? { grundlage: p.grundlage } : {}),
      ...(p.seed !== undefined ? { seed: p.seed } : {}),
      ...(p.guete !== undefined ? { guete: p.guete } : {}),
    };
    return [
      {
        settings: true as const,
        // Schmales Patch (nur `visRenderAuftrag`), Muster `design.schnittSetzen`:
        // `??  null` macht «vorher» explizit statt den Schlüssel wegzulassen —
        // ein Objekt-Spread löscht auf Undo sonst keine fehlenden Keys.
        before: { visRenderAuftrag: doc.settings.visRenderAuftrag ?? null },
        after: { visRenderAuftrag: wunsch },
      },
    ];
  },
});

/*
 * «Varianten mit einem Klick» (Owner-Entscheide 92/92a/92b der Visbox; L24 Bildweg Varianten,
 * E246) — ein Befehl `vis.varianten`, damit Kosmo und Claude den Bildweg von Demoauftrag 01
 * ohne eigenes Skript gehen koennen: bestellen und (mit `stand: true`) lesen. Rechnung in
 * `derive/varianten.ts`.
 *
 * Das Bestellen stellt — wie `vis.render` — nur den AUFTRAG ins Dokument: es setzt die
 * Achsen am Knoten und zaehlt `bestellNr` hoch. Senden ist Laufzeit (`modules/vis/varianten.ts`
 * der App): sie sieht den Befehl im Journal und schickt je Stimmung und Entwurf einen Auftrag an
 * die HomeStation. Kein Netz im Kern, kein Zeitstempel (Doppellauf-Probe). Freigegeben wird
 * NICHT hier: die Freigabe ist der Handgriff des Architekten («Alle freigeben» am Knoten).
 */

function findeVariantenKnoten(doc: KosmoDoc, graphId: string | undefined, nodeId: string | undefined): { graph: VisGraph; node: VisNode } {
  if (graphId !== undefined) requireGraph(doc, graphId);
  const treffer = findeVariantenKnotenIn(doc, graphId, nodeId);
  if (!treffer) {
    throw new CommandError(
      nodeId !== undefined
        ? `Node «${nodeId}» existiert nicht${graphId !== undefined ? ' im Graphen' : ''}`
        : 'Kein Varianten-Knoten — erst einen Knoten «varianten» hinter den Render-Knoten setzen (vis_nodeSetzen, vis_verbinden: Render.bild → Varianten.render).',
    );
  }
  if (treffer.node.typ !== VARIANTEN_TYP) {
    throw new CommandError(`Node «${treffer.node.id}» ist kein Varianten-Knoten (Typ «${treffer.node.typ}»)`);
  }
  return treffer;
}

interface VariantenAufloesung {
  graph: VisGraph;
  node: VisNode;
  achsen: VariantenAchsen;
  /** Der Kern kennt keine Standpunkte (Visbox): die Gegenseite rechnet ihre eigenen. */
  standpunkteDerGegenseite: boolean;
}

function loeseVariantenAuf(
  doc: KosmoDoc,
  p: { graphId?: string | undefined; nodeId?: string | undefined; standpunkte?: string[] | undefined; stimmungen?: string[] | undefined; entwuerfe?: string[] | undefined },
): VariantenAufloesung {
  const { graph, node } = findeVariantenKnoten(doc, p.graphId, p.nodeId);
  const render = variantenRenderKnoten(graph, node.id);
  if (!render) {
    throw new CommandError(
      'Der Varianten-Knoten hängt an keinem Render-Knoten — verbinde Render «Bild» mit Varianten «Render».',
    );
  }
  const standpunkte = verfuegbareStandpunkte(doc, graph, render.id).map((s) => s.name);
  const stimmungen = Object.keys(VIS_STIMMUNGEN);
  const entwuerfe = verfuegbareEntwuerfe(doc).map((e) => e.id);
  const unbekannt = (wahl: string[] | undefined, da: readonly string[], was: string) => {
    const fehlt = (wahl ?? []).filter((x) => !da.includes(x));
    if (fehlt.length > 0) {
      throw new CommandError(
        `${was} unbekannt: ${fehlt.map((x) => `«${x}»`).join(', ')} — verfügbar: ${da.length > 0 ? da.map((x) => `«${x}»`).join(', ') : 'keine'}`,
      );
    }
  };
  if (standpunkte.length > 0) unbekannt(p.standpunkte, standpunkte, 'Standpunkt');
  unbekannt(p.stimmungen, stimmungen, 'Stimmung');
  unbekannt(p.entwuerfe, entwuerfe, 'Entwurf');
  const params = {
    ...(node.params ?? {}),
    ...(p.standpunkte !== undefined && standpunkte.length > 0 ? { standpunkte: schreibeListe(p.standpunkte) } : {}),
    ...(p.stimmungen !== undefined ? { stimmungen: schreibeListe(p.stimmungen) } : {}),
    ...(p.entwuerfe !== undefined ? { entwuerfe: schreibeListe(p.entwuerfe) } : {}),
  };
  return {
    graph,
    node,
    achsen: gewaehlteAchsen(params, standpunkte, stimmungen, entwuerfe),
    standpunkteDerGegenseite: standpunkte.length === 0,
  };
}

function bestellSatz(a: VariantenAufloesung): string {
  const { standpunkte, stimmungen, entwuerfe } = a.achsen;
  const auftraege = stimmungen.length * entwuerfe.length;
  const auftragWort = `${auftraege} ${auftraege === 1 ? 'Auftrag' : 'Aufträge'}`;
  if (a.standpunkteDerGegenseite) {
    return (
      `Varianten bestellt: ${auftragWort} (${stimmungen.length} × ${entwuerfe.length}), Standpunkte rechnet die ` +
      `HomeStation selbst — jeder wartet auf Freigabe am Knoten «Varianten» (${a.node.id}).`
    );
  }
  const n = variantenAnzahl(standpunkte.length, stimmungen.length, entwuerfe.length);
  return (
    `Varianten bestellt: ${variantenZaehlerSatz(standpunkte.length, stimmungen.length, entwuerfe.length)} — ` +
    `${variantenAchsenSatz(standpunkte.length, stimmungen.length, entwuerfe.length)}, ${auftragWort}` +
    `${variantenWarnt(n) ? ', viele Bilder: das dauert' : ''}; jeder wartet auf Freigabe am Knoten «Varianten» (${a.node.id}).`
  );
}

/**
 * EIN Befehl fuer Bestellen und Lesen (Integrator 15.10.2026: Sperre fuer neue Befehle und
 * laengere Beschreibungen, bis Buendel C eingespielt ist — in der vollen Werkzeugliste waren nur
 * noch 90 Token frei). Darum knapp: ohne `stand` bestellt er (Achsen am Knoten setzen,
 * `bestellNr` hochzaehlen, ein Rueckgaengig-Schritt, Karte wie `vis.render`); mit `stand: true`
 * aendert er nichts und gibt je Zelle Stand, Auftrag, Bild und Urteil zurueck — ohne Patch ist
 * das fuer Kosmo und Claude ein Lauf ohne Karte («ohne Änderung», `istLesenderLauf`).
 */
export const varianten = registerCommand({
  id: 'vis.varianten',
  title: 'Varianten',
  description:
    'Bestellt am Varianten-Knoten alle Kombinationen der Achsen; stand:true liest nur den Stand.',
  params: z.object({
    nodeId: z.string().optional(),
    standpunkte: z.array(z.string()).optional(),
    stimmungen: z.array(z.string()).optional(),
    entwuerfe: z.array(z.string()).optional(),
    stand: z.boolean().optional(),
  }),
  summarize: (p, doc) => {
    if (!doc) return 'Varianten';
    try {
      if (p.stand) {
        const { graph, node } = findeVariantenKnoten(doc, undefined, p.nodeId);
        return (
          variantenStandLesen(graph.id, node.id) ??
          `Varianten-Knoten «${node.id}»: der Stand der Bilder lebt in der laufenden App (KosmoVis), hier ist keine angemeldet.`
        );
      }
      return bestellSatz(loeseVariantenAuf(doc, p));
    } catch (err) {
      return `Varianten: ${err instanceof CommandError ? err.message : 'nicht auswertbar'}`;
    }
  },
  run: (doc, p) => {
    if (p.stand) {
      findeVariantenKnoten(doc, undefined, p.nodeId);
      return [];
    }
    const a = loeseVariantenAuf(doc, p);
    const { standpunkte, stimmungen, entwuerfe } = a.achsen;
    if (stimmungen.length === 0 || entwuerfe.length === 0 || (!a.standpunkteDerGegenseite && standpunkte.length === 0)) {
      throw new CommandError('Nichts zu bestellen — mindestens ein Standpunkt, eine Stimmung und ein Entwurf.');
    }
    const alt = a.node.params ?? {};
    const bestellNr = (typeof alt['bestellNr'] === 'number' ? alt['bestellNr'] : 0) + 1;
    const params = {
      ...alt,
      ...(a.standpunkteDerGegenseite ? {} : { standpunkte: schreibeListe(standpunkte) }),
      stimmungen: schreibeListe(stimmungen),
      entwuerfe: schreibeListe(entwuerfe),
      bestellNr,
    };
    const after: VisGraph = {
      ...a.graph,
      nodes: a.graph.nodes.map((n) => (n.id === a.node.id ? { ...n, params } : n)),
    };
    return [{ id: a.graph.id, before: a.graph, after }];
  },
});
