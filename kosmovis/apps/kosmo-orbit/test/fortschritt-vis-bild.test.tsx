// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { type VisGraph, type VisNode } from '@kosmo/kernel';

/**
 * Fortschritt am Ort in KosmoVis (Owner 06.10.2026): das Holen eines Ergebnisbilds (#2) und das Nachbearbeiten
 * über die Brücke (#3) haben keine Zahl — sie zeigen darum eine unbestimmte Leiste am Ort, mit Worten, was
 * läuft (Regel G6: ohne echte Zahl atmet sie). Vorher stand «lädt …» bzw. waren nur die Knöpfe gesperrt.
 */
vi.mock('../src/modules/vis/vis-jobs', async (orig) => ({
  ...(await orig<typeof import('../src/modules/vis/vis-jobs')>()),
  // Ein Bild, das nie ankommt: der Wartezustand bleibt stehen und kann gemessen werden.
  bildBlob: () => new Promise<Blob>(() => {}),
}));

const { BridgeBild } = await import('../src/modules/vis/BridgeBild');
const { KuratierInspektor } = await import('../src/modules/vis/KuratierInspektor');
const { useVisRuntime } = await import('../src/modules/vis/vis-runtime');

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function zeichne(el: React.ReactElement): HTMLDivElement {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
  return container;
}

beforeEach(() => {
  useVisRuntime.setState({ gerechneteBilder: {}, gehobeneBilder: {} });
});

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  container?.remove();
  container = null;
});

describe('BridgeBild — Bild holen wartet am Ort', () => {
  it('zeigt eine unbestimmte Leiste mit Worten statt «lädt …»', () => {
    const c = zeichne(<BridgeBild jobId="vis-1-abcdef" imageName="cam-01.png" alt="Render" testid="render-bild" />);
    const ort = c.querySelector('[data-testid="render-bild-laedt"]');
    expect(ort).not.toBeNull();
    const warten = ort!.querySelector('.k-warten')!;
    expect(warten.getAttribute('data-form')).toBe('leiste');
    expect(warten.getAttribute('data-art')).toBe('unbestimmt');
    expect(warten.textContent).toBe('Bild wird geholt');
  });
});

describe('KuratierInspektor — Nachbearbeiten zeigt, was läuft', () => {
  const NODE: VisNode = { id: 'node-fs', typ: 'render', x: 0, y: 0, params: {} } as VisNode;
  const GRAPH = { id: 'g1', typ: 'VisGraph', name: 'P', nodes: [NODE], edges: [] } as unknown as VisGraph;

  it('nach dem Klick auf «Heller» steht eine unbestimmte Leiste mit dem Vorgang in Worten', () => {
    const c = zeichne(
      <KuratierInspektor
        graph={GRAPH}
        karte={{ node: NODE, quelle: { dataUrl: 'data:image/png;base64,iVBORw0KGgo=' }, kur: { markiert: false, verworfen: false } }}
        id="pruef"
        onMarkieren={() => {}}
        onVerwerfen={() => {}}
        onInsProjekt={() => {}}
      />,
    );
    expect(c.querySelector('[data-testid="vis-kuratier-warteort"]')).toBeNull();
    act(() => {
      c.querySelector('[data-testid="vis-kuratier-belichten"]')!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    const warten = c.querySelector('[data-testid="vis-kuratier-warteort"] .k-warten')!;
    expect(warten).not.toBeNull();
    expect(warten.getAttribute('data-form')).toBe('leiste');
    expect(warten.getAttribute('data-art')).toBe('unbestimmt');
    expect(warten.textContent).toContain('heller');
  });
});
