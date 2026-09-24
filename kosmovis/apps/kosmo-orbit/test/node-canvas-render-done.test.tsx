// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';
import { memoKey, useVisRuntime } from '../src/modules/vis/vis-runtime';

/**
 * P-DONE (auftraege/von-homestation/auf-orbit-20260821-01.md, AUFTRAG 1):
 * die HomeStation hat gemessen, dass die Bridge auf `status:"done"` mit
 * vollem `result`-Block antwortet (237 Abfragen, alle 200 OK) — und der
 * Render-Node trotzdem bei "rendert" hängen bleibt. Bisher gab es dafür
 * KEINEN Test, der die echte Poll-Schleife (NodeCanvas.tsx, `useEffect` ab
 * Zeile 404) gegen eine gemockte Bridge-Antwort laufen lässt — nur `mappeJobStatus` isoliert
 * (vis-lebenszyklus.test.ts) und `postRenderJob`s Feld-Mapping
 * (pc2-vis-render-executor.test.ts). Dieser Test schliesst genau diese
 * Lücke: ein laufender Node + eine Bridge, die auf den ersten Poll mit
 * `done` + realistischem `render-result/v2` antwortet, MUSS den Node auf
 * «fertig» bringen und das Bild zeigen.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// jsdom kennt `URL.createObjectURL`/`revokeObjectURL` NICHT (bekannte Lücke,
// wie ResizeObserver oben) — `BridgeBild.tsx` ruft es nach jedem erfolgreich
// geholten Blob auf; ohne Stub wirft das, landet im eigenen `.catch()` und
// zeigt «Bild nicht ladbar», was NICHTS mit AUFTRAG 1 zu tun hat.
if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });
}

function graphMitRenderNode(): { graphId: string; renderNodeId: string } {
  const { runCommand, doc } = useProject.getState();
  const g = runCommand('vis.graphErstellen', { name: `P-DONE-Test-${Math.random()}` });
  const graphId = (g.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
  const renderNodeId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  return { graphId, renderNodeId };
}

/** Realistische Bridge-Antwort — wörtlich aus dem Homestation-Befund
 * (auf-orbit-20260821-01.md), ergänzt um die seit v0.9.42/1068 verbindlichen
 * QA-Pflichtfelder (rho_maske/kantenanteil/paarurteil, style_score:null). */
function doneJobRecord(jobId: string) {
  return {
    job_id: jobId,
    status: 'done',
    scene: `/tmp/kosmo-jobs/${jobId}/render-scene.json`,
    idle_window_only: true,
    created_at: '2026-08-20T10:00:00Z',
    updated_at: '2026-08-20T10:01:15Z',
    worker: 'real-worker',
    result: {
      schema: 'kosmovis.render-result/v2',
      job_id: jobId,
      images: ['sSE.png'],
      qa: {
        style: { style_score: null, threshold: null, passed: true, method: 'belichtungsrahmen/hausstil' },
        geometry: {
          rho_maske: -0.9059,
          kantenanteil: 0.874,
          paarurteil: { rho_maske: -0.9059, kantenanteil: 0.874 },
          passed: true,
          method: 'depthanything-v2-redepth',
        },
        verdict: { passed: true },
      },
      timings: { sSE: 40.7, gesamt: 40.7 },
    },
  };
}

