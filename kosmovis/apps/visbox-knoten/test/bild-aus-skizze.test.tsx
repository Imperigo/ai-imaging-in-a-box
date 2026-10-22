// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, setzeModellGlb, type VisGraph } from '@kosmo/kernel';
import { RenderScene } from '@kosmo/contracts';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { sendeGraphRenderAuftrag } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { registriereSkizzenQuelle, SKIZZE_IPAD_TYP } from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { BILD_AUS_SKIZZE_KNOPF, BILD_AUS_SKIZZE_SATZ } from '../../kosmo-orbit/src/modules/vis/grundlage';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import { huellboxAlsNetz, skizzenQuelleDerMappe } from '../src/mappe';

/**
 * FUND B des Mac-Demolaufs «Skizze vom iPad bis zum Bild» (Visbox 0.3.34, 22.10.2026): mit Skizze am
 * Render-Knoten war «Variante erzeugen» gesperrt («… dafür gibt es keine Grundlage»), und «Grundlage
 * rendern» rechnet ohne Skizze — kein Knopf schickte die Skizze. Nach Entscheid 96/98 ist die Skizze der
 * Eingang des KI-Bilds und braucht keine Grundlage. Jetzt heisst der zweite Knopf mit Skizze «Bild aus
 * Skizze erzeugen» und bestellt das Bild aus der Skizze (derselbe Auftrag wie `vis_render` mit Skizze).
 * Gegen den alten Stand rot (gesperrt; ueber `stufe: 'variante'` ging nichts hinaus).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
const SKIZZEN = [
  { name: 'skizze-20261015-081200.png', titel: 'Vordach', erzeugt: '2026-10-15T08:12:00', ueber: 'bild-1.png', stand: 'offen' },
  { name: 'skizze-20261014-091200.png', titel: 'Fassade Süd', erzeugt: '2026-10-14T09:12:00', ueber: null, stand: 'offen' },
];

/** Ein glb-Kopf mit leerem JSON-Block — genug für Glasnaht-Prüfung und Versand. */
function glb(): ArrayBuffer {
  const js = new TextEncoder().encode(JSON.stringify({ asset: { version: '2.0' } }).padEnd(28, ' '));
  const buf = new ArrayBuffer(12 + 8 + js.length);
  const dv = new DataView(buf);
  dv.setUint32(0, 0x46546c67, true);
  dv.setUint32(4, 2, true);
  dv.setUint32(8, buf.byteLength, true);
  dv.setUint32(12, js.length, true);
  dv.setUint32(16, 0x4e4f534a, true);
  new Uint8Array(buf, 20).set(js);
  return buf;
}

let gesendet: Record<string, unknown> | null = null;

beforeEach(() => {
  gesendet = null;
  history.replaceState(null, '', '/knoten/?ordner=Probemappe');
  localStorage.setItem('kosmo.bridge', `${location.origin}/bruecke`);
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  setzeModellGlb(glb());
  // Wie `ladeMappe`: die Hüllbox des Modells als Netz im Dokument — sonst sperrt «0 Bauteile».
  const { doc } = useProject.getState();
  const geschoss = { id: 'st-probe', kind: 'storey', name: 'Mappe', index: 0, elevation: 0, height: 3000, cutHeight: 1100 };
  const huelle = { id: 'fm-probe', kind: 'freemesh', storeyId: geschoss.id, name: 'Hüllbox', ...huellboxAlsNetz([[0, 0, 0], [8, 5, 3]]) };
  doc.apply([
    { id: geschoss.id, before: null, after: geschoss as never },
    { id: huelle.id, before: null, after: huelle as never },
  ]);
  vi.stubGlobal('fetch', async (url: string, init?: RequestInit) => {
    if (String(url).startsWith('./mappe')) return { ok: true, json: async () => ({ name: 'Probemappe', glb: true, skizzen: SKIZZEN }) };
    if (String(url).endsWith('/bruecke/jobs')) {
      gesendet = JSON.parse(String((init!.body as FormData).get('scene')));
      return {
        ok: true,
        json: async () => ({ job_id: 'vis-1790500000-5e1a00', status: 'awaiting_approval', scene: 's.json', created_at: '2026-10-15T08:00:00Z', idle_window_only: true }),
      };
    }
    return { ok: true, blob: async () => new Blob([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], { type: 'image/png' }) };
  });
});

