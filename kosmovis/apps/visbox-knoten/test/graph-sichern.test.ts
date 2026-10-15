// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { ladeGesichertenGraph, legeGraphen, renderGraphen, sichereBeiAenderung } from '../src/graph-sichern';

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
});
