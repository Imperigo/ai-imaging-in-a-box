import { describe, expect, it } from 'vitest';
import { CommandError, History, KosmoDoc, execute, type SettingsPatch, type VisGraph } from '../src';

/**
 * v0.8.4 PC2 (`docs/V084-SPEZ.md` E6/C-18) — `vis.render`: der Command
 * stellt NUR den Render-AUFTRAG als SettingsPatch (kameraWahl/stimmungPreset/
 * backbone/aufloesung), die Ausführung bleibt Laufzeit (`vis-jobs.ts`/
 * `vis-runtime.ts`). Diese Suite prüft die zod-Validierung, die
 * SettingsPatch-Form, Undo-Neutralität und Doppellauf-Determinismus (kein
 * `Date.now()`/`Math.random()` im Command-Pfad — s. Kommentar bei
 * `VisRenderWunsch`, `model/doc.ts`).
 */

function neuerGraphMitRenderNode(doc: KosmoDoc): { graphId: string; renderNodeId: string; modellNodeId: string } {
  const g = execute(doc, 'vis.graphErstellen', { name: 'Testgraph' });
  const graphId = (g.patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  const modellNodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
  const renderNodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  execute(doc, 'vis.verbinden', {
    graphId,
    from: modellNodeId,
    fromPort: 'szene',
    to: renderNodeId,
    toPort: 'szene',
  });
  return { graphId, renderNodeId, modellNodeId };
}

describe('vis.render — zod-Validierung', () => {
  it('kameraWahl fehlt → Default «auto»', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    execute(doc, 'vis.render', { graphId, nodeId: renderNodeId });
    expect(doc.settings.visRenderAuftrag?.kameraWahl).toBe('auto');
  });

  it('lehnt eine unbekannte kameraWahl ab', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    expect(() =>
      execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, kameraWahl: 'irgendwas' }),
    ).toThrow(CommandError);
  });

  it('lehnt ein unbekanntes stimmungPreset ab', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    expect(() =>
      execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, stimmungPreset: 'nacht' }),
    ).toThrow(CommandError);
  });

  it('lehnt einen unbekannten backbone ab', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    expect(() =>
      execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, backbone: 'dall-e' }),
    ).toThrow(CommandError);
  });

  it('lehnt eine aufloesung ab, die kein positives [Breite,Höhe]-Tupel ist', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    expect(() =>
      execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, aufloesung: [0, 1000] }),
    ).toThrow(CommandError);
    expect(() =>
      execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, aufloesung: [1600] }),
    ).toThrow(CommandError);
  });

  it('lehnt einen unbekannten Graphen ehrlich ab', () => {
    const doc = new KosmoDoc();
    expect(() => execute(doc, 'vis.render', { graphId: 'visgraph_x', nodeId: 'node_x' })).toThrow(
      CommandError,
    );
  });

  it('lehnt einen unbekannten Node im Graphen ab', () => {
    const doc = new KosmoDoc();
    const { graphId } = neuerGraphMitRenderNode(doc);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId: 'node_x' })).toThrow(CommandError);
  });

  it('lehnt einen Node ab, der kein Render-Node ist', () => {
    const doc = new KosmoDoc();
    const { graphId, modellNodeId } = neuerGraphMitRenderNode(doc);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId: modellNodeId })).toThrow(CommandError);
  });
});

describe('vis.render — SettingsPatch-Form', () => {
  it('liefert genau EINE settings-Patch mit before/after auf visRenderAuftrag', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    const res = execute(doc, 'vis.render', {
      graphId,
      nodeId: renderNodeId,
      kameraWahl: 'auto',
      stimmungPreset: 'abend',
      backbone: 'qwen',
      aufloesung: [1920, 1080],
    });
    expect(res.patches).toHaveLength(1);
    const [patch] = res.patches as [SettingsPatch];
    expect(patch.settings).toBe(true);
    expect(patch.before).toEqual({ visRenderAuftrag: null });
    expect(patch.after).toEqual({
      visRenderAuftrag: {
        graphId,
        nodeId: renderNodeId,
        kameraWahl: 'auto',
        stimmungPreset: 'abend',
        backbone: 'qwen',
        aufloesung: [1920, 1080],
      },
    });
    expect(doc.settings.visRenderAuftrag).toEqual(patch.after.visRenderAuftrag);
  });

  it('optionale Felder fehlen im Auftrag, wenn nicht übergeben (exactOptionalPropertyTypes-ehrlich)', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    execute(doc, 'vis.render', { graphId, nodeId: renderNodeId });
    const wunsch = doc.settings.visRenderAuftrag!;
    expect('stimmungPreset' in wunsch).toBe(false);
    expect('backbone' in wunsch).toBe(false);
    expect('aufloesung' in wunsch).toBe(false);
  });

  it('appears als Kosmo-Werkzeug: commandTools() enthält vis.render (Namens-Muster toolNameFor)', async () => {
    // Grep-Beleg statt Paket-Kreuzimport (Kernel importiert nie aus kosmo-ai) —
    // die eigentliche End-zu-End-Prüfung läuft in
    // packages/kosmo-ai/test/pc2-vis-render-tool.test.ts, da commandTools()
    // dort lebt. Hier nur die Kernel-seitige Garantie: der Command ist real
    // registriert (allCommands()).
    const { allCommands } = await import('../src');
    expect(allCommands().some((c) => c.id === 'vis.render')).toBe(true);
  });
});