let root: Root | null = null;
let halter: HTMLDivElement | null = null;

afterEach(() => {
  if (root) act(() => root!.unmount());
  halter?.remove();
  root = null;
  halter = null;
  registriereSkizzenQuelle(null);
  setzeModellGlb(null);
  vi.unstubAllGlobals();
});

function graph(mitSkizze: boolean): { graphId: string; renderId: string } {
  const { runCommand, doc } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: 'Skizze führt' }).patches[0] as { id: string }).id;
  const setze = (typ: string, params?: Record<string, string>) => {
    runCommand('vis.nodeSetzen', { graphId, typ, x: 0, y: 0, ...(params ? { params } : {}) });
    return doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  };
  const modell = setze('modell');
  const renderId = setze('render');
  runCommand('vis.verbinden', { graphId, from: modell, fromPort: 'szene', to: renderId, toPort: 'szene' });
  const p = setze('prompt', { text: 'ein Vordach aus Holz' });
  runCommand('vis.verbinden', { graphId, from: p, fromPort: 'prompt', to: renderId, toPort: 'prompt' });
  if (mitSkizze) {
    const s = setze(SKIZZE_IPAD_TYP);
    runCommand('vis.verbinden', { graphId, from: s, fromPort: 'bild', to: renderId, toPort: 'skizze' });
  }
  return { graphId, renderId };
}

describe('Fund B · mit Skizze: «Bild aus Skizze erzeugen»', () => {
  it('der Weg des zweiten Knopfs (stufe «variante») bestellt mit Skizze das Bild aus der Skizze — ohne Grundlage', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph(true);
    sendeGraphRenderAuftrag(graphId, renderId, undefined, { stufe: 'variante' });
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect(gesendet!['skizze']).toEqual({ quelle: 'mappe', name: 'skizze-20261015-081200.png' });
    const vis = (gesendet!['vis'] ?? {}) as Record<string, unknown>;
    expect(vis['grundlage']).toBeUndefined();
    expect(RenderScene.safeParse(gesendet).success).toBe(true);
    // Auch dieser Auftrag wartet am Knoten auf «Freigeben» (der Heim-PC legt jeden so an).
    await vi.waitFor(() => expect(useVisRuntime.getState().laeufe[renderId]?.status).toBe('wartetFreigabe'));
  });

  it('am Knoten: der Knopf heisst, was er tut, ist frei und traegt den Satz', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId, renderId } = graph(true);
    halter = document.createElement('div');
    document.body.appendChild(halter);
    root = createRoot(halter);
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    await act(async () => {
      for (let i = 0; i < 6; i += 1) await new Promise((r) => setTimeout(r, 0));
    });
    const knopf = halter.querySelector<HTMLButtonElement>('[data-testid="render-ausfuehren"]')!;
    expect(knopf.textContent).toBe(BILD_AUS_SKIZZE_KNOPF);
    expect(knopf.disabled).toBe(false);
    expect(knopf.getAttribute('title')).toBe(BILD_AUS_SKIZZE_SATZ);
    act(() => knopf.click());
    await vi.waitFor(() => expect(gesendet).not.toBeNull());
    expect(gesendet!['skizze']).toEqual({ quelle: 'mappe', name: 'skizze-20261015-081200.png' });
    await vi.waitFor(() => expect(useVisRuntime.getState().laeufe[renderId]?.status).toBe('wartetFreigabe'));
  });

  it('ohne Skizze bleibt es «Variante erzeugen», gesperrt bis eine Grundlage da ist', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { graphId } = graph(false);
    halter = document.createElement('div');
    document.body.appendChild(halter);
    root = createRoot(halter);
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    const knopf = halter.querySelector<HTMLButtonElement>('[data-testid="render-ausfuehren"]')!;
    expect(knopf.textContent).toBe('Variante erzeugen');
    expect(knopf.disabled).toBe(true);
  });
});
