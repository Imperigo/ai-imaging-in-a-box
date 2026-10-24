// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';

/**
 * Die Ebene ueber der Leinwand (Owner-Fehler und stehende Regel 24.10.2026, Visbox 0.3.54:
 * «beim Zoomen verschwindet die Porttyp-Legende hinter den Nodes»). Gemessen: die Legende
 * (z 20) lag im selben Stapel wie das Render-Beiblatt (z 25), das mit dem Knoten wandert.
 *
 * Diese Probe haelt den BAU fest (jsdom zeichnet nicht; die Trefferprobe mit
 * `elementFromPoint` bei Zoom 0,25 bis max steht in `e2e/vis-ueber-leinwand.spec.ts`):
 *  - Legende, Kuratier-Knopf (und die Kuratier-Flaeche) liegen in `.vis-ueber-leinwand`,
 *    einem Geschwister der Knotenebene, nie in der verschobenen und gezoomten Welt;
 *  - die Ebene steht in der Dokumentreihenfolge NACH Knotenebene und Beiblatt;
 *  - im CSS bildet sie einen eigenen Stapel ueber dem Beiblatt und unter dem Insel-Chrome,
 *    und die Knotenebene traegt ihre eigene Stufe (`--k-ebene-grund`).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let container: HTMLDivElement | null = null;
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
});

function montiere(): void {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `Ueber-Leinwand-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'prompt', x: 40, y: 40 });
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 320, y: 120 });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

const CSS = readFileSync(path.resolve(__dirname, '../src/modules/vis/vis-visual.css'), 'utf8');
const QUELLE = readFileSync(path.resolve(__dirname, '../src/modules/vis/NodeCanvas.tsx'), 'utf8');

function block(selektor: string): string {
  const i = CSS.search(new RegExp(`(^|\\n)${selektor.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\{`));
  expect(i, `Regel ${selektor} fehlt`).toBeGreaterThanOrEqual(0);
  return CSS.slice(CSS.indexOf('{', i), CSS.indexOf('}', i) + 1);
}

describe('Ebene ueber der Leinwand · feste Flaechen nie hinter der Arbeitsflaeche', () => {
  it('Legende und Kuratier-Knopf liegen in der Ebene, nicht in der gezoomten Welt', () => {
    montiere();
    const ebene = container!.querySelector('[data-testid="vis-ueber-leinwand"]');
    expect(ebene).not.toBeNull();
    const welt = container!.querySelector('.vis-knoten-welt')!;
    for (const id of ['vis-island-legende', 'vis-kuratier-toggle']) {
      const el = container!.querySelector(`[data-testid="${id}"]`);
      expect(el, `${id} fehlt`).not.toBeNull();
      expect(ebene!.contains(el), `${id} liegt nicht in der Ebene ueber der Leinwand`).toBe(true);
      expect(welt.contains(el), `${id} liegt in der gezoomten Welt`).toBe(false);
    }
    // Geschwister der Knotenebene, und nach ihr im Dokument.
    const knotenEbene = container!.querySelector('[data-testid="vis-knoten-ebene"]')!;
    expect(ebene!.parentElement).toBe(knotenEbene.parentElement);
    expect(knotenEbene.compareDocumentPosition(ebene!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('das Beiblatt steht vor der Ebene und unter ihrer Stufe', () => {
    montiere();
    const knopf = container!.querySelector<HTMLButtonElement>('[data-testid="vis-node-render"] [data-testid="node-expand"]')!;
    act(() => knopf.click());
    const beiblatt = container!.querySelector<HTMLElement>('[data-testid="render-beiblatt"]');
    expect(beiblatt).not.toBeNull();
    const ebene = container!.querySelector('[data-testid="vis-ueber-leinwand"]')!;
    expect(ebene.contains(beiblatt)).toBe(false);
    expect(beiblatt!.compareDocumentPosition(ebene) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const beiblattZ = Number(beiblatt!.style.zIndex);
    const ebeneZ = Number(/z-index:\s*calc\(var\(--k-ebene-grund\)\s*\+\s*(\d+)\)/.exec(block('.vis-ueber-leinwand'))?.[1]);
    expect(beiblattZ).toBeGreaterThan(0);
    expect(ebeneZ, 'Stufe der Ebene nicht lesbar').toBeGreaterThan(beiblattZ);
    expect(ebeneZ, 'die Ebene muss unter dem Insel-Chrome (40) bleiben').toBeLessThan(40);
  });

  it('eigener Stapel fuer die Ebene, eigene Stufe fuer die Knotenebene', () => {
    const ueber = block('.vis-ueber-leinwand');
    expect(ueber).toMatch(/isolation:\s*isolate/);
    expect(ueber).toMatch(/pointer-events:\s*none/);
    expect(ueber).toMatch(/W0-EBENENTAFEL VIS_UEBER_LEINWAND/);
    expect(CSS).toMatch(/\.vis-ueber-leinwand > \*\s*\{\s*pointer-events:\s*auto;/);
    // Die erste `.vis-knoten-ebene`-Regel traegt die Stufe der Arbeitsflaeche.
    expect(block('.vis-knoten-ebene')).toMatch(/z-index:\s*var\(--k-ebene-grund\)/);
    // Keine feste Flaeche wandert mit: die Welt traegt nur Knoten.
    const welt = QUELLE.slice(QUELLE.indexOf('className="vis-knoten-welt"'), QUELLE.indexOf('{/* P16 · DIE BEIBLAETTER'));
    expect(welt).not.toMatch(/vis-island-legende|vis-chrome-topright|KuratierFlaeche/);
  });
});
