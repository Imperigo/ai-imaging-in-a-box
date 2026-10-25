/**
 * Visbox-eigen — «Grundlage rendern» als Werkzeug für Claude und den Assistenten (Owner-Entscheid
 * 146, 24.10.2026, Befund (4) vom Mac: «Für "Grundlage rendern" gibt es kein Werkzeug»).
 *
 * Der Knopf «Grundlage rendern» am Render-Knoten bestellt nur Blender (Cycles) mit allen Ebenen; der
 * Heim-PC legt die Grundlage ab, auf der «Variante erzeugen» danach rechnet (Entscheid 98). Bis jetzt
 * ging das nur per Klick — Claude konnte eine Variante bestellen, aber nie die Grundlage dazu.
 *
 * WIE `vis.render`: Der Befehl `vis.grundlage` stellt nur einen AUFTRAG ins Dokument
 * (`settings.visGrundlageAuftrag`, ein frisches Objekt je Aufruf, rückgängig wie jeder Befehl).
 * Ausgeführt wird er hier (`haengeGrundlageAn`) auf demselben Weg wie der Knopf
 * (`sendeGraphRenderAuftrag` mit `stufe: 'grundlage'` und `wiederverwenden`). Er geht durch den
 * Werkzeugsatz wie jeder Vis-Befehl, eingeteilt als «rendern» (`VIS_BEFEHL_ART`): Karte im Modus
 * Karte und Coop, in «Voll» ohne Karte mit denselben Grenzen wie `vis_render` (`voll-render.ts`) —
 * und der Heim-PC startet die Grafikkarte nur ohne Klick, wenn die Mac-App es ansagt und die
 * Grenze je Stunde nicht erreicht ist.
 *
 * Der Befehl ist nur in Visbox angemeldet (KosmoOrbit hat den Knopf, braucht das Werkzeug nicht);
 * darum steht er hier und nicht im Kern. Ein zurückgeholter früherer Auftrag (Rückgängig) startet
 * nichts (`istFrischerAuftrag`).
 */
