// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type VisGraph } from '@kosmo/kernel';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { BildPaarGross } from '../src/modules/vis/BildPaar';
import { modusDerZelle } from '../src/modules/vis/varianten';
import { modusMarkeArt } from '../src/modules/vis/modus-marke';
import type { VerlaufEintrag } from '../src/modules/vis/render-verlauf';
import { memoKey, useVisRuntime, type NodeLauf } from '../src/modules/vis/vis-runtime';
import { useProject } from '../src/state/project-store';

/**
 * Modus-Marke «Ohne Grundlagenbild» / «Anders gerechnet» an jedem Bild, an dem auch «Vorschau» steht:
 * Hauptbild des Render-Knotens (mit Zusatzzeile), Grossansicht einzeln und nebeneinander, Bildpaar gross,
 * Varianten-Zelle (Angabe der eigenen Kamera). Gelesen wird nur `NodeLauf.modus`.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('createObjectURL' in URL)) Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });

const SATZ = "KI-BILD OHNE GRUNDLAGENBILD, Kamera 'sSE': bestellt 'image_edit', gerechnet 'txt2img'";
const OHNE = { bestellt: 'image_edit', gerechnet: 'txt2img', abweichung: true, satz: SATZ } as const;
const MEHRERE = {
  bestellt: 'image_edit',
  gerechnet: null,
  abweichung: true,
  kameras: { sSE: { gerechnet: 'txt2img', abweichung: true }, nNW: { gerechnet: 'image_edit', abweichung: false } },
} as const;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let graphId = '';
let nodeId = '';
let schluessel = '';

function eintrag(nr: number, extra: Partial<NodeLauf> = {}): VerlaufEintrag {
  return {
    status: 'fertig',
    jobId: `job-${nr}`,
    bild: `bild-${nr}.png`,
    qa: { verdict: { passed: true } },
    memoKey: schluessel,
    gestartetUm: Date.UTC(2026, 9, 21, 12, nr),
    fertigUm: Date.UTC(2026, 9, 21, 12, nr + 1),
    ...extra,
  } as VerlaufEintrag;
}
function laeufe(...l: NodeLauf[]): void {
  for (const lauf of l) act(() => useVisRuntime.getState().setzeLauf(nodeId, lauf));
}
function montiere(el?: React.ReactElement): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el ?? <NodeCanvas graphId={graphId} />));
}
const q = <T extends Element = HTMLElement>(sel: string, im: ParentNode = document): T | null => im.querySelector<T>(sel);
const qa = (sel: string, im: ParentNode = document): HTMLElement[] => [...im.querySelectorAll<HTMLElement>(sel)];
function klick(el: Element): void {
  act(() => {
    el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
}

beforeEach(() => {
  vi.stubGlobal('fetch', (async (url: unknown) =>
    String(url).includes('/artifacts/')
      ? ({ ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) } as Response)
      : ({ ok: false, status: 404, json: async () => ({}) } as Response)) as unknown as typeof fetch);
  useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {}, kuration: {} });
  const { runCommand, doc } = useProject.getState();
  graphId = (runCommand('vis.graphErstellen', { name: `Modus-${Math.random()}` }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 40, y: 20, params: { verlaufOffen: true } });
  const graph = doc.get<VisGraph>(graphId)!;
  nodeId = graph.nodes.at(-1)!.id;
  schluessel = memoKey(evaluiereGraph(doc, graph).renderAuftraege.get(nodeId)!);
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});

describe('Hauptbild des Render-Knotens', () => {
  it('Vorschau und Modus-Marke stehen in einer Leiste im Bild; die Zusatzzeile folgt unter dem Bild', () => {
    laeufe(eintrag(1, { guete: 'vorschau', modus: MEHRERE }));
    montiere();
    const leiste = q('[data-testid="render-hauptbild"] .vis-marken-leiste', container!)!;
    expect([...leiste.querySelectorAll('[data-testid]')].map((e) => e.getAttribute('data-testid'))).toEqual(['render-guete-marke', 'render-modus-marke']);
    expect(q('[data-testid="render-modus-marke"]', leiste)!.getAttribute('data-modus')).toBe('anders-gerechnet');
    expect(q('[data-testid="render-modus-zusatzzeile"]', container!)!.textContent).toBe('1 von 2 Kameras ohne Grundlagenbild gerechnet (sSE)');
  });
  it('ohne Abweichung weder Marke noch Zusatzzeile', () => {
    laeufe(eintrag(1, { modus: { bestellt: 'image_edit', gerechnet: 'image_edit', abweichung: false } }));
    montiere();
    expect(q('[data-testid="render-modus-marke"]', container!)).toBeNull();
    expect(q('[data-testid="render-modus-zusatzzeile"]', container!)).toBeNull();
  });
});

describe('Grossansicht', () => {
  it('einzeln: Marke neben «Vorschau», Alternativtext und Knopfname nennen den Rechenweg', async () => {
    laeufe(eintrag(1, { guete: 'vorschau', modus: OHNE }), eintrag(2));
    montiere();
    const daumen = qa('[data-testid="render-verlauf-bild"]', container!);
    expect(daumen.map((d) => d.getAttribute('aria-label') ?? '').filter((a) => a.includes(', ohne Grundlagenbild, gross anzeigen')).length).toBe(1);
    klick(daumen.find((d) => d.dataset['job'] === 'job-1')!);
    await act(async () => {
      for (let i = 0; i < 6; i++) await Promise.resolve();
    });
    const leiste = q('[data-testid="render-verlauf-gross"] .vis-marken-leiste')!;
    expect(q('[data-testid="render-verlauf-gross-guete-marke"]', leiste)).not.toBeNull();
    expect(q('[data-testid="render-verlauf-gross-modus-marke"]', leiste)!.textContent).toBe('Ohne Grundlagenbild');
    expect(q('[data-testid="render-verlauf-gross-bild"]')!.getAttribute('alt')).toContain(', ohne Grundlagenbild');
  });
  it('nebeneinander: die Marke steht nur an der abweichenden Zelle', () => {
    laeufe(eintrag(1, { grundlageId: 'gl', stufe: 'variante', modus: OHNE }), eintrag(2, { grundlageId: 'gl', stufe: 'variante' }));
    montiere();
    klick(qa('[data-testid="render-verlauf-bild"]', container!)[0]!);
    klick(q('[data-testid="render-verlauf-gross-nebeneinander"]')!);
    const zellen = qa('[data-testid="render-verlauf-gross-reihe-zelle"]');
    expect(zellen.length).toBe(2);
    const mit = zellen.filter((z) => q('[data-testid="render-verlauf-gross-reihe-modus"]', z));
    expect(mit.map((z) => z.dataset['job'])).toEqual(['job-1']);
  });
});

describe('Bildpaar gross', () => {
  it('die Marke steht am KI-Bild, nicht am Grundbild', () => {
    montiere(
      <BildPaarGross lauf={{ modus: OHNE }} jobId="job-1" ki="ki.png" grundbild="grund.png" ansicht="beide" onAnsicht={() => {}} onClose={() => {}} />,
    );
    const ki = q('[data-testid="render-bildpaar-ki"]')!;
    expect(q('[data-testid="render-bildpaar-modus-marke"]', ki)!.textContent).toBe('Ohne Grundlagenbild');
    expect(q('[data-testid="render-bildpaar-grundbild"] [data-testid="render-bildpaar-modus-marke"]')).toBeNull();
  });
});

describe('Varianten-Zelle', () => {
  it('traegt die Angabe ihrer Kamera (Name oder Kuerzel); die des Laufs nur ohne Verzeichnis je Kamera', () => {
    const lauf = { modus: MEHRERE } as unknown as NodeLauf;
    const heim = [{ name: 'Suedost', kuerzel: 'sSE' }, { name: 'Nordwest', kuerzel: 'nNW' }];
    expect(modusMarkeArt(modusDerZelle(lauf, 'Suedost', heim).modus)).toBe('ohne-grundlagenbild');
    expect(modusMarkeArt(modusDerZelle(lauf, 'Nordwest', heim).modus)).toBeNull();
    expect(modusMarkeArt(modusDerZelle(lauf, 'sSE', undefined).modus)).toBe('ohne-grundlagenbild');
    // Kamera fehlt im vorhandenen Verzeichnis: keine Marke, nicht die des ganzen Laufs.
    expect(modusDerZelle(lauf, 'Unbekannt', heim)).toEqual({});
    const ohneVerzeichnis = { modus: { bestellt: 'image_edit', gerechnet: 'txt2img', abweichung: true } } as unknown as NodeLauf;
    expect(modusMarkeArt(modusDerZelle(ohneVerzeichnis, 'Unbekannt', heim).modus)).toBe('ohne-grundlagenbild');
    expect(modusDerZelle({} as NodeLauf, 'x', heim)).toEqual({});
  });
});
