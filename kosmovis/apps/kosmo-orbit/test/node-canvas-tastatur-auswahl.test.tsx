// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KAnsageBereich } from '@kosmo/ui';
import { NodeCanvas } from '../src/modules/vis/NodeCanvas';
import { useProject } from '../src/state/project-store';

class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * S3-a (`docs/UI-UX-2026-09-09-GRAPH-TASTATUR.md`) — Auswahl per Tastatur.
 * Enter/Leertaste rufen DENSELBEN Auswahlweg wie ein Klick auf den
 * Kopf-Griff (`setAuswahl(new Set([n.id]))`, `NodeCanvas.tsx`s
 * Einzelauswahl-Zweig) — geprüft hier NICHT über einen zweiten Mechanismus,
 * sondern über sein sichtbares Ergebnis: `data-testid="vis-node-
 * ausgewaehlt"` (derselbe Test-Hook, den auch der Maus-Pfad auslöst —
 * die CSS-Klasse heisst `vis-node-ausgewaehlt-rahmen`, der Test-Hook
 * selbst kürzer) und `aria-pressed`. `KAnsageBereich` wird HIER nur als
 * Test-Harness mitmontiert (dasselbe Singleton-Modul wie `ansage()`
 * selbst) — das Mounten in der echten Shell bleibt ausserhalb dieses
 * Dateikreises (s. Bericht).
 *
 * Beide Fälle unten liefen VOR dem Fix rot: ohne `onKeyDown` am Node-`<g>`
 * blieb `aria-pressed` nie gesetzt und der Auswahl-Rahmen erschien nie.
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let ansageRoot: Root | null = null;
let ansageContainer: HTMLDivElement | null = null;

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
  if (ansageRoot) {
    act(() => ansageRoot!.unmount());
    ansageRoot = null;
  }
  if (ansageContainer) {
    ansageContainer.remove();
    ansageContainer = null;
  }
});

function montiere(graphId: string): void {
  ansageContainer = document.createElement('div');
  document.body.appendChild(ansageContainer);
  ansageRoot = createRoot(ansageContainer);
  act(() => {
    ansageRoot!.render(<KAnsageBereich />);
  });

  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<NodeCanvas graphId={graphId} />);
  });
}

function neuerGraphMitZweiNodes(): string {
  const { runCommand } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `S3a-Auswahl-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  runCommand('vis.nodeSetzen', { graphId, typ: 'material', x: 300, y: 0 });
  return graphId;
}

function nodeGs(): SVGGElement[] {
  return Array.from(container!.querySelectorAll<SVGGElement>('[data-rf-index]')).sort(
    (a, b) => Number(a.getAttribute('data-rf-index')) - Number(b.getAttribute('data-rf-index')),
  );
}

function ausgewaehlteRahmen(): number {
  return container!.querySelectorAll('[data-testid="vis-node-ausgewaehlt"]').length;
}

function polite(): string {
  return ansageContainer!.querySelector('[data-testid="ansage-polite"]')!.textContent ?? '';
}

function druecke(el: Element, key: string): void {
  act(() => {
    el.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
  });
}

describe('NodeCanvas — Tastatur-Auswahl (S3-a)', () => {
  it('Pfeiltaste allein wählt NICHT aus — nur Wandern, kein Rahmen, kein aria-pressed', () => {
    const graphId = neuerGraphMitZweiNodes();
    montiere(graphId);

    expect(ausgewaehlteRahmen()).toBe(0);
    const [n0] = nodeGs();
    druecke(n0!, 'ArrowRight');

    expect(ausgewaehlteRahmen()).toBe(0);
    const gsNachher = nodeGs();
    expect(gsNachher.map((g) => g.getAttribute('aria-pressed'))).toEqual(['false', 'false']);
  });

  it('Enter am fokussierten Node wählt ihn — derselbe Auswahlweg wie ein Klick (Rahmen + aria-pressed), UND meldet die Auswahl über ansage()', () => {
    const graphId = neuerGraphMitZweiNodes();
    montiere(graphId);

    const [n0, n1] = nodeGs();
    // Erst zum zweiten Node wandern, DANN wählen — beweist, dass die
    // Auswahl dem FOKUS folgt, nicht immer Index 0 trifft.
    druecke(n0!, 'ArrowRight');
    druecke(n1!, 'Enter');

    expect(ausgewaehlteRahmen()).toBe(1);
    const gs = nodeGs();
    expect(gs[0]!.getAttribute('aria-pressed')).toBe('false');
    expect(gs[1]!.getAttribute('aria-pressed')).toBe('true');
    expect(polite()).toContain('ausgewählt');
    expect(polite()).toContain('Material-Bausteine');
  });

  it('Leertaste wählt genauso wie Enter, und Escape hebt die Auswahl wieder auf (bestehender globaler Weg)', () => {
    const graphId = neuerGraphMitZweiNodes();
    montiere(graphId);

    const [n0] = nodeGs();
    druecke(n0!, ' ');
    expect(ausgewaehlteRahmen()).toBe(1);
    expect(nodeGs()[0]!.getAttribute('aria-pressed')).toBe('true');

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(ausgewaehlteRahmen()).toBe(0);
    expect(nodeGs()[0]!.getAttribute('aria-pressed')).toBe('false');
  });
});
