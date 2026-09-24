import { z } from 'zod';
import { newId } from '../model/ids';
import type { VisEdge, VisGraph, VisNode } from '../model/entities';
import type { KosmoDoc, VisRenderWunsch } from '../model/doc';
import { hatZyklus, visPort, VIS_NODE_KATALOG } from '../derive/visgraph';
import { CommandError, registerCommand } from './core';

/**
 * Vis-Commands (V1-Finish P2) — der Render-Graph läuft über denselben
 * Command-Weg wie jedes Bauteil: Undo, Yjs, Journal, und Kosmo kann
 * Render-Graphen SPRECHEN (jedes Schema wird automatisch LLM-Tool).
 */

const ParamWert = z.union([z.string(), z.number(), z.boolean()]);

function requireGraph(doc: KosmoDoc, id: string): VisGraph {
  const e = doc.get<VisGraph>(id);
  if (!e || e.kind !== 'visgraph') throw new CommandError(`Render-Graph «${id}» existiert nicht`);
  return e;
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
  summarize: (p) => `Render-Graph «${p.name}»`,
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
  summarize: (p) => `Node ${p.typ}`,
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
      params: { ...kat.defaults, ...(p.params ?? {}) },
    };
    const after: VisGraph = { ...graph, nodes: [...graph.nodes, node] };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const setNodeParams = registerCommand({
  id: 'vis.nodeParametrieren',
  title: 'Node parametrieren',
  description:
    'Setzt Parameter eines Nodes (mischt in die bestehenden), z.B. den Text eines Prompt-Nodes, das Preset einer Stimmung (morgen/abend/weiss) oder den Wert eines Zahl-Nodes.',
  params: z.object({
    graphId: z.string(),
    nodeId: z.string(),
    params: z.record(z.string(), ParamWert),
  }),
  summarize: (p) => `Node-Parameter (${Object.keys(p.params).join(', ')})`,
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    const after: VisGraph = {
      ...graph,
      // ?? {} statt n.params direkt: ein Node ohne params (Alt-Stand/Import)
      // darf hier nicht in einen halbkaputten Zustand gemischt werden.
      nodes: graph.nodes.map((n) => (n.id === node.id ? { ...n, params: { ...(n.params ?? {}), ...p.params } } : n)),
    };
    return [{ id: graph.id, before: graph, after }];
  },
});

export const moveNode = registerCommand({
  id: 'vis.nodeSchieben',
  title: 'Node schieben',
  description: 'Verschiebt einen Node auf dem Canvas (ein Schritt pro Drag, nie pro Mausbewegung).',
  params: z.object({ graphId: z.string(), nodeId: z.string(), x: z.number(), y: z.number() }),
  summarize: () => 'Node verschoben',
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
  summarize: (p) => `Verbinden ${p.fromPort} → ${p.toPort}`,
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
  summarize: () => 'Verbindung getrennt',
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
  summarize: () => 'Node gelöscht',
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
  summarize: (p) => (p.collapsed ? 'Node eingeklappt' : 'Node ausgeklappt'),
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
  summarize: () => 'Render-Graph gelöscht',
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
    'Stellt einen Render-AUFTRAG für einen Render-Node: kameraWahl (auto = wie verbunden/Bridge-Default, saved = die von der HomeStation gemerkten Kamera-Standpunkte), optional Stimmungs-Preset (morgen/abend/weiss), KI-Backbone und Zielauflösung. Der Auftrag selbst ist Teil des Docs (undo-fähig) — die eigentliche Ausführung (Bridge-Job, Bild, Status) startet dieser Command NICHT selbst, das übernimmt die App-Laufzeit, sobald sie den Auftrag sieht.',
  params: z.object({
    graphId: z.string(),
    nodeId: z.string().describe('Render-Node im Graphen (Typ «render»)'),
    kameraWahl: z.enum(['auto', 'saved']).default('auto'),
    stimmungPreset: z.enum(['morgen', 'abend', 'weiss']).optional(),
    backbone: z.enum(['z-image-turbo', 'qwen', 'flux2-klein', 'flux-krea', 'sdxl']).optional(),
    aufloesung: z
      .tuple([z.number().int().positive(), z.number().int().positive()])
      .optional()
      .describe('[Breite, Höhe] in Pixeln'),
  }),
  summarize: (p) =>
    `Render-Auftrag (${p.kameraWahl}${p.stimmungPreset ? `, ${p.stimmungPreset}` : ''}${p.backbone ? `, ${p.backbone}` : ''})`,
  run: (doc, p) => {
    const graph = requireGraph(doc, p.graphId);
    const node = requireNode(graph, p.nodeId);
    if (node.typ !== 'render') {
      throw new CommandError(`Node «${p.nodeId}» ist kein Render-Node (Typ «${node.typ}»)`);
    }
    const wunsch: VisRenderWunsch = {
      graphId: p.graphId,
      nodeId: p.nodeId,
      kameraWahl: p.kameraWahl,
      ...(p.stimmungPreset !== undefined ? { stimmungPreset: p.stimmungPreset } : {}),
      ...(p.backbone !== undefined ? { backbone: p.backbone } : {}),
      ...(p.aufloesung !== undefined ? { aufloesung: p.aufloesung } : {}),
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
