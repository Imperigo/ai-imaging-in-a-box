// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import {
  memoKey,
  useVisRuntime,
  wartetAbholerLabel,
  wartetAbholerText,
  WARTET_ABHOLER_LABEL,
} from '../src/modules/vis/vis-runtime';

/**
 * Auftrag auf-20260901-70 (Posten 1, `docs/auftraege-kosmovis/
 * auf-20260901-70.md`) — die Bridge schreibt seit 01.09.2026 den Wartegrund
 * in `RenderJob.message`, solange ein Job `queued` bleibt. Vorher las
 * `NodeCanvas.tsx` `j.message` NUR im Zweig `kein-render-worker`; für
 * `queued` fiel der Poll auf `mappeJobStatus(j)` und der Node zeigte
 * unveränderlich «wartet — nicht abgeholt (Grund unbekannt)» — selbst wenn
 * die Bridge den Grund alle 30 Sekunden mitschickte (das Journal-Beispiel
 * aus dem Auftrag: «Karte: NICHT frei - Auslastung 12 % (Grenze 10 %)»).
 *
 * Diese Datei prüft BEIDE Hälften der Auflage: mit `message` erscheint der
 * echte Grund (kein erfundener Ersatztext), ohne `message` bleibt die
 * Beschriftung BYTE-GLEICH zum heutigen Stand.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

function graphMitRenderNode(): { graphId: string; renderNodeId: string } {
  const { runCommand, doc } = useProject.getState();
  const g = runCommand('vis.graphErstellen', { name: `auf-20260901-70-Test-${Math.random()}` });
  const graphId = (g.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
  const renderNodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  return { graphId, renderNodeId };
}

function queuedJobRecord(jobId: string, message?: string) {
  return {
    job_id: jobId,
    status: 'queued',
    scene: `/tmp/kosmo-jobs/${jobId}/render-scene.json`,
    idle_window_only: true,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:00:30Z',
    ...(message !== undefined ? { message } : {}),
  };
}

function stubFetchQueuedBridge(jobId: string, message?: string): void {
  vi.stubGlobal('fetch', (async (url: unknown) => {
    const href = String(url);
    if (href.endsWith(`/jobs/${jobId}`)) {
      return { ok: true, status: 200, json: async () => queuedJobRecord(jobId, message) } as Response;
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch);
}

describe('wartetAbholerText / wartetAbholerLabel mit Grund (Auftrag auf-20260901-70)', () => {
  it('ohne Grund bleibt der Wortlaut BYTE-GLEICH zum heutigen Stand', () => {
    expect(wartetAbholerLabel(undefined)).toBe(WARTET_ABHOLER_LABEL);
    expect(wartetAbholerText(undefined, 0)).toBe(
      'wartet — noch nicht abgeholt (Grund unbekannt). Läuft auf der HomeStation ein Render-Abholer?',
    );
    // Ein leerer String ist KEIN Grund — dieselbe Regel wie beim Vertrag
    // selbst («kein erfundener Text»): eine leere `message` darf nicht wie
    // ein gelieferter Grund behandelt werden.
    expect(wartetAbholerLabel('')).toBe(WARTET_ABHOLER_LABEL);
    expect(wartetAbholerText(undefined, 0, '')).toBe(
      'wartet — noch nicht abgeholt (Grund unbekannt). Läuft auf der HomeStation ein Render-Abholer?',
    );
  });

  it('mit Grund erscheint der WÖRTLICHE Vertragstext statt der Ersatzzeile', () => {
    const grund = "Der Auftrag traegt 'idle_window_only' und die Karte ist nicht frei: Auslastung 12 % (Grenze 10 %).";
    expect(wartetAbholerLabel(grund)).not.toBe(WARTET_ABHOLER_LABEL);
    expect(wartetAbholerLabel(grund).toLowerCase()).not.toContain('grund unbekannt');
    const text = wartetAbholerText(undefined, 0, grund);
    expect(text).toContain(grund);
    // Die «Läuft auf der HomeStation ein Render-Abholer?»-Vermutung ist mit
    // bekanntem Grund FALSCH (der Abholer läuft nachweislich) — sie darf mit
    // Grund nicht mehr auftauchen.
    expect(text).not.toContain('Läuft auf der HomeStation ein Render-Abholer?');
    expect(text).not.toContain('Grund unbekannt');
  });
});

describe('NodeCanvas — Render-Node zeigt den echten Wartegrund bei "queued" (Auftrag auf-20260901-70)', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root!.unmount());
      root = null;
    }
    if (container) {
      container.remove();
      container = null;
    }
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('ein Poll mit status:"queued" + message zeigt den Grund am Node, nicht «Grund unbekannt»', async () => {
    const jobId = 'vis-1788277501-b799e4';
    const grund =
      "Der Auftrag traegt 'idle_window_only' und die Karte ist nicht frei: Auslastung 12 % (Grenze 10 %).";
    const { graphId, renderNodeId } = graphMitRenderNode();

    const { doc } = useProject.getState();
    const graph = doc.get<VisGraph>(graphId)!;
    const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
    const echterMemoKey = memoKey(auftrag);

    useVisRuntime.getState().setzeLauf(renderNodeId, {
      status: 'gesendet',
      jobId,
      memoKey: echterMemoKey,
      gestartetUm: Date.now(),
    });

    stubFetchQueuedBridge(jobId, grund);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.useFakeTimers();
    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    expect(lauf?.status).toBe('wartetGpu');
    expect(lauf?.wartetGrund).toBe(grund);

    const statusEl = container.querySelector('[data-testid="render-status"]');
    expect(statusEl).not.toBeNull();
    expect(statusEl!.textContent).not.toContain('Grund unbekannt');

    // DOM-erkennbarer Unterschied (Fable-Auflage): ein eigenes Attribut,
    // nicht nur ein Text-Unterschied — ein Test kann «Grund bekannt» gezielt
    // abfragen, ohne den genauen Wortlaut zu kennen.
    const platzhalter = container.querySelector('[data-testid="render-wartet-text"]');
    expect(platzhalter).not.toBeNull();
    expect(platzhalter!.getAttribute('data-grund-bekannt')).toBe('true');
    expect(platzhalter!.textContent).toContain(grund);
  });

  it('ein Poll mit status:"queued" OHNE message bleibt bei der heutigen Beschriftung — kein erfundener Grund', async () => {
    const jobId = 'vis-1788277502-c8aa5f';
    const { graphId, renderNodeId } = graphMitRenderNode();

    const { doc } = useProject.getState();
    const graph = doc.get<VisGraph>(graphId)!;
    const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
    const echterMemoKey = memoKey(auftrag);

    useVisRuntime.getState().setzeLauf(renderNodeId, {
      status: 'gesendet',
      jobId,
      memoKey: echterMemoKey,
      gestartetUm: Date.now(),
    });

    stubFetchQueuedBridge(jobId, undefined);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.useFakeTimers();
    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    expect(lauf?.status).toBe('wartetGpu');
    expect(lauf?.wartetGrund).toBeUndefined();

    const statusEl = container.querySelector('[data-testid="render-status"]');
    expect(statusEl!.textContent).toBe(WARTET_ABHOLER_LABEL);

    const platzhalter = container.querySelector('[data-testid="render-wartet-text"]');
    expect(platzhalter).not.toBeNull();
    expect(platzhalter!.getAttribute('data-grund-bekannt')).toBe('false');
    expect(platzhalter!.textContent).toContain('Grund unbekannt');
  });

  it('der Grund wird gelöscht, sobald der Job nicht mehr "queued" ist — kein stehenbleibender alter Grund', async () => {
    const jobId = 'vis-1788277503-d9bb6a';
    const grund = 'Karte belegt.';
    const { graphId, renderNodeId } = graphMitRenderNode();

    const { doc } = useProject.getState();
    const graph = doc.get<VisGraph>(graphId)!;
    const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
    const echterMemoKey = memoKey(auftrag);

    useVisRuntime.getState().setzeLauf(renderNodeId, {
      status: 'gesendet',
      jobId,
      memoKey: echterMemoKey,
      gestartetUm: Date.now(),
    });

    // Erste Antwort: queued MIT Grund. Zweite Antwort: running OHNE `message`
    // (die Vertragszusage — «message wird gelöscht, sobald der Auftrag
    // läuft»). `patchLauf` MISCHT — ohne die explizite Weitergabe im `marker`
    // bliebe der alte Grund über den Statuswechsel hinweg stehen.
    let anfragen = 0;
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      if (href.endsWith(`/jobs/${jobId}`)) {
        anfragen++;
        const record =
          anfragen === 1
            ? queuedJobRecord(jobId, grund)
            : { ...queuedJobRecord(jobId, undefined), status: 'running', progress: { phase: 'render', pct: 0.1 } };
        return { ok: true, status: 200, json: async () => record } as Response;
      }
      return { ok: false, status: 404, json: async () => ({}) } as Response;
    }) as unknown as typeof fetch);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.useFakeTimers();
    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });
    expect(useVisRuntime.getState().laeufe[renderNodeId]?.wartetGrund).toBe(grund);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });
    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    expect(lauf?.status).toBe('rendert');
    expect(lauf?.wartetGrund).toBeUndefined();
  });
});
