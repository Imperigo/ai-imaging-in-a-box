// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { graphDerNeuenMappe, ladeGesichertenGraph, legeGraphen, renderGraphen, sichereBeiAenderung } from '../src/graph-sichern';
import { registriereMappenWechsel, verfolge, type LadeStand } from '../src/mappe';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { registriereModellLaden } from '../../kosmo-orbit/src/modules/vis/modell-laden';
import { groessteNodeHoehe } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';

/**
 * VISBOX-EIGEN (15.10.2026, auf-20261015-286): Nach dem Neuladen war der Graph weg. Der Wirt
 * legt den gesicherten Graph der Mappe vor dem ersten Bild ins Dokument und sichert jede
 * Änderung (verzögert, nur wenn sich etwas geändert hat).
 */
const GRAPH: VisGraph = { id: 'visgraph_probe', kind: 'visgraph', name: 'Bilder', nodes: [], edges: [] } as VisGraph;

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), revision: 0 } as never);
});
afterEach(() => {
  vi.useRealTimers();
});

describe('Graph der Mappe', () => {
  it('legt den gesicherten Graph ins Dokument', async () => {
    const holen = vi.fn(async () => new Response(JSON.stringify({ graphen: [GRAPH] }), { status: 200 }));
    expect(await ladeGesichertenGraph(holen as unknown as typeof fetch)).toBe(1);
    expect(renderGraphen().map((g) => g.id)).toEqual(['visgraph_probe']);
    expect(holen).toHaveBeenCalledWith('./graph');
  });

  it('ohne Antwort bleibt das Dokument leer und nichts wirft', async () => {
    const holen = vi.fn(async () => {
      throw new Error('kein Netz');
    });
    expect(await ladeGesichertenGraph(holen as unknown as typeof fetch)).toBe(0);
    expect(renderGraphen()).toEqual([]);
  });

  it('sichert nach einer Änderung, verzögert und nur einmal je Stand', async () => {
    vi.useFakeTimers();
    const senden = vi.fn(async () => undefined);
    const ab = sichereBeiAenderung(senden, 1000);
    legeGraphen([GRAPH]);
    expect(senden).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1000);
    expect(senden).toHaveBeenCalledTimes(1);
    expect(JSON.parse(senden.mock.calls[0][0] as string).graphen[0].id).toBe('visgraph_probe');
    // Revision ohne inhaltliche Änderung: nichts erneut senden.
    useProject.setState((s) => ({ revision: s.revision + 1 }));
    vi.advanceTimersByTime(1000);
    expect(senden).toHaveBeenCalledTimes(1);
    ab();
  });

  it('ein vorher gesicherter Graph mit überlappenden Knoten wird beim Legen einmal entzerrt (Owner-Befund 20.10.2026)', () => {
    registriereModellLaden({ formate: ['IFC'], annehmen: '.ifc', laden: async () => ({ stand: 'leer' }) });
    try {
      // So lag der Anfang, als der Modell-Knoten noch ohne 3D-Fenster war: Kamera 204 + 32 px darunter.
      const alt = {
        ...GRAPH,
        id: 'visgraph_alt',
        nodes: [
          { id: 'm', typ: 'modell', x: 40, y: 400, params: {} },
          { id: 'k', typ: 'kamera', x: 40, y: 636, params: {} },
          { id: 'r', typ: 'render', x: 600, y: 40, params: {} },
        ],
      } as VisGraph;
      legeGraphen([alt]);
      const g = renderGraphen().find((x) => x.id === 'visgraph_alt')!;
      const m = g.nodes.find((n) => n.id === 'm')!;
      const k = g.nodes.find((n) => n.id === 'k')!;
      expect(m.y, 'das Modell bleibt').toBe(400);
      expect(k.y, 'die Kamera steht unter dem ganzen Modell-Knoten').toBeGreaterThanOrEqual(400 + groessteNodeHoehe('modell'));
      expect(g.nodes.find((n) => n.id === 'r')!.y, 'die andere Spalte bleibt').toBe(40);
    } finally {
      registriereModellLaden(null);
    }
  });

  it('ohne Überlappung bleibt der gesicherte Graph Pixel für Pixel', () => {
    const frei = {
      ...GRAPH,
      id: 'visgraph_frei',
      nodes: [
        { id: 'm', typ: 'modell', x: 40, y: 40, params: {} },
        { id: 'k', typ: 'kamera', x: 40, y: 900, params: {} },
      ],
    } as VisGraph;
    legeGraphen([frei]);
    expect(renderGraphen().find((x) => x.id === 'visgraph_frei')).toEqual(frei);
  });
});

