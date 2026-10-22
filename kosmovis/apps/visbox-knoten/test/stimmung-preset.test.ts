// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { beforeEach, describe, expect, it } from 'vitest';
import { evaluiereGraph, execute, History, KosmoDoc, STIMMUNG_PARAM_SATZ, stimmungAusParams, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { anwenden, behandle, leereKiZustand } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';

/**
 * VISBOX-EIGEN (Mac-Befund 0.3.33, 22.10.2026): Claude schlug am Stimmung-Knoten `{preset: "morgen"}`
 * vor, der Owner wendete die Karte an — im Graphen stand danach `preset="morgen"`, aber
 * `presets=["abend"]`; Knoten und Prompt blieben bei Abend. Die Regel steht in der Kopie
 * (`stimmungAufruf`, wörtlich aus KosmoVis); diese Probe hält sie in Visbox fest und prüft, dass
 * die Werkzeugliste im Bau (`dist/ki-werkzeugliste.json`, die die Mac-App Claude nennt) den Satz
 * zur Stimmung trägt.
 */
let graphId = '';
let stimmungId = '';
let renderId = '';

beforeEach(() => {
  leereKiZustand();
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  const setze = (typ: string, params?: Record<string, string>) => {
    execute(doc, 'vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
    const g = doc.get<VisGraph>(graphId)!;
    return g.nodes[g.nodes.length - 1]!.id;
  };
  const modell = setze('modell');
  stimmungId = setze('stimmung', { presets: '["abend"]', preset: 'abend' });
  renderId = setze('render');
  execute(doc, 'vis.verbinden', { graphId, from: stimmungId, fromPort: 'prompt', to: renderId, toPort: 'prompt' });
  execute(doc, 'vis.verbinden', { graphId, from: modell, fromPort: 'szene', to: renderId, toPort: 'szene' });
  useProject.setState({ doc, history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
});

describe('Stimmung per Karte (Befund 0.3.33)', () => {
  it('Karte {preset: "morgen"} anwenden: Liste, Prompt und Bestellung folgen', () => {
    behandle({ kennung: 'S-1', werkzeug: 'vis_nodeParametrieren', argumente: { graphId, nodeId: stimmungId, params: { preset: 'morgen' } } }, 'karte');
    expect(anwenden('S-1')!.ok).toBe(true);
    const doc = useProject.getState().doc;
    const g = doc.get<VisGraph>(graphId)!;
    const st = g.nodes.find((n) => n.id === stimmungId)!;
    expect(st.params).toMatchObject({ preset: 'morgen', presets: '["morgen"]' });
    expect(stimmungAusParams(st.params).presets).toEqual(['morgen']);
    const a = evaluiereGraph(doc, g);
    expect(String(a.werte.get(stimmungId)?.['prompt'])).toContain('Morgenlicht');
    expect(a.renderAuftraege.get(renderId)?.umgebung?.preset).toBe('morgen');
  });

  it('ein alter, widersprüchlicher Stand liest «presets gewinnt»', () => {
    expect(stimmungAusParams({ preset: 'morgen', presets: '["abend"]' }).presets).toEqual(['abend']);
  });

  it('die Werkzeugliste im Bau trägt den Satz zur Stimmung', () => {
    const liste = JSON.parse(readFileSync(resolve(process.cwd(), 'dist/ki-werkzeugliste.json'), 'utf-8')) as {
      werkzeuge: { name: string; description: string }[];
    };
    const w = liste.werkzeuge.find((x) => x.name === 'vis_nodeParametrieren')!;
    expect(w.description).toContain(STIMMUNG_PARAM_SATZ);
  });
});
