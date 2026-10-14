// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import { memoKey, useVisRuntime } from '../src/modules/vis/vis-runtime';

/**
 * P11/B6 (V016-SPEZ, Strang Bildstrecke) — Befund: der Poll in
 * `NodeCanvas.tsx` (`useEffect` ab Zeile ~865) zeigte bei `status:"error"`
 * IMMER den festen Satz «Render fehlgeschlagen» — auch wenn die Bridge einen
 * echten Grund mitschickte (`RenderJob.error`/`message`, z. B. «ComfyUI-
 * Timeout nach 300s bei Kamera 'Eingang'.», wörtlich so geschrieben von
 * `kosmo_worker_comfyui.py`). Und ein HTTP-Fehler der Bridge
 * (`BridgeHttpError`, z. B. 404/502) UND ein echter Netzfehler (`TypeError`)
 * fielen im `catch`-Block lautlos durch den Kommentar «Transiente Netzfehler
 * NICHT hochziehen» — bewusst UNVERÄNDERT dabei bleibt, dass ein einmaliger
 * Aussetzer den Lauf nicht sofort auf «fehler» kippt (derselbe Entscheid wie
 * beim Viewport3D-Zwilling, `viewport3d-render-vertragsbruch.test.ts`
 * GEGENPROBEN, ausserhalb dieses Pakets NICHT angefasst) — aber der GRUND
 * war bisher NIRGENDS zu sehen. Diese Suite zeigt beide Lücken zuerst rot,
 * dann grün nach der Reparatur (neues `NodeLauf.bridgeHinweis`-Feld,
 * `vis-runtime.ts`).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });
}

function graphMitRenderNode(): { graphId: string; renderNodeId: string } {
  const { runCommand, doc } = useProject.getState();
  const g = runCommand('vis.graphErstellen', { name: `P11-B6-Test-${Math.random()}` });
  const graphId = (g.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
  const renderNodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  return { graphId, renderNodeId };
}

// P11/B6-Randnotiz (nicht Teil des Befunds, aber beim Bau gefunden): der
// Zustand `useVisRuntime` wird zwischen `it()`-Blöcken NICHT zurückgesetzt
// (dasselbe gewachsene Muster wie `pc2-vis-render-executor.test.ts`s
// Kopfkommentar zu `useProject`). B6b/B6c lassen den Lauf ABSICHTLICH offen
// (`status: 'rendert'`, s. deren eigenen Kommentar) — ein GEMEINSAMER, fest
// verdrahteter `jobId` über mehrere Tests hinweg hätte den Poll-Effekt dann
// MEHRERE offene Läufe mit demselben `jobId` gleichzeitig abfragen lassen,
// und der lokale `ersterVersuch`-Zähler des Fetch-Stubs wäre vom FALSCHEN
// Node verbraucht worden (gemessen: B6d schlug genau so fehl). Ein
// eindeutiger `jobId` je Aufruf schliesst das, unabhängig vom
// Store-Zustand — dieselbe Vertrags-Form wie im Bestand
// (`/^vis-\d+-[0-9a-f]{6}$/`, `RenderJob.job_id`).
let starteLaufendenNodeZaehler = 0;
function starteLaufendenNode(): { graphId: string; renderNodeId: string; jobId: string } {
  const jobId = `vis-1787245160-${(++starteLaufendenNodeZaehler).toString(16).padStart(6, '0')}`;
  const { graphId, renderNodeId } = graphMitRenderNode();
  const { doc } = useProject.getState();
  const graph = doc.get<VisGraph>(graphId)!;
  const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
  useVisRuntime.getState().setzeLauf(renderNodeId, {
    status: 'rendert',
    jobId,
    memoKey: memoKey(auftrag),
    gestartetUm: Date.now(),
  });
  return { graphId, renderNodeId, jobId };
}

describe('NodeCanvas — Fehlergrund sichtbar (P11/B6)', () => {
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

  it('B6a: status:"error" mit echtem Bridge-Grund (message) zeigt DIESEN Grund, nicht den festen Satz «Render fehlgeschlagen»', async () => {
    const { graphId, renderNodeId, jobId } = starteLaufendenNode();
    const grund = "ComfyUI-Timeout nach 300s bei Kamera 'Eingang'.";
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      if (href.endsWith(`/jobs/${jobId}`)) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            job_id: jobId,
            status: 'error',
            scene: `/tmp/kosmo-jobs/${jobId}/render-scene.json`,
            idle_window_only: true,
            created_at: '2026-09-20T10:00:00Z',
            message: grund,
          }),
        } as Response;
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

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    expect(lauf?.status).toBe('fehler');
    // VOR der Reparatur: lauf?.fehler === 'Render fehlgeschlagen' (fester Satz,
    // der echte Grund ging verloren).
    expect(lauf?.fehler).toBe(grund);
  });

  it('B6b: ein 404 der Bridge (BridgeHttpError) bleibt offen (kein sofortiges «fehler» — bewusst unverändert), aber der Grund wird sichtbar', async () => {
    const { graphId, renderNodeId, jobId } = starteLaufendenNode();
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      if (href.endsWith(`/jobs/${jobId}`)) {
        return { ok: false, status: 404, json: async () => ({}) } as Response;
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

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    // Bewusst UNVERÄNDERT: ein einmaliger 404 tötet den Lauf nicht.
    expect(lauf?.status).toBe('rendert');
    // VOR der Reparatur: `bridgeHinweis` existierte nicht, der 404 fiel
    // lautlos durch — hier MUSS der Status-Code auftauchen.
    expect(lauf?.bridgeHinweis).toMatch(/404/);
  });

  it('B6c: ein echter Netzfehler (TypeError) bleibt offen, aber der Grund wird sichtbar', async () => {
    const { graphId, renderNodeId } = starteLaufendenNode();
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch');
      }),
    );

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
    expect(lauf?.status).toBe('rendert');
    // VOR der Reparatur: `bridgeHinweis` existierte nicht, der Netzfehler
    // fiel lautlos durch.
    expect(lauf?.bridgeHinweis).toBeTruthy();
  });

  it('B6d: nach einem sichtbaren Hinweis räumt ein erfolgreicher Folge-Poll ihn wieder weg', async () => {
    const { graphId, renderNodeId, jobId } = starteLaufendenNode();
    let ersterVersuch = true;
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      if (href.endsWith(`/jobs/${jobId}`)) {
        if (ersterVersuch) {
          ersterVersuch = false;
          return { ok: false, status: 502, json: async () => ({}) } as Response;
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({
            job_id: jobId,
            status: 'running',
            scene: `/tmp/kosmo-jobs/${jobId}/render-scene.json`,
            idle_window_only: true,
            created_at: '2026-09-20T10:00:00Z',
          }),
        } as Response;
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
    expect(useVisRuntime.getState().laeufe[renderNodeId]?.bridgeHinweis).toMatch(/502/);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });
    expect(useVisRuntime.getState().laeufe[renderNodeId]?.bridgeHinweis).toBeUndefined();
  });
});
