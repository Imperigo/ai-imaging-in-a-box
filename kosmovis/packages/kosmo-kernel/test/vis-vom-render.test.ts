import { describe, expect, it } from 'vitest';
import * as kern from '../src';
import { CommandError, KosmoDoc, VARIANTEN_TYP, execute, type VisGraph } from '../src';

/**
 * A0061 (Owner-Entscheid «Immer vom Render», 31.10.2026): jedes KI-Bild startet vom Beauty-Render derselben Kamera.
 * Die Guete «Vorschau» (ohne das Grundbild als Bildeingang) und jedes Bildwerkzeug ohne belegten Beauty-Eingang
 * werden im Kern abgewiesen — an `vis.render`, `vis.varianten` und an der Wahl am Knoten (`vis.nodeParametrieren`,
 * `vis.nodeSetzen`). Das Dokument bleibt, wie es war.
 */
const k = kern as unknown as {
  VORSCHAU_ABSAGE: string;
  BILDWERKZEUG_BEAUTY_EINGANG: Record<string, { status: string; grund: string; beleg: string }>;
  bildwerkzeugAbsage: (bw: unknown) => string | null;
};

const GESPERRT = ['qwen', 'qwen-image-2.1', 'sdxl', 'flux2-klein', 'flux-krea'] as const;