function stubFetchDoneBridge(jobId: string): { anfragen: string[] } {
  const anfragen: string[] = [];
  vi.stubGlobal('fetch', (async (url: unknown) => {
    const href = String(url);
    anfragen.push(href);
    if (href.endsWith(`/jobs/${jobId}`)) {
      return { ok: true, status: 200, json: async () => doneJobRecord(jobId) } as Response;
    }
    if (href.includes(`/jobs/${jobId}/artifacts/`)) {
      return { ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) } as Response;
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch);
  return { anfragen };
}

describe('NodeCanvas — Render-Node reagiert auf status:"done" (P-DONE, HomeStation-Befund 21.08.2026)', () => {
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

  it('ein Poll mit status:"done" + vollem result-Block bringt den Node auf «fertig» und zeigt das Bild', async () => {
    const jobId = 'vis-1787245160-895ba3';
    const { graphId, renderNodeId } = graphMitRenderNode();

    // memoKey EXAKT wie `sendeGraphRenderAuftrag` ihn beim echten Absenden
    // berechnet (vis-jobs.ts:379) — sonst meldet der unabhängige
    // «veraltet»-Mechanismus (NodeCanvas.tsx:1052-1055) einen Treffer, der
    // mit AUFTRAG 1 (Reaktion auf status:"done") nichts zu tun hat und die
    // Zusicherung hier verfälschen würde.
    const { doc } = useProject.getState();
    const graph = doc.get<VisGraph>(graphId)!;
    const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
    const echterMemoKey = memoKey(auftrag);

    // Der Node läuft bereits (wie nach einem echten "Ausführen"-Klick) —
    // dieselbe Vorbedingung, die die HomeStation gemessen hat: ein jobId
    // ist da, der Status steht auf "rendert", die Bridge liefert "done".
    useVisRuntime.getState().setzeLauf(renderNodeId, {
      status: 'rendert',
      jobId,
      memoKey: echterMemoKey,
      gestartetUm: Date.now(),
    });

    const { anfragen } = stubFetchDoneBridge(jobId);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.useFakeTimers();
    act(() => {
      root!.render(<NodeCanvas graphId={graphId} />);
    });

    // Die Poll-Schleife steht auf 2500 ms (NodeCanvas.tsx:472) — EIN Tick
    // reicht, um den ersten Poll auszulösen; await, damit die async
    // holeJob()-Kette (fetch → json → parseJob → patchLauf) durchläuft.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });

    expect(anfragen.some((a) => a.endsWith(`/jobs/${jobId}`))).toBe(true);

    const statusEl = container.querySelector('[data-testid="render-status"]');
    expect(statusEl).not.toBeNull();
    // DER ROTE BEFUND (vor der Reparatur): dieses Feld blieb "rendert" statt
    // "fertig" zu werden, obwohl useVisRuntime.getState().laeufe[...].status
    // bereits "fertig" war — der Bruch lag in der ANZEIGE, nicht im Store.
    expect(statusEl!.textContent).toBe('fertig');

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    expect(lauf?.status).toBe('fertig');
    expect(lauf?.bild).toBe('sSE.png');

    // BridgeBild.tsx holt das Bild ERST NACH dem Mount per eigenem
    // useEffect (bildBlob() → fetch → blob()) — eine zweite, unabhängige
    // Mikrotask-Kette. Mehrere Flush-Runden, bis sie durchgelaufen ist.
    for (let i = 0; i < 5; i++) {
      // eslint-disable-next-line no-await-in-loop
      await act(async () => {
        await vi.advanceTimersByTimeAsync(50);
      });
    }

    const bildEl = container.querySelector('[data-testid="render-bild"]');
    expect(bildEl).not.toBeNull();
  });

  /**
   * Der zweite, unabhängige Befund aus derselben Untersuchung: der happy
   * path oben ist bereits repariert (P-KANTENANTEIL/1068 + die v0.9.42-QA-
   * Feldfreigaben) — aber die Ursachenklasse, die AUFTRAG 1 am 20.08.
   * tatsächlich ausgelöst hat, ist NICHT geschlossen. `holeJob` wirft eine
   * normale `Error` (WEDER `TypeError` [Netzfehler] NOCH `BridgeHttpError`
   * [Auth/HTTP-Status]), wenn `RenderJob.safeParse` eine `res.ok`-Antwort
   * ablehnt (`vis-jobs.ts` `parseJob`) — z.B. weil ein Feld fehlt/anders
   * heisst, exakt das Muster, das `kantenanteil` vor 1068 auslöste. Der
   * Catch-Handler in NodeCanvas.tsx (Zeile ~452-470) behandelt genau diesen
   * Fall NICHT: nur `istAuthFehler` löst eine ehrliche Fehleranzeige aus,
   * alles andere fällt durch den Kommentar «Transiente Netzfehler NICHT
   * hochziehen» lautlos durch. Jeder Folge-Poll holt denselben, weiterhin
   * unverständlichen Datensatz — der Lauf bleibt für immer bei "rendert"
   * stehen, ohne dass der Nutzer je einen Grund sieht. Das ist die Lücke,
   * die 237 Abfragen über 8 Minuten in der HomeStation-Messung erzeugt hat.
   */
  it('eine schema-ungültige status:"done"-Antwort bleibt NICHT lautlos für immer bei "rendert" stehen', async () => {
    const jobId = 'vis-1787245160-895ba3';
    const { graphId, renderNodeId } = graphMitRenderNode();
    const { doc } = useProject.getState();
    const graph = doc.get<VisGraph>(graphId)!;
    const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
    const echterMemoKey = memoKey(auftrag);

    useVisRuntime.getState().setzeLauf(renderNodeId, {
      status: 'rendert',
      jobId,
      memoKey: echterMemoKey,
      gestartetUm: Date.now(),
    });

    // Vertragswidrig: `qa.geometry` OHNE das Pflichtfeld `passed` (kein
    // Default im Schema) — dieselbe Fehlerklasse wie der reale
    // `paarurteil.kante`-Fund vor 1068, nur an einer anderen Stelle im
    // selben Objekt. `RenderJob.safeParse` lehnt den GANZEN Record ab.
    let anfragen = 0;
    vi.stubGlobal('fetch', (async (url: unknown) => {
      const href = String(url);
      if (href.endsWith(`/jobs/${jobId}`)) {
        anfragen++;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            job_id: jobId,
            status: 'done',
            scene: `/tmp/kosmo-jobs/${jobId}/render-scene.json`,
            idle_window_only: true,
            created_at: '2026-08-20T10:00:00Z',
            result: {
              schema: 'kosmovis.render-result/v2',
              job_id: jobId,
              images: ['sSE.png'],
              qa: {
                geometry: { rho_maske: -0.9, kantenanteil: 0.8, method: 'x' }, // passed FEHLT
                verdict: { passed: true },
              },
            },
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

    // Drei Zeitfenster (7.5 s) angeboten — VOR der Reparatur hätte das drei
    // identisch abgelehnte Polls gegeben (der Datensatz ändert sich nicht,
    // 237 Wiederholungen im echten Befund bewiesen das). NACH der
    // Reparatur markiert schon der ERSTE Poll den Lauf "fehler", und
    // "fehler" steht nicht in `OFFENE_LAUF_STATUS` (vis-runtime.ts) — der
    // Poll fragt einen fertig gescheiterten Lauf konsequenterweise nicht
    // weiter ab. EIN Request ist darum das korrekte Bild nach dem Fix.
    for (let i = 0; i < 3; i++) {
      // eslint-disable-next-line no-await-in-loop
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2600);
      });
    }
    expect(anfragen).toBe(1);

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    const statusEl = container.querySelector('[data-testid="render-status"]');
    // NACH DER REPARATUR: eine schema-ungültige, aber erfolgreich
    // zugestellte ("res.ok") Antwort MUSS als ehrlicher Fehler ankommen —
    // nicht als endloses "rendert".
    expect(lauf?.status).toBe('fehler');
    expect(statusEl!.textContent).toBe('fehler');
    // Die Meldung nennt den Vertragsbruch beim Namen (`parseJob`,
    // vis-jobs.ts) statt nur "irgendwas stimmt nicht" — das fehlende
    // `passed`-Feld MUSS in der Zeile auftauchen.
    expect(lauf?.fehler).toMatch(/passed/);
  });
});