import { z } from 'zod';
import { CommandError, evaluiereGraph, getCommand, OHNE_FREIGABE_RENDER, rechnetOhneFreigabe, registerCommand, type KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { grundlageAmKnoten } from '../../kosmo-orbit/src/modules/vis/grundlage';
import { NICHT_NEU_GERECHNET } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { abbrechenJob, grundlageStandFuerKnoten, istFrischerAuftrag, sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { useProject } from '../../kosmo-orbit/src/state/project-store';

export const GRUNDLAGE_BEFEHL = 'vis.grundlage';
/** Das Feld im Dokument — Visbox-eigen, darum nicht in `DocSettings` des Kerns. */
export const GRUNDLAGE_FELD = 'visGrundlageAuftrag';

export interface GrundlageAuftrag {
  graphId: string;
  nodeId: string;
}

/**
 * Visbox-Mac-Test 0.3.67 (C): Liegt für den JETZIGEN Stand des Render-Knotens schon eine Grundlage
 * vor, rechnet «Grundlage rendern» nichts (`sendeGraphRenderAuftrag` mit `wiederverwenden`, Befund B1
 * aus 306) — dieselbe Regel: der Stand wie beim Senden (`grundlageStandFuerKnoten`), die Grundlage am
 * Knoten oder gemerkt für diesen Stand (`grundlageAmKnoten`). `null`: keine, es wird gerechnet.
 */
export function vorhandeneGrundlage(doc: KosmoDoc, graphId: string, nodeId: string): string | null {
  const graph = doc.get<VisGraph>(graphId);
  if (!graph || graph.kind !== 'visgraph') return null;
  const node = graph.nodes.find((n) => n.id === nodeId);
  const roh = evaluiereGraph(doc, graph).renderAuftraege.get(nodeId);
  if (!node || node.typ !== 'render' || !roh) return null;
  const stand = grundlageStandFuerKnoten(doc, roh, node.params ?? {});
  const da = grundlageAmKnoten(node.params, stand);
  return da && da.stand === stand ? da.id : null;
}

/** Die Antwort, wenn nichts gerechnet wird — mit der vollen Kennung, damit Claude sie weiterreichen kann. */
export function grundlageVorhandenZeile(id: string): string {
  return `${NICHT_NEU_GERECHNET}: ${id} — «Variante erzeugen» (vis_render mit grundlage, oder vis_varianten) rechnet auf ihr.`;
}

export function grundlageZeile(): string {
  return `Grundlage rendern am Render-Knoten — nur Blender, alle Ebenen (${rechnetOhneFreigabe() ? OHNE_FREIGABE_RENDER : 'Freigabe durch den Architekten'})`;
}

/** Der Auftrag im Dokument, `null`: keiner. */
export function grundlageAuftragIn(doc: KosmoDoc): GrundlageAuftrag | null {
  const a = (doc.settings as unknown as Record<string, unknown>)[GRUNDLAGE_FELD];
  return a && typeof a === 'object' ? (a as GrundlageAuftrag) : null;
}

/** Meldet `vis.grundlage` an — einmal; ein zweiter Aufruf ändert nichts. */
export function meldeGrundlageBefehlAn(): void {
  if (getCommand(GRUNDLAGE_BEFEHL)) return;
  registerCommand({
    id: GRUNDLAGE_BEFEHL,
    title: 'Grundlage rendern',
    description:
      'Stellt den Auftrag «Grundlage rendern» für einen Render-Knoten: nur Blender (Cycles) mit allen Ebenen, ohne KI — auf dieser Grundlage rechnet danach «Variante erzeugen» (vis_render mit grundlage, oder vis_varianten). Liegt für denselben Stand schon eine Grundlage vor, wird sie genannt statt neu gerechnet.',
    params: z.object({
      graphId: z.string(),
      nodeId: z.string().describe('Render-Node im Graphen (Typ «render»)'),
    }),
    summarize: (p, doc) => {
      const da = vorhandeneGrundlage(doc, p.graphId, p.nodeId);
      return da ? grundlageVorhandenZeile(da) : grundlageZeile();
    },
    run: (doc, p) => {
      const graph = doc.get<VisGraph>(p.graphId);
      if (!graph || graph.kind !== 'visgraph') throw new CommandError(`Render-Graph «${p.graphId}» existiert nicht`);
      const node = graph.nodes.find((n) => n.id === p.nodeId);
      if (!node) throw new CommandError(`Node «${p.nodeId}» existiert nicht im Graphen`);
      if (node.typ !== 'render') throw new CommandError(`Node «${p.nodeId}» ist kein Render-Node (Typ «${node.typ}»)`);
      const auftrag: GrundlageAuftrag = { graphId: p.graphId, nodeId: p.nodeId };
      const vorher = grundlageAuftragIn(doc);
      return [{ settings: true as const, before: { [GRUNDLAGE_FELD]: vorher } as never, after: { [GRUNDLAGE_FELD]: auftrag } as never }];
    },
  });
}

/**
 * Derselbe Weg wie der Knopf «Grundlage rendern» (`NodeCanvas.grundlageRendern`): bestellen, und ein
 * Auftrag, der am Knoten noch auf Freigabe wartete, wird abgebrochen, wenn wirklich neu bestellt wurde.
 */
export function grundlageRendernWieDerKnopf(a: GrundlageAuftrag): void {
  const vorher = useVisRuntime.getState().laeufe[a.nodeId];
  const preset = useVisRuntime.getState().renderStimmungPreset;
  sendeGraphRenderAuftrag(a.graphId, a.nodeId, preset ? { preset } : undefined, { stufe: 'grundlage', wiederverwenden: true });
  const nachher = useVisRuntime.getState().laeufe[a.nodeId];
  if (vorher?.status === 'wartetFreigabe' && vorher.jobId && nachher !== vorher) {
    void abbrechenJob(vorher.jobId).catch(() => undefined);
  }
}

/**
 * Der Ausführer: sieht einen FRISCHEN Auftrag im Dokument und bestellt. Ein Auftrag, der beim
 * Anhängen schon dasteht (geladenes Dokument), und ein per Rückgängig zurückgeholter starten nichts.
 * Liefert das Abhängen.
 */
export function haengeGrundlageAn(bestelle: (a: GrundlageAuftrag) => void = grundlageRendernWieDerKnopf): () => void {
  meldeGrundlageBefehlAn();
  const gesehen = new WeakSet<object>();
  const merke = (doc: KosmoDoc) => {
    const a = grundlageAuftragIn(doc);
    if (a) gesehen.add(a);
  };
  let doc = useProject.getState().doc;
  merke(doc);
  return useProject.subscribe((s) => {
    if (s.doc !== doc) {
      doc = s.doc;
      merke(doc);
      return;
    }
    const a = grundlageAuftragIn(s.doc);
    if (!a || !istFrischerAuftrag(gesehen, a)) return;
    bestelle(a);
  });
}