function graphMitKnoten(doc: KosmoDoc): { graphId: string; renderId: string; variantenId: string } {
  const graphId = (execute(doc, 'vis.graphErstellen', { name: 'Vom Render' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  const modellId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
  const renderId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  execute(doc, 'vis.verbinden', { graphId, from: modellId, fromPort: 'szene', to: renderId, toPort: 'szene' });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: VARIANTEN_TYP, x: 400, y: 0 });
  const variantenId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  execute(doc, 'vis.verbinden', { graphId, from: renderId, fromPort: 'bild', to: variantenId, toPort: 'render' });
  return { graphId, renderId, variantenId };
}

function wirft(f: () => unknown): Error {
  try {
    f();
  } catch (e) {
    return e as Error;
  }
  throw new Error('kein Wurf');
}

describe('A0061 — Liste der Bildwerkzeuge mit Status und Beleg', () => {
  it('nur Z-Image Turbo ist belegt; Qwen-Image-Edit (nur Tiefe) und die ungemessenen sind gesperrt, je mit Beleg', () => {
    const liste = k.BILDWERKZEUG_BEAUTY_EINGANG;
    expect(liste).toBeDefined();
    expect(Object.keys(liste).sort()).toEqual(['flux-krea', 'flux2-klein', 'qwen', 'qwen-image-2.1', 'sdxl', 'z-image-turbo']);
    expect(liste['z-image-turbo']).toMatchObject({ status: 'belegt', beleg: expect.stringContaining('auf-20261021-298') });
    expect(liste['qwen']).toMatchObject({ status: 'gesperrt', beleg: expect.stringContaining('auf-20260818-09') });
    for (const bw of GESPERRT) {
      expect(liste[bw]!.status, bw).toBe('gesperrt');
      expect(liste[bw]!.beleg.length, bw).toBeGreaterThan(0);
    }
    expect(k.bildwerkzeugAbsage('z-image-turbo')).toBeNull();
    expect(k.bildwerkzeugAbsage('')).toBeNull();
    expect(k.bildwerkzeugAbsage(undefined)).toBeNull();
    expect(k.bildwerkzeugAbsage('unbekannt-9')).toContain('gesperrt');
  });
});

describe('A0061 (a) — Güte «Vorschau» im Kern', () => {
  it('vis.render guete:"vorschau" → CommandError mit dem Absage-Satz, kein Auftrag im Dokument (auch dryRun)', () => {
    const doc = new KosmoDoc();
    const { graphId, renderId } = graphMitKnoten(doc);
    const vorher = JSON.stringify(doc.toJSON());
    for (const dryRun of [true, false]) {
      const e = wirft(() => execute(doc, 'vis.render', { graphId, nodeId: renderId, guete: 'vorschau' }, { dryRun }));
      expect(e).toBeInstanceOf(CommandError);
      expect(e.message).toContain(k.VORSCHAU_ABSAGE);
    }
    expect(doc.settings.visRenderAuftrag).toBeUndefined();
    expect(JSON.stringify(doc.toJSON())).toBe(vorher);
  });

  it('die Wahl «Vorschau» am Render- und am Varianten-Knoten (nodeParametrieren, nodeSetzen) wird abgewiesen', () => {
    const doc = new KosmoDoc();
    const { graphId, renderId, variantenId } = graphMitKnoten(doc);
    const vorher = JSON.stringify(doc.toJSON());
    for (const nodeId of [renderId, variantenId]) {
      expect(() => execute(doc, 'vis.nodeParametrieren', { graphId, nodeId, params: { guete: 'vorschau' } })).toThrow(k.VORSCHAU_ABSAGE);
    }
    for (const typ of ['render', VARIANTEN_TYP]) {
      expect(() => execute(doc, 'vis.nodeSetzen', { graphId, typ, x: 0, y: 0, params: { guete: 'vorschau' } })).toThrow(k.VORSCHAU_ABSAGE);
    }
    expect(JSON.stringify(doc.toJSON())).toBe(vorher);
  });

  it('vis.varianten mit einer alten Wahl «Vorschau» am Varianten-Knoten (Projekt von vorher) → Absage, bestellNr bleibt', () => {
    const doc = new KosmoDoc();
    const { graphId, variantenId } = graphMitKnoten(doc);
    const g = doc.get<VisGraph>(graphId)!;
    const alt: VisGraph = { ...g, nodes: g.nodes.map((n) => (n.id === variantenId ? { ...n, params: { ...(n.params ?? {}), guete: 'vorschau' } } : n)) };
    doc.apply([{ id: graphId, before: g, after: alt } as never]);
    const vorher = JSON.stringify(doc.get<VisGraph>(graphId));
    expect(() => execute(doc, 'vis.varianten', { nodeId: variantenId, standpunkte: ['sSE'] })).toThrow(k.VORSCHAU_ABSAGE);
    expect(JSON.stringify(doc.get<VisGraph>(graphId))).toBe(vorher);
  });

  it('Gegenprobe: guete:"voll" und ohne Feld bestellt vis.render wie bisher', () => {
    const doc = new KosmoDoc();
    const { graphId, renderId } = graphMitKnoten(doc);
    execute(doc, 'vis.render', { graphId, nodeId: renderId, guete: 'voll' });
    expect(doc.settings.visRenderAuftrag).toMatchObject({ guete: 'voll' });
    execute(doc, 'vis.render', { graphId, nodeId: renderId });
    expect(doc.settings.visRenderAuftrag).not.toHaveProperty('guete');
    execute(doc, 'vis.nodeParametrieren', { graphId, nodeId: renderId, params: { guete: 'voll' } });
  });
});

describe('A0061 (b) — Bildwerkzeuge ohne belegten Beauty-Eingang im Kern', () => {
  it('vis.render backbone:<gesperrt> → CommandError mit Satz, kein Auftrag; z-image-turbo geht', () => {
    const doc = new KosmoDoc();
    const { graphId, renderId } = graphMitKnoten(doc);
    for (const bw of GESPERRT) {
      const e = wirft(() => execute(doc, 'vis.render', { graphId, nodeId: renderId, backbone: bw }));
      expect(e, bw).toBeInstanceOf(CommandError);
      expect(e.message, bw).toContain(`Bildwerkzeug «${bw}» ist gesperrt`);
      expect(e.message, bw).toContain('Immer vom Render');
    }
    expect(doc.settings.visRenderAuftrag).toBeUndefined();
    execute(doc, 'vis.render', { graphId, nodeId: renderId, backbone: 'z-image-turbo' });
    expect(doc.settings.visRenderAuftrag).toMatchObject({ backbone: 'z-image-turbo' });
  });

  it('die Wahl am Knoten (nodeParametrieren, nodeSetzen) ist gesperrt; leer (Vorgabe) und z-image-turbo gehen', () => {
    const doc = new KosmoDoc();
    const { graphId, renderId } = graphMitKnoten(doc);
    const vorher = JSON.stringify(doc.toJSON());
    for (const bw of GESPERRT) {
      expect(() => execute(doc, 'vis.nodeParametrieren', { graphId, nodeId: renderId, params: { backbone: bw } }), bw).toThrow(`Bildwerkzeug «${bw}» ist gesperrt`);
      expect(() => execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0, params: { backbone: bw } }), bw).toThrow(CommandError);
    }
    expect(JSON.stringify(doc.toJSON())).toBe(vorher);
    execute(doc, 'vis.nodeParametrieren', { graphId, nodeId: renderId, params: { backbone: 'z-image-turbo' } });
    execute(doc, 'vis.nodeParametrieren', { graphId, nodeId: renderId, params: { backbone: '' } });
  });

  it('eine alte gesperrte Wahl am Render-Knoten: vis.render ohne backbone und vis.varianten werden abgewiesen', () => {
    const doc = new KosmoDoc();
    const { graphId, renderId, variantenId } = graphMitKnoten(doc);
    const g = doc.get<VisGraph>(graphId)!;
    const alt: VisGraph = { ...g, nodes: g.nodes.map((n) => (n.id === renderId ? { ...n, params: { ...(n.params ?? {}), backbone: 'qwen' } } : n)) };
    doc.apply([{ id: graphId, before: g, after: alt } as never]);
    expect(() => execute(doc, 'vis.render', { graphId, nodeId: renderId })).toThrow('Bildwerkzeug «qwen» ist gesperrt');
    expect(doc.settings.visRenderAuftrag).toBeUndefined();
    const vorher = JSON.stringify(doc.get<VisGraph>(graphId));
    expect(() => execute(doc, 'vis.varianten', { nodeId: variantenId, standpunkte: ['sSE'] })).toThrow('Bildwerkzeug «qwen» ist gesperrt');
    expect(JSON.stringify(doc.get<VisGraph>(graphId))).toBe(vorher);
    // Ein ausdruecklich belegtes Werkzeug im Aufruf gewinnt (wie im Versand: `opts.backbone` vor dem Knoten).
    execute(doc, 'vis.render', { graphId, nodeId: renderId, backbone: 'z-image-turbo' });
    expect(doc.settings.visRenderAuftrag).toMatchObject({ backbone: 'z-image-turbo' });
  });
});
