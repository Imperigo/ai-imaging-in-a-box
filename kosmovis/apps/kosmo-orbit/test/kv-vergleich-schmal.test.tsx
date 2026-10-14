// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { KuratierFlaeche } from '../src/modules/vis/KuratierFlaeche';
import type { KuratierKartenDaten } from '../src/modules/vis/varianten-diff';

/**
 * Nachgang 3, Punkt 4 — der Vergleich der Kuratier-Flaeche bei schmaler
 * Mitte (Befund des lokalen Workers, auf-20261007-250, 1b: bei 1024 x 768
 * brach «Lizenz offen» dreizeilig, «V-01» zweizeilig, Karte B und die Spalte
 * «Variante B» liefen unter den Inspektor). Die Lage misst
 * `e2e/kv-vergleich-schmal.spec.ts`; jsdom rechnet keine Lage. Hier steht,
 * was sie traegt: die Spalte B hat eine eigene Klasse (sonst kann die schmale
 * Fassung sie nicht unter ihren Wert stellen), und `vis-visual.css` hat den
 * Groessen-Behaelter, die schmale Fassung und die umbrechenden Wertspalten.
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const HIER = path.dirname(fileURLToPath(import.meta.url));
const CSS = readFileSync(path.resolve(HIER, '../src/modules/vis/vis-visual.css'), 'utf8');

/** Der Rumpf der ersten Regel, deren Selektor genau `selektor` ist, ab `ab`. */
function regel(selektor: string, ab = 0): string {
  const i = CSS.indexOf(`${selektor} {`, ab);
  expect(i, `Regel «${selektor}» fehlt in vis-visual.css`).toBeGreaterThanOrEqual(0);
  return CSS.slice(i, CSS.indexOf('}', i));
}

function karte(id: string): KuratierKartenDaten {
  const node: VisNode = { id, typ: 'render', x: 0, y: 0, params: {} };
  return {
    node,
    quelle: {
      jobId: `job-${id}`,
      bild: 'render.png',
      lizenzOffen: true,
      engineUsed: 'qwen-image-2.1',
      engineLicense: 'Qwen Research License Agreement',
    },
    kur: { markiert: false, verworfen: false },
  };
}

describe('kv-vergleich-schmal · Vergleich bei schmaler Mitte', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;
  beforeEach(() => {
    // Das Bild holt `BridgeBild` von der Bruecke; hier gibt es keine.
    vi.stubGlobal('fetch', (async () => ({ ok: false, status: 404, json: async () => ({}) }) as Response) as unknown as typeof fetch);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    if (root) act(() => root!.unmount());
    container?.remove();
    root = null;
    container = null;
  });

  it('jede Zelle der Spalte «Variante B» traegt `vis-vergleich-zeile-wert--b`, jede der Spalte A `--a`', () => {
    const a = karte('n1');
    const b = karte('n2');
    const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'Test', nodes: [a.node, b.node], edges: [] };
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() =>
      root!.render(
        <KuratierFlaeche
          graph={graph}
          karten={[a, b]}
          vergleichAuswahl={['n1', 'n2']}
          onMarkieren={() => {}}
          onVerwerfen={() => {}}
          onVergleichWahl={() => {}}
        />,
      ),
    );
    const flaeche = container.querySelector('[data-testid="vis-kuratier-vergleich-flaeche"]')!;
    expect(flaeche).not.toBeNull();
    const zeilen = Array.from(flaeche.querySelectorAll('.vis-vergleich-zeile'));
    expect(zeilen.length).toBeGreaterThan(5);
    for (const z of zeilen) {
      const kinder = Array.from(z.children);
      expect(kinder).toHaveLength(3);
      expect(kinder[0]!.classList.contains('vis-vergleich-zeile-wert--a'), z.textContent ?? '').toBe(true);
      expect(kinder[1]!.classList.contains('vis-vergleich-zeile-label'), z.textContent ?? '').toBe(true);
      expect(kinder[2]!.classList.contains('vis-vergleich-zeile-wert--b'), z.textContent ?? '').toBe(true);
    }
    // Beide Karten tragen das Abzeichen; der volle Grund bleibt in der Kurzhilfe.
    expect(flaeche.querySelectorAll('[data-testid^="vis-kuratier-vergleich-lizenz-offen-"]')).toHaveLength(2);
  });

  it('vis-visual.css: Groessen-Behaelter, Karten untereinander unter 480 px, Wertspalten brechen um, Kennung einzeilig', () => {
    expect(regel('.vis-vergleich-flaeche')).toMatch(/container:\s*vis-vergleich\s*\/\s*inline-size/);
    expect(regel('.vis-vergleich-paar')).toMatch(/grid-template-columns:\s*minmax\(0, 1fr\) minmax\(0, 1fr\)/);
    expect(regel('.vis-vergleich-zeile')).toMatch(/grid-template-columns:\s*minmax\(0, 1fr\) auto minmax\(0, 1fr\)/);
    expect(regel('.vis-vergleich-tabelle-kopf')).toMatch(/grid-template-columns:\s*minmax\(0, 1fr\) auto minmax\(0, 1fr\)/);
    const wert = regel('.vis-vergleich-zeile-wert');
    expect(wert).toMatch(/min-width:\s*0/);
    expect(wert).toMatch(/overflow-wrap:\s*anywhere/);
    const id = regel('.vis-vergleich-karte-id');
    expect(id).toMatch(/white-space:\s*nowrap/);
    expect(id).toMatch(/flex:\s*none/);

    const schmal = CSS.indexOf('@container vis-vergleich (max-width: 479px) {');
    expect(schmal, 'schmale Fassung fehlt').toBeGreaterThanOrEqual(0);
    expect(regel('.vis-vergleich-paar', schmal)).toMatch(/grid-template-columns:\s*minmax\(0, 1fr\);/);
    expect(CSS.slice(schmal)).toMatch(/\.vis-vergleich-zeile-wert--b \{\s*grid-area: b;/);
    expect(CSS.slice(schmal)).toMatch(/\.vis-vergleich-zeile-label \{\s*grid-area: label;/);
  });
});