/**
 * Generalprobe 327 (S2, 22.10.2026): Nach «Datei laden …» blieb der Graph der vorigen Mappe stehen; der
 * fertige Anfang der neuen erschien erst nach dem Neuladen der Seite.
 */
describe('eine andere Mappe, ihr Graph (Generalprobe 327, S2)', () => {
  const ALT: VisGraph = { id: 'visgraph_alt', kind: 'visgraph', name: 'Alt', nodes: [], edges: [] } as VisGraph;

  it('nimmt den Graph der vorigen Mappe heraus und legt den gesicherten der neuen', async () => {
    legeGraphen([ALT]);
    const holen = vi.fn(async () => new Response(JSON.stringify({ graphen: [GRAPH] }), { status: 200 }));
    expect(await graphDerNeuenMappe(holen as unknown as typeof fetch)).toBe(1);
    expect(renderGraphen().map((g) => g.id)).toEqual(['visgraph_probe']);
    expect(useVisRuntime.getState().aktiverGraphId).toBe('visgraph_probe');
  });

  it('hat die neue Mappe keinen Graph, steht der fertige Anfang da — ohne Neuladen', async () => {
    legeGraphen([ALT]);
    const holen = vi.fn(async () => new Response(JSON.stringify({ graphen: [] }), { status: 200 }));
    expect(await graphDerNeuenMappe(holen as unknown as typeof fetch)).toBe(1);
    const graphen = renderGraphen();
    expect(graphen).toHaveLength(1);
    expect(graphen[0]!.id).not.toBe('visgraph_alt');
    expect(graphen[0]!.nodes.map((n) => n.typ)).toEqual(
      expect.arrayContaining(['stimmung', 'prompt', 'modell', 'kamera', 'render', 'varianten', 'vergleich', 'materialTextur', 'material']),
    );
  });

  it('nach «Datei laden …» in eine andere Mappe geht der Wechsel los, bei einer neuen Fassung derselben nicht', async () => {
    const wechsel = vi.fn(async () => 1);
    registriereMappenWechsel(wechsel);
    let name = 'erste';
    vi.stubGlobal('fetch', async (url: string) => {
      if (String(url).startsWith('./mappe')) {
        return new Response(JSON.stringify({ name, mappe: name, glb: false, huellbox_m: null, hochachse: null, grund: '', huellbox_vermerk: '' }), { status: 200 });
      }
      return new Response('{}', { status: 200 });
    });
    try {
      const stand = (mappe: string): LadeStand => ({ kennung: 'k1', stand: 'geladen', datei: 'testbau.glb', satz: 'geladen', schritt: null, seit_s: 1, mappe });
      await verfolge(stand('erste'), () => {});
      expect(wechsel).toHaveBeenCalledTimes(1); // von «keiner» zu «erste»
      await verfolge(stand('erste'), () => {});
      expect(wechsel).toHaveBeenCalledTimes(1); // neue Fassung derselben Mappe: der Graph bleibt
      name = 'testbau';
      await verfolge(stand('testbau'), () => {});
      expect(wechsel).toHaveBeenCalledTimes(2);
    } finally {
      registriereMappenWechsel(null);
      vi.unstubAllGlobals();
    }
  });
});
