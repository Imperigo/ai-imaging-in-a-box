// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KosmoDoc } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import {
  GRAPH_ENTFERNT_SATZ,
  laufZugehoerigkeit,
  setzeProjektLeser,
  useVisRuntime,
} from '../src/modules/vis/vis-runtime';

/**
 * KosmoVis-Entscheide 1 und 2 (Gegenlesung 22.10.2026, Nachzug v0.1.10):
 * (1) kommt ein Projekt mit offenem Render-Lauf wieder nach vorne, wird der Lauf SOFORT abgefragt,
 *     nicht erst nach einem vollen Takt;
 * (2) ein Lauf, dessen Graph im eigenen Projekt geloescht oder per Rueckgaengig entfernt wurde, endet
 *     «abgebrochen» mit «Graph entfernt» — der Heim-PC rechnet zu Ende, abgelegt wird nichts.
 * Ein Lauf aus einem ANDEREN Projekt ruht weiter (Feldmeldung v0.1.8, `vis-lauf-fremdes-projekt`).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

describe('laufZugehoerigkeit', () => {
  const hatGraph = (id: string) => id === 'visgraph_hier';

  it('Graph im Dokument → hier; ohne Graph-Kennung (aelterer Weg) auch', () => {
    expect(laufZugehoerigkeit({ graphId: 'visgraph_hier', projekt: 'p1' }, hatGraph, 'p1')).toBe('hier');
    expect(laufZugehoerigkeit({}, hatGraph, 'p1')).toBe('hier');
  });

  it('Graph fehlt im eigenen Projekt → graph-entfernt', () => {
    expect(laufZugehoerigkeit({ graphId: 'visgraph_weg', projekt: 'p1' }, hatGraph, 'p1')).toBe('graph-entfernt');
  });

  it('Graph fehlt, Lauf aus anderem Projekt oder ohne Projekt → fremd (ruht)', () => {
    expect(laufZugehoerigkeit({ graphId: 'visgraph_weg', projekt: 'p1' }, hatGraph, 'p2')).toBe('fremd');
    expect(laufZugehoerigkeit({ graphId: 'visgraph_weg' }, hatGraph, 'p1')).toBe('fremd');
    expect(laufZugehoerigkeit({ graphId: 'visgraph_weg' }, hatGraph, undefined)).toBe('fremd');
  });
});

describe('setzeLauf stempelt das Projekt', () => {
  afterEach(() => setzeProjektLeser(() => undefined));

  it('nur an einem Lauf mit Graph, und nur wenn die App ein Projekt nennt', () => {
    setzeProjektLeser(() => 'p1');
    const { setzeLauf } = useVisRuntime.getState();
    setzeLauf('n-mit', { status: 'gesendet', memoKey: 'm', graphId: 'visgraph_a', gestartetUm: 1 });
    setzeLauf('n-ohne', { status: 'gesendet', memoKey: 'm', gestartetUm: 1 });
    expect(useVisRuntime.getState().laeufe['n-mit']?.projekt).toBe('p1');
    expect(useVisRuntime.getState().laeufe['n-ohne']?.projekt).toBeUndefined();
    setzeProjektLeser(() => undefined);
    setzeLauf('n-visbox', { status: 'gesendet', memoKey: 'm', graphId: 'visgraph_a', gestartetUm: 1 });
    expect(useVisRuntime.getState().laeufe['n-visbox']?.projekt).toBeUndefined();
  });
});

describe('Poll im Knoten-Canvas: Graph entfernt und Sofort-Abfrage', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;
  let projekt = 'p1';
  let anfragen: string[] = [];

  beforeEach(() => {
    projekt = 'p1';
    anfragen = [];
    setzeProjektLeser(() => projekt);
    useProject.setState({ doc: new KosmoDoc(), journal: [] });
    useVisRuntime.setState({ laeufe: {} });
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      anfragen.push(href);
      const jobId = href.split('/jobs/')[1] ?? '';
      return {
        ok: true,
        status: 200,
        json: async () => ({ job_id: jobId, status: 'rendering', scene: 's.json', idle_window_only: true, created_at: '2026-10-24T00:00:00Z' }),
      } as Response;
    }) as unknown as typeof fetch);
    vi.useFakeTimers();
  });

  afterEach(() => {
    if (root) {
      act(() => root!.unmount());
      root = null;
    }
    container?.remove();
    container = null;
    setzeProjektLeser(() => undefined);
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  function neuerGraph(): string {
    const g = useProject.getState().runCommand('vis.graphErstellen', { name: `Probe-${Math.random()}` });
    return (g.patches[0] as { id: string }).id;
  }

  function haengeEin(graphId: string): void {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });
  }

  it('Graph im eigenen Projekt entfernt → «abgebrochen» mit «Graph entfernt», keine Abfrage mehr', async () => {
    const gezeigt = neuerGraph();
    useVisRuntime.getState().setzeLauf('n-weg', {
      status: 'rendert',
      jobId: 'vis-1761300000-weg001',
      memoKey: 'm',
      graphId: 'visgraph_geloescht',
      gestartetUm: Date.now(),
    });
    expect(useVisRuntime.getState().laeufe['n-weg']?.projekt).toBe('p1');
    haengeEin(gezeigt);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });
    const lauf = useVisRuntime.getState().laeufe['n-weg'];
    expect(lauf?.status).toBe('abgebrochen');
    expect(lauf?.fehler).toBe(GRAPH_ENTFERNT_SATZ);
    expect(anfragen.some((a) => a.includes('weg001'))).toBe(false);
  });

  it('Lauf eines anderen Projekts ruht; kommt sein Projekt nach vorne, wird er sofort abgefragt', async () => {
    const graphId = neuerGraph();
    const docMitGraph = useProject.getState().doc;
    useVisRuntime.getState().setzeLauf('n-zurueck', {
      status: 'rendert',
      jobId: 'vis-1761300000-zur001',
      memoKey: 'm',
      graphId,
      gestartetUm: Date.now(),
    });
    // Wechsel ins andere Projekt: der Graph fehlt dort, der Lauf ruht (nicht «Graph entfernt»).
    projekt = 'p2';
    useProject.setState({ doc: new KosmoDoc() });
    haengeEin(neuerGraph());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });
    expect(useVisRuntime.getState().laeufe['n-zurueck']?.status).toBe('rendert');
    expect(anfragen.some((a) => a.includes('zur001'))).toBe(false);

    // Zurueck: die Abfrage kommt ohne einen weiteren Takt.
    projekt = 'p1';
    await act(async () => {
      useProject.setState({ doc: docMitGraph });
      await vi.advanceTimersByTimeAsync(10);
    });
    expect(anfragen.some((a) => a.includes('zur001'))).toBe(true);
  });
});
