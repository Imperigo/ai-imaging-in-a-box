// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph, type VisNode } from '@kosmo/kernel';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import { BildKachel, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { lieferVorbehalt, quelleAusLauf, type KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import { holeJob, type JobQa } from '../src/modules/vis/vis-jobs';
import { memoKey, useVisRuntime } from '../src/modules/vis/vis-runtime';
import { useProject } from '../src/state/project-store';

/**
 * kv-lieferstatus-null (KosmoVis L1, Antwortblatt
 * `auftraege/ergebnisse/erg-20261001-216-kosmovis-v017.md` L1): ein Ergebnis
 * mit `lieferstatus: null` («nicht festgestellt») ist ein VORBEHALT. Vorher
 * warf `parseJob` es samt allen Bildern weg; jetzt wird es angenommen, als
 * benannter Mangel gemeldet und in Kachel und Inspektor als Vorbehalt
 * gezeigt, nie als «geliefert».
 *
 * Abnahme (a) und (d) aus dem Auftrag; (b) und (c) stehen am Vertrag
 * (`packages/kosmo-contracts/test/kv-lieferstatus-null.test.ts`).
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

const JOB_ID = 'vis-1790000000-11a0ff';
const GRUND = 'Nicht festgestellt: die Bilderzahl der Kameras passt nicht zur Bildliste.';

/** Die Form, wie der Schreiber der Gegenseite sendet (Auftrag vom 01.10.2026). */
function ergebnisMitNull(): Record<string, unknown> {
  return {
    schema: 'kosmovis.render-result/v2',
    job_id: JOB_ID,
    images: ['sSE.png', 'sNW.png'],
    lieferstatus: null,
    lieferstatus_grund: GRUND,
    qa: { verdict: { passed: true, reason: '', hinweise: [] } },
  };
}

function stubBridge(result: Record<string, unknown>): void {
  vi.stubGlobal('fetch', (async (url: unknown) => {
    const href = String(url);
    if (href.endsWith(`/jobs/${JOB_ID}`)) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          job_id: JOB_ID,
          status: 'done',
          scene: `jobs/${JOB_ID}/render-scene.json`,
          created_at: '2026-10-01T10:00:00Z',
          result,
        }),
      } as Response;
    }
    if (href.includes(`/jobs/${JOB_ID}/artifacts/`)) {
      return { ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) } as Response;
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch);
}

const qaOk: JobQa = { verdict: { passed: true } };