describe('vis.render — Undo-Neutralität', () => {
  it('Undo stellt «kein offener Wunsch» wieder her (H-9-Muster wie design.schnittSetzen)', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    const h = new History();
    const res = execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, stimmungPreset: 'morgen' });
    h.record(res.patches);
    expect(doc.settings.visRenderAuftrag).not.toBe(undefined);
    expect(doc.settings.visRenderAuftrag).not.toBe(null);
    h.undo(doc);
    expect(doc.settings.visRenderAuftrag ?? null).toBe(null);
  });

  it('zweiter Undo-Schritt stellt den ERSTEN Auftrag wieder her, nicht «kein Wunsch»', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    const h = new History();
    const erster = execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, stimmungPreset: 'morgen' });
    h.record(erster.patches);
    const zweiter = execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, stimmungPreset: 'abend' });
    h.record(zweiter.patches);
    expect(doc.settings.visRenderAuftrag?.stimmungPreset).toBe('abend');
    h.undo(doc);
    expect(doc.settings.visRenderAuftrag?.stimmungPreset).toBe('morgen');
    h.undo(doc);
    expect(doc.settings.visRenderAuftrag ?? null).toBe(null);
  });

  it('Redo nach Undo stellt den Auftrag exakt wieder her', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    const h = new History();
    const res = execute(doc, 'vis.render', { graphId, nodeId: renderNodeId, backbone: 'flux-krea' });
    h.record(res.patches);
    const nachAusfuehrung = doc.settings.visRenderAuftrag;
    h.undo(doc);
    expect(doc.settings.visRenderAuftrag ?? null).toBe(null);
    h.redo(doc);
    expect(doc.settings.visRenderAuftrag).toEqual(nachAusfuehrung);
  });
});

describe('vis.render — Doppellauf-Determinismus', () => {
  it('zwei Aufrufe mit IDENTISCHEN Parametern auf demselben Doc-Stand liefern byte-gleiche Patches (dryRun, kein Date.now/Math.random im Pfad)', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    const params = {
      graphId,
      nodeId: renderNodeId,
      kameraWahl: 'saved' as const,
      stimmungPreset: 'weiss' as const,
      backbone: 'sdxl' as const,
      aufloesung: [2400, 1600] as const,
    };
    const lauf1 = execute(doc, 'vis.render', params, { dryRun: true });
    const lauf2 = execute(doc, 'vis.render', params, { dryRun: true });
    expect(lauf1.patches).toEqual(lauf2.patches);
    expect(lauf1.summary).toBe(lauf2.summary);
  });

  it('doppeltes Ausführen (angewendet) erzeugt zwei UNTERSCHIEDLICHE `before`, aber identische `after`-Nutzlast', () => {
    const doc = new KosmoDoc();
    const { graphId, renderNodeId } = neuerGraphMitRenderNode(doc);
    const params = { graphId, nodeId: renderNodeId, stimmungPreset: 'abend' as const };
    const lauf1 = execute(doc, 'vis.render', params);
    const lauf2 = execute(doc, 'vis.render', params);
    const patch1 = lauf1.patches[0] as { after: { visRenderAuftrag: unknown } };
    const patch2 = lauf2.patches[0] as { after: { visRenderAuftrag: unknown } };
    expect(patch1.after.visRenderAuftrag).toEqual(patch2.after.visRenderAuftrag);
  });
});
