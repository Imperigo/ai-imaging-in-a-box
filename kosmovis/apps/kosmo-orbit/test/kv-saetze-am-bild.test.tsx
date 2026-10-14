// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { VisGraph, VisNode } from '@kosmo/kernel';
import { BildKachel } from '../src/modules/vis/NodeCanvas';
import { KuratierInspektor } from '../src/modules/vis/KuratierInspektor';
import type { KuratierKartenDaten } from '../src/modules/vis/varianten-diff';
import type { JobQa } from '../src/modules/vis/vis-jobs';

/**
 * Blatt 16 «Sätze am Bild», Teil A.
 *
 * Entscheid 72 (KosmoOrbit E198): der Grund-Satz an der Bild-Kachel brach
 * nach einer halben Zeile ab (feste Knotenhoehe). Jetzt genau EINE Zeile mit
 * «…», der volle Satz woertlich in der Kurzhilfe — beim Darueberfahren und
 * bei Tastaturfokus. Ohne Satz keine Zeile; vollstaendig weiter im Inspektor.
 *
 * HomeStation 268: beim echten Durchfallen (passed:false, ohne Maskenfelder —
 * Lage `widerrufen`) zeigte der Inspektor «QA-Verdikt: verfehlt» und darunter
 * «Bewertung zurueckgezogen …» — eine Gegenaussage zum gefaellten Urteil.
 * `widerrufen` betrifft nur Sterne und Zahlen; dort steht jetzt ein knapper
 * Hinweis dazu, keiner zum Urteil.
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

const LANG =
  "NICHT BEURTEILBAR (Gebaeudeanteil): Das Haus fuellt nur 17.9% des Bildes, weniger als 20 %; der Gesamtwert ist hier nicht anwendbar. 'passed: false' heisst hier nicht durchgefallen, sondern nicht beurteilbar.";

/** So liefert der echte Abholer: keine Maskenfelder. */
function echt(passed: boolean, reason?: string): JobQa {
  return {
    verdict: { passed, ...(reason !== undefined ? { reason } : {}) },
    geometry: { geometry_fidelity: passed ? 0.81 : 0.598, geom_iou: 0.77, threshold: 0.65, passed, method: 'depthanything-v2-redepth' },
    style: { style_score: 0.6, threshold: 0.3, passed: true, method: 'clip' },
  };
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;
beforeEach(() => {
  vi.stubGlobal('fetch', (async () =>
    ({ ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) }) as Response) as unknown as typeof fetch);
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});
function mount(el: React.ReactElement): HTMLDivElement {
  if (root) act(() => root!.unmount());
  container?.remove();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
  return container;
}
const grundZeile = (c: ParentNode): HTMLElement | null => c.querySelector<HTMLElement>('[data-testid="vis-bild-kachel-qa-vorbehalt"]');

describe('Entscheid 72 — der Grund an der Kachel: eine Zeile, der volle Satz in der Kurzhilfe', () => {
  it('langer Satz: eine Zeile mit «…», fokussierbar, die Kurzhilfe traegt den Satz woertlich, kein natives title', () => {
    const c = mount(<BildKachel jobId="j" bild="b.png" qa={echt(false, LANG)} alt="Bild" />);
    const z = grundZeile(c)!;
    expect(z.classList.contains('vis-bild-kachel-grund-zeile'), 'einzeilige Klasse').toBe(true);
    expect(z.textContent).toBe(LANG);
    expect(z.getAttribute('tabindex'), 'mit der Tastatur erreichbar').toBe('0');
    expect(z.getAttribute('title')).toBeNull();
    const id = z.getAttribute('aria-describedby');
    expect(id, 'Kurzhilfe verbunden').toBeTruthy();
    expect(document.getElementById(id!)!.textContent).toBe(LANG);
  });

  it('die Stilvorlage macht die Zeile einzeilig mit «…»', () => {
    const css = readFileSync(
      path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis/vis-visual.css'),
      'utf8',
    );
    const block = /\n\.vis-bild-kachel-grund-zeile \{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(block).toContain('white-space: nowrap;');
    expect(block).toContain('overflow: hidden;');
    expect(block).toContain('text-overflow: ellipsis;');
  });

  it('ohne Satz keine Zeile; ein kurzer Satz steht ganz da', () => {
    const c = mount(<BildKachel jobId="j" bild="b.png" qa={echt(true)} alt="Bild" />);
    expect(grundZeile(c)).toBeNull();
    const c2 = mount(<BildKachel jobId="j" bild="b.png" qa={echt(false, 'Geometrie 0.598 gegen 0.65')} alt="Bild" />);
    expect(grundZeile(c2)!.textContent).toBe('Geometrie 0.598 gegen 0.65');
  });
});

describe('HomeStation 268 — Inspektor: kein «zurückgezogen» gegen ein gefälltes Urteil', () => {
  const node: VisNode = { id: 'n1', typ: 'render', x: 0, y: 0, params: {} };
  const graph: VisGraph = { id: 'g1', kind: 'visgraph', name: 'T', nodes: [node], edges: [] };
  function inspektor(qa: JobQa): string {
    const karte: KuratierKartenDaten = { node, quelle: { jobId: 'j1', bild: 'b.png', qa }, kur: { markiert: false, verworfen: false } };
    return mount(<KuratierInspektor graph={graph} karte={karte} id="V-01" onMarkieren={() => {}} onVerwerfen={() => {}} onInsProjekt={() => {}} />).textContent ?? '';
  }
  for (const [name, qa, verdikt] of [
    ['echtes Durchfallen', echt(false, 'Geometrie 0.598 gegen 0.65'), 'verfehlt'],
    ['Bestehen ohne rho_maske', echt(true), 'bestanden'],
  ] as const) {
    it(`${name}: Verdikt steht, kein «zurückgezogen», knapper Hinweis nur zu den Sternen`, () => {
      const t = inspektor(qa);
      expect(t).toContain(`QA-Verdikt${verdikt}`);
      expect(t).not.toMatch(/zur(ue|ü)ckgezogen/);
      expect(t).not.toMatch(/widerlegt/);
      expect(t).toContain('Keine Sterne: die Geometrie-Zahlen dieses Ergebnisses sind als Wertung widerrufen.');
    });
  }
  it('der volle Grund-Satz steht weiter im Inspektor', () => {
    expect(inspektor(echt(false, LANG))).toContain(LANG);
  });
});