describe('kv-lieferstatus-null', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;
  afterEach(() => {
    if (root) act(() => root!.unmount());
    container?.remove();
    root = null;
    container = null;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });
  function mount(el: React.ReactElement) {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(el));
  }

  it('(a) parseJob nimmt lieferstatus: null an, mit allen Bildern und EINER benannten Mangelzeile', async () => {
    stubBridge(ergebnisMitNull());
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    const job = await holeJob(JOB_ID);

    expect(job.status).toBe('done');
    expect(job.result?.lieferstatus).toBeNull();
    expect(job.result?.images).toEqual(['sSE.png', 'sNW.png']);
    expect(job.result?.qa.verdict.passed).toBe(true);
    expect(warnSpy).toHaveBeenCalledTimes(1);
    const meldung = String(warnSpy.mock.calls[0]?.[0]);
    expect(meldung).toContain('[E123]');
    expect(meldung).toContain(`Lieferstatus nicht festgestellt: ${GRUND}`);
  });

  it('(a) der Poll am Knotenfeld bringt den Lauf auf «fertig» und traegt den Vorbehalt mit', async () => {
    const { runCommand, doc } = useProject.getState();
    const g = runCommand('vis.graphErstellen', { name: `L1-Test-${Math.random()}` });
    const graphId = (g.patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 200, y: 0 });
    const graph = doc.get<VisGraph>(graphId)!;
    const renderNodeId = graph.nodes.at(-1)!.id;
    const auftrag = evaluiereGraph(doc, graph).renderAuftraege.get(renderNodeId)!;
    useVisRuntime.getState().setzeLauf(renderNodeId, {
      status: 'rendert',
      jobId: JOB_ID,
      memoKey: memoKey(auftrag),
      gestartetUm: Date.now(),
    });
    stubBridge(ergebnisMitNull());
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    vi.useFakeTimers();
    mount(<NodeCanvas graphId={graphId} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600);
    });

    const lauf = useVisRuntime.getState().laeufe[renderNodeId];
    expect(lauf?.status).toBe('fertig');
    expect(lauf?.bild).toBe('sSE.png');
    expect(lauf?.lieferstatus).toBeNull();
    expect(lauf?.lieferstatusGrund).toBe(GRUND);
    // Und die Kuratier-Quelle reicht beides weiter.
    expect(quelleAusLauf(lauf)).toMatchObject({ lieferstatus: null, lieferstatusGrund: GRUND });
  });

  it('lieferVorbehalt: null ist ein Vorbehalt; «geliefert» und fehlend bleiben still', () => {
    expect(lieferVorbehalt(null, GRUND)).toBe(`Lieferstatus nicht festgestellt: ${GRUND}`);
    expect(lieferVorbehalt(null, undefined)).toBe('Lieferstatus nicht festgestellt: ohne Grund');
    expect(lieferVorbehalt('geliefert', undefined)).toBeUndefined();
    expect(lieferVorbehalt(undefined, undefined)).toBeUndefined();
  });

  it('(d) Kachel: null steht als Vorbehalt da, nie als «geliefert»', () => {
    mount(<BildKachel jobId={JOB_ID} bild="sSE.png" qa={qaOk} lieferstatus={null} lieferstatusGrund={GRUND} alt="Bild 1" />);
    const zeile = container!.querySelector('[data-testid="vis-bild-kachel-liefer-vorbehalt"]');
    expect(zeile).not.toBeNull();
    expect(zeile!.textContent).toBe(`Lieferstatus nicht festgestellt: ${GRUND}`);
    expect(container!.textContent).not.toMatch(/\bgeliefert\b/);
  });

  it('(d) Kachel: «geliefert» oder fehlendes Feld zeigt keine Vorbehaltszeile', () => {
    mount(<BildKachel jobId={JOB_ID} bild="sSE.png" qa={qaOk} lieferstatus="geliefert" alt="Bild 1" />);
    expect(container!.querySelector('[data-testid="vis-bild-kachel-liefer-vorbehalt"]')).toBeNull();
    act(() => root!.unmount());
    container!.remove();
    mount(<BildKachel jobId={JOB_ID} bild="sSE.png" qa={qaOk} alt="Bild 1" />);
    expect(container!.querySelector('[data-testid="vis-bild-kachel-liefer-vorbehalt"]')).toBeNull();
  });

  it('(d) Inspektor: eigene Vorbehaltszeile «nicht festgestellt», ungekuerzt', () => {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = {
      node,
      quelle: { jobId: JOB_ID, bild: 'sSE.png', qa: qaOk, lieferstatus: null, lieferstatusGrund: GRUND },
      kur: { markiert: false, verworfen: false },
    };
    mount(
      <KuratierInspektor graph={graph} karte={karte} id="V-01" onMarkieren={() => {}} onVerwerfen={() => {}} onInsProjekt={() => {}} />,
    );
    expect(container!.textContent).toContain('Liefer-Vorbehalt');
    expect(container!.textContent).toContain(`Lieferstatus nicht festgestellt: ${GRUND}`);
  });

  it('(d) Inspektor: ohne null keine Vorbehaltszeile', () => {
    const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [node], edges: [] };
    const karte: KuratierKartenDaten = {
      node,
      quelle: { jobId: JOB_ID, bild: 'sSE.png', qa: qaOk, lieferstatus: 'geliefert' },
      kur: { markiert: false, verworfen: false },
    };
    mount(
      <KuratierInspektor graph={graph} karte={karte} id="V-01" onMarkieren={() => {}} onVerwerfen={() => {}} onInsProjekt={() => {}} />,
    );
    expect(container!.textContent).not.toContain('Liefer-Vorbehalt');
  });
});
