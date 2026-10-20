import { describe, expect, it } from 'vitest';
import { CommandError, History, KosmoDoc, execute, type VisGraph } from '../src';

/**
 * Nr. 85 Paket 2 (Entscheide 98/98a, 20.10.2026): `vis.render` traegt Grundlage und Startwert
 * in den Render-Wunsch (`doc.settings.visRenderAuftrag`), damit ein Auftrag ueber Kosmo
 * dieselbe Variante bestellen kann wie der Knopf «Variante erzeugen». Der Befehl bleibt
 * deterministisch und rechnet nichts aus — er legt nur ab.
 */

const GL = 'gl-74896f0a1b2c3d4e';

function graphMitRender(doc: KosmoDoc): { graphId: string; nodeId: string } {
  const g = execute(doc, 'vis.graphErstellen', { name: 'Testgraph' });
  const graphId = (g.patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  const nodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  return { graphId, nodeId };
}

describe('kv-grundlage — vis.render traegt Grundlage und Startwert', () => {
  it('grundlage und seed landen unveraendert im Wunsch', () => {
    const doc = new KosmoDoc();
    const { graphId, nodeId } = graphMitRender(doc);
    execute(doc, 'vis.render', { graphId, nodeId, grundlage: GL, seed: 123456 });
    expect(doc.settings.visRenderAuftrag).toMatchObject({ graphId, nodeId, grundlage: GL, seed: 123456 });
  });

  it('ohne die beiden Felder bleibt der Wunsch wie bisher (kein Schluessel)', () => {
    const doc = new KosmoDoc();
    const { graphId, nodeId } = graphMitRender(doc);
    execute(doc, 'vis.render', { graphId, nodeId });
    const w = doc.settings.visRenderAuftrag!;
    expect('grundlage' in w).toBe(false);
    expect('seed' in w).toBe(false);
  });

  it('eine Kennung, die keine Grundlage sein kann, wird abgewiesen', () => {
    const doc = new KosmoDoc();
    const { graphId, nodeId } = graphMitRender(doc);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId, grundlage: 'gl-zu-kurz' })).toThrow(CommandError);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId, grundlage: 'GL-74896F0A1B2C3D4E' })).toThrow(CommandError);
  });

  it('der Startwert liegt im Vertragsbereich 0..2147483647, ganzzahlig', () => {
    const doc = new KosmoDoc();
    const { graphId, nodeId } = graphMitRender(doc);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId, seed: -1 })).toThrow(CommandError);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId, seed: 2147483648 })).toThrow(CommandError);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId, seed: 1.5 })).toThrow(CommandError);
    execute(doc, 'vis.render', { graphId, nodeId, seed: 0 });
    expect(doc.settings.visRenderAuftrag?.seed).toBe(0);
  });

  it('Doppellauf: derselbe Aufruf ergibt dieselbe Nutzlast, und Undo raeumt sie weg', () => {
    const a = new KosmoDoc();
    const b = new KosmoDoc();
    const ga = graphMitRender(a);
    const gb = graphMitRender(b);
    const pa = execute(a, 'vis.render', { graphId: ga.graphId, nodeId: ga.nodeId, grundlage: GL, seed: 7 });
    const pb = execute(b, 'vis.render', { graphId: gb.graphId, nodeId: gb.nodeId, grundlage: GL, seed: 7 });
    const ohneIds = (w: unknown) => ({ ...(w as Record<string, unknown>), graphId: '', nodeId: '' });
    expect(ohneIds(a.settings.visRenderAuftrag)).toEqual(ohneIds(b.settings.visRenderAuftrag));
    expect(pa.patches).toHaveLength(1);
    expect(pb.patches).toHaveLength(1);

    const doc = new KosmoDoc();
    const h = new History();
    const { graphId, nodeId } = graphMitRender(doc);
    h.record(execute(doc, 'vis.render', { graphId, nodeId, grundlage: GL, seed: 7 }).patches);
    expect(doc.settings.visRenderAuftrag?.grundlage).toBe(GL);
    h.undo(doc);
    expect(doc.settings.visRenderAuftrag ?? null).toBeNull();
  });
});

describe('Entscheid 104 — vis.render traegt die Guete', () => {
  it('guete landet unveraendert im Wunsch; ohne Feld kein Schluessel', () => {
    const doc = new KosmoDoc();
    const { graphId, nodeId } = graphMitRender(doc);
    execute(doc, 'vis.render', { graphId, nodeId, grundlage: GL, seed: 1, guete: 'vorschau' });
    expect(doc.settings.visRenderAuftrag).toMatchObject({ grundlage: GL, seed: 1, guete: 'vorschau' });
    execute(doc, 'vis.render', { graphId, nodeId });
    expect('guete' in doc.settings.visRenderAuftrag!).toBe(false);
  });

  it('eine unbekannte Guete wird abgewiesen', () => {
    const doc = new KosmoDoc();
    const { graphId, nodeId } = graphMitRender(doc);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId, guete: 'schnell' })).toThrow(CommandError);
  });
});
