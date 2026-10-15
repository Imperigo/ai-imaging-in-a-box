// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { type VisGraph } from '@kosmo/kernel';
import {
  basisNodeHoehe,
  NodeCanvas,
  RENDER_ZEILE_SKIZZE,
  RENDER_ZEILEN,
  sichtbareEingaenge,
  ZEILEN_ABSTAND,
  zeilenHoehe,
} from '../src/modules/vis/NodeCanvas';
import {
  registriereSkizzenQuelle,
  SKIZZE_IPAD_TYP,
  SKIZZE_OHNE_BEMERKUNG_SATZ,
  type Skizze,
  type SkizzenQuelle,
} from '../src/modules/vis/skizze-quelle';
import {
  SKIZZE_KAMERAS_SATZ,
  SKIZZE_KEINE_ZEILE,
  SKIZZE_OHNE_KI_ZEILE,
  SKIZZE_STANDPUNKT_BILD,
  SKIZZE_STANDPUNKT_OHNE_BILD,
  SKIZZE_STANDPUNKT_UNBEKANNT,
} from '../src/modules/vis/skizze-fuehrt';
import { useProject } from '../src/state/project-store';

/**
 * KV-SKIZZE-FUEHRT · der Knoten (Owner-Entscheid 96 der Visbox, 15.10.2026). Der Eingang «Skizze»
 * und die Zeile «Skizze» stehen NUR mit Wirt (Visbox); ohne Wirt (KosmoOrbit) ist der Render-Knoten
 * Pixel fuer Pixel so hoch wie vorher. Mit Wirt sagt die Zeile, welches Modell rechnet und ob die
 * Skizze darauf ankommt, und (96b) von welchem Standpunkt das Bild entsteht; die Anweisung ist
 * (96a) die Bemerkung der Skizze, die Stimmung tritt zurueck — ohne Bemerkung steht das vorher da.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const SKIZZEN: Skizze[] = [
  { name: 'skizze-20261015-0812.png', titel: 'Balkon', erzeugt: '2026-10-15T08:12:00', ueber: null, stand: 'abgelegt', bemerkung: 'Balkon aus Holz', standpunkt: 'mappe' },
];
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function wirt(liste: Skizze[] = SKIZZEN): SkizzenQuelle {
  return { liste: async () => liste, bildUrl: (n: string) => `./skizze?name=${encodeURIComponent(n)}` };
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;

beforeEach(() => {
  vi.stubGlobal('fetch', async () => ({ ok: true, blob: async () => new Blob([PNG], { type: 'image/png' }) }));
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereSkizzenQuelle(null);
  vi.unstubAllGlobals();
});

function montiere(
  opts: { skizze?: boolean; params?: Record<string, string | boolean>; kameras?: boolean; prompt?: string } = {},
): {
  graphId: string;
  renderId: string;
} {
  const { runCommand, doc } = useProject.getState();
  const graphId = (runCommand('vis.graphErstellen', { name: `KV-SKIZZE-KNOTEN-${Math.random()}` }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 320, y: 40, ...(opts.params ? { params: opts.params } : {}) });
  const renderId = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
  if (opts.skizze) {
    runCommand('vis.nodeSetzen', { graphId, typ: SKIZZE_IPAD_TYP, x: 40, y: 40 });
    const s = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    runCommand('vis.verbinden', { graphId, from: s, fromPort: 'bild', to: renderId, toPort: 'skizze' });
  }
  if (opts.prompt !== undefined) {
    runCommand('vis.nodeSetzen', { graphId, typ: 'prompt', x: 40, y: 500, params: { text: opts.prompt } });
    const p = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    runCommand('vis.verbinden', { graphId, from: p, fromPort: 'prompt', to: renderId, toPort: 'prompt' });
  }
  if (opts.kameras) {
    runCommand('vis.nodeSetzen', { graphId, typ: 'kamera', x: 40, y: 300 });
    const k = doc.get<VisGraph>(graphId)!.nodes.at(-1)!.id;
    runCommand('vis.verbinden', { graphId, from: k, fromPort: 'kameras', to: renderId, toPort: 'kameras' });
  }
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
  return { graphId, renderId };
}

const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);

async function warte(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 6; i += 1) await new Promise((r) => setTimeout(r, 0));
  });
}

describe('KV-SKIZZE-FUEHRT · ohne Wirt (KosmoOrbit)', () => {
  it('kein Eingang «Skizze», keine Zeile «Skizze», und der Knoten so hoch wie vor Entscheid 96', () => {
    expect(sichtbareEingaenge('render').map((p) => p.name)).toEqual(['szene', 'prompt', 'treue', 'samples', 'kameras']);
    // 26 Kopf + 8 + 5 Anschluesse à 20 + Koerper + 10 — die Rechnung von vorher, ausgeschrieben.
    expect(basisNodeHoehe('render')).toBe(26 + 8 + 5 * 20 + zeilenHoehe(RENDER_ZEILEN) + 10);
    montiere();
    expect(q('port-in-skizze')).toBeNull();
    expect(q('render-skizze')).toBeNull();
    expect(container!.querySelector('[data-zeile="skizze"]')).toBeNull();
  });

  it('eine Skizzen-Kante aus einem Visbox-Graphen wird nicht gezeichnet (sie landete sonst am ersten Anschluss)', () => {
    montiere({ skizze: true });
    expect(q('port-in-skizze')).toBeNull();
    // Keine Kante zum verborgenen Eingang: im Kantenlayer steht keine.
    expect(container!.querySelectorAll('[data-testid="vis-edge"]').length).toBe(0);
  });
});

describe('KV-SKIZZE-FUEHRT · mit Wirt (Visbox)', () => {
  it('der Eingang «Skizze» steht als letzter; der Knoten waechst um einen Anschluss und die Zeile', async () => {
    registriereSkizzenQuelle(wirt());
    expect(sichtbareEingaenge('render').map((p) => p.name).at(-1)).toBe('skizze');
    expect(basisNodeHoehe('render')).toBe(
      26 + 8 + 6 * 20 + zeilenHoehe(RENDER_ZEILEN) + RENDER_ZEILE_SKIZZE.h + ZEILEN_ABSTAND + 10,
    );
    montiere();
    await warte();
    expect(q('port-in-skizze')).not.toBeNull();
    expect(q('render-skizze')?.textContent).toBe(SKIZZE_KEINE_ZEILE);
  });

  it('mit Wirt wird die Skizzen-Kante gezeichnet (Gegenprobe zum verborgenen Eingang)', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true });
    await warte();
    expect(container!.querySelectorAll('[data-testid="vis-edge"]').length).toBe(1);
  });

  it('Skizze am Eingang, Vorgabemodell: «kommt gemessen nicht an», Warnfarbe, voller Satz am title', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true });
    await warte();
    const zeile = q('render-skizze') as HTMLElement;
    expect(zeile.textContent).toBe(`Skizze führt · Z-Image Turbo: darauf kommt sie gemessen nicht an. ${SKIZZE_STANDPUNKT_OHNE_BILD}`);
    expect(zeile.dataset['warnung']).toBe('true');
    const title = (q('render-skizze') as HTMLElement).dataset['satz']!;
    expect(title).toContain('«Balkon · 15.10. 08:12» führt das Bild');
    expect(title).toContain('auf-20260919-123');
    expect(title).toContain('SKIZZE NICHT ANGEKOMMEN');
  });

  it('Skizze am Eingang, Qwen-Image 2.1: «ungemessen», ohne Warnfarbe — das Modell wird nie von selbst umgestellt', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true, params: { backbone: 'qwen-image-2.1' } });
    await warte();
    const zeile = q('render-skizze') as HTMLElement;
    expect(zeile.textContent).toBe(`Skizze führt · Qwen-Image 2.1: ob sie ankommt, ist ungemessen. ${SKIZZE_STANDPUNKT_OHNE_BILD}`);
    expect(zeile.dataset['warnung']).toBe('false');
  });

  it('Skizze und «nur Cycles»: die Zeile sagt, dass das nicht geht', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true, params: { nurCycles: true } });
    await warte();
    expect(q('render-skizze')?.textContent).toBe(SKIZZE_OHNE_KI_ZEILE);
  });

  it('Skizze und Kamera-Standpunkte: der Satz sagt, dass sie nicht gelten', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true, kameras: true });
    await warte();
    expect((q('render-skizze') as HTMLElement).dataset['satz']).toContain(SKIZZE_KAMERAS_SATZ);
  });

  it('96a: mit Skizze ist die Anweisung die Bemerkung der Skizze; ohne Prompt kein Mangel', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true });
    await warte();
    const prompt = q('render-final-prompt') as HTMLElement;
    expect(prompt.textContent).toBe('Anweisung: Bemerkung der Skizze «Balkon aus Holz»');
    expect(prompt.className).not.toContain('warnung');
  });

  it('96a: mit Skizze und Stimmung tritt die Stimmung zurueck — und das steht da', async () => {
    registriereSkizzenQuelle(wirt());
    montiere({ skizze: true, prompt: 'Abendstimmung' });
    await warte();
    const prompt = q('render-final-prompt') as HTMLElement;
    expect(prompt.textContent).toBe('Anweisung: Bemerkung der Skizze «Balkon aus Holz» — Stimmung tritt zurück');
    expect(prompt.getAttribute('title')).toContain('«Abendstimmung» tritt zurück und wird nicht gesendet');
  });

  it('96c: Skizze ohne Bemerkung, aber mit Prompt — der Prompt gilt als Anweisung, keine Warnung', async () => {
    registriereSkizzenQuelle(wirt([{ ...SKIZZEN[0]!, bemerkung: '' }]));
    montiere({ skizze: true, prompt: 'Abendstimmung' });
    await warte();
    const zeile = q('render-skizze') as HTMLElement;
    // (Die Zeile kann aus einem anderen Grund warnen: Auf Z-Image kommt die Skizze nicht an.)
    expect(zeile.textContent).not.toBe(SKIZZE_OHNE_BEMERKUNG_SATZ);
    const prompt = q('render-final-prompt') as HTMLElement;
    expect(prompt.textContent).toContain('Anweisung: Prompt «Abendstimmung»');
    expect(prompt.textContent).toContain('keine Bemerkung');
    expect(prompt.className).not.toContain('warnung');
  });

  it('96a/96c: Skizze ohne Bemerkung UND ohne Prompt — Warnung VOR dem Klick', async () => {
    registriereSkizzenQuelle(wirt([{ ...SKIZZEN[0]!, bemerkung: '' }]));
    montiere({ skizze: true, prompt: '' });
    await warte();
    const zeile = q('render-skizze') as HTMLElement;
    expect(zeile.textContent).toBe(SKIZZE_OHNE_BEMERKUNG_SATZ);
    expect(zeile.dataset['warnung']).toBe('true');
  });

  it('96b: auf ein Bild gezeichnet und dessen Standpunkt bekannt — «Standpunkt: vom Bild unter der Skizze»', async () => {
    registriereSkizzenQuelle(wirt([{ ...SKIZZEN[0]!, ueber: 'bilder/bild-1.png', standpunkt: 'bild' }]));
    montiere({ skizze: true });
    await warte();
    const zeile = q('render-skizze') as HTMLElement;
    expect(zeile.textContent).toContain(SKIZZE_STANDPUNKT_BILD);
    expect(zeile.textContent).not.toContain('Standpunkt der Mappe');
    expect(zeile.dataset['satz']).toContain(SKIZZE_STANDPUNKT_BILD);
  });

  it('96b: auf ein Bild gezeichnet, dessen Standpunkt NICHT bekannt ist — Standpunkt der Mappe, mit Grund', async () => {
    registriereSkizzenQuelle(wirt([{ ...SKIZZEN[0]!, ueber: 'bilder/alt.png', standpunkt: 'mappe' }]));
    montiere({ skizze: true });
    await warte();
    expect(q('render-skizze')?.textContent).toContain(SKIZZE_STANDPUNKT_UNBEKANNT);
  });
});
