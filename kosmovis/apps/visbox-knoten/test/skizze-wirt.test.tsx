// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { NodeCanvas } from '../../kosmo-orbit/src/modules/vis/NodeCanvas';
import {
  registriereSkizzenQuelle,
  SKIZZE_IPAD_TYP,
  SKIZZE_LEER_SATZ,
  skizzenStand,
} from '../../kosmo-orbit/src/modules/vis/skizze-quelle';
import { skizzenQuelleDerMappe } from '../src/mappe';

/**
 * VISBOX-EIGEN (Entscheide 95/95a, 14.10.2026, Blatt 25): Der Wirt meldet dem Knoten «Skizze vom
 * iPad» die Skizzen der Mappe an — Liste aus `GET ./mappe` (Feld `skizzen`, die neueste zuerst),
 * Bild aus `GET ./skizze?name=…`, beides für die Mappe dieser Seite (`?ordner=` bleibt erhalten).
 * Die Probe des Knotens selbst (`kv-skizze-vom-ipad.test.tsx`) kommt aus KosmoOrbit; diese prüft
 * die Anbindung an den Visbox-Server.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;

const SKIZZEN = [
  { name: 'skizze-20261014-091200.png', titel: 'Fassade Süd', erzeugt: '2026-10-14T09:12:00', ueber: null, stand: 'abgelegt' },
  { name: 'skizze-20261013-173000.png', titel: null, erzeugt: '2026-10-13T17:30:00', ueber: 'bild-1.png', stand: 'gerechnet' },
];

let container: HTMLDivElement | null = null;
let root: Root | null = null;
const abrufe: string[] = [];
let mappe: unknown = { name: 'Testmappe', glb: false, skizzen: SKIZZEN };

beforeEach(() => {
  abrufe.length = 0;
  mappe = { name: 'Testmappe', glb: false, skizzen: SKIZZEN };
  history.replaceState(null, '', '/knoten/');
  useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] });
  useVisRuntime.setState({ aktiverGraphId: null, aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {}, laeufe: {} });
  vi.stubGlobal('fetch', async (url: string) => {
    abrufe.push(String(url));
    if (String(url).startsWith('./mappe')) {
      return { ok: true, json: async () => mappe, text: async () => JSON.stringify(mappe) };
    }
    return { ok: true, blob: async () => new Blob([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], { type: 'image/png' }) };
  });
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereSkizzenQuelle(null);
  vi.unstubAllGlobals();
});

const q = (id: string): HTMLElement | null => document.body.querySelector(`[data-testid="${id}"]`);

async function warte(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 6; i += 1) await new Promise((r) => setTimeout(r, 0));
  });
}

describe('Visbox: Skizzen-Quelle der Mappe', () => {
  it('liest die Liste aus ./mappe und das Bild aus ./skizze — die Mappe der Seite bleibt dabei', async () => {
    history.replaceState(null, '', '/knoten/?ordner=testmappe');
    const quelle = skizzenQuelleDerMappe();
    expect(await quelle.liste()).toEqual(SKIZZEN);
    expect(abrufe).toEqual(['./mappe?ordner=testmappe']);
    expect(quelle.bildUrl('skizze-20261014-091200.png')).toBe('./skizze?ordner=testmappe&name=skizze-20261014-091200.png');
  });

  it('ohne ?ordner= gilt die zuletzt geöffnete Mappe; nur der Name geht mit', () => {
    expect(skizzenQuelleDerMappe().bildUrl('a b.png')).toBe('./skizze?name=a+b.png');
  });

  it('eine Mappe ohne Feld «skizzen» (älterer Server) ist eine leere Liste, kein Fehler', async () => {
    mappe = { name: 'alt', glb: false };
    expect(await skizzenQuelleDerMappe().liste()).toEqual([]);
  });

  it('antwortet der Server nicht, steht sein Satz als Fehler', async () => {
    vi.stubGlobal('fetch', async () => ({ ok: false, status: 404, text: async () => JSON.stringify({ fehler: 'Kein Projektordner.' }) }));
    await expect(skizzenQuelleDerMappe().liste()).rejects.toThrow('Kein Projektordner.');
  });

  it('am Knoten: die neueste mit Daumenbild vom Server; leere Mappe mit dem Satz zum iPad', async () => {
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    const { runCommand } = useProject.getState();
    const graphId = (runCommand('vis.graphErstellen', { name: 'Skizze' }).patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: SKIZZE_IPAD_TYP, x: 40, y: 40 });
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root!.render(<NodeCanvas graphId={graphId} />));
    await warte();
    expect(q('skizze-wahl')?.textContent).toMatch(/^neueste — Fassade Süd · 14\.10\. 09:12$/);
    expect(q('skizze-bild')?.getAttribute('src')).toBe('./skizze?name=skizze-20261014-091200.png');
    expect(skizzenStand().bilder['skizze-20261014-091200.png']).toMatch(/^data:image\/png;base64,/);

    mappe = { name: 'leer', glb: false, skizzen: [] };
    registriereSkizzenQuelle(skizzenQuelleDerMappe());
    await warte();
    expect(q('skizze-satz')?.textContent).toBe(SKIZZE_LEER_SATZ);
  });
});
