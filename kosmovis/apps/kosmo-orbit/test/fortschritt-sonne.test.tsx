// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import '../src/modules/vis/island/inhalte/sonne';
import { visInhaltsRegistry } from '../src/modules/vis/island/inhalte/registry';
import { blenderJobStatusWort, useBlenderJobsRuntime } from '../src/modules/vis/blender-jobs-runtime';

/**
 * Sonnenstunden (#4, Owner 06.10.2026): statt roh «Status: running» steht der Zustand deutsch in Worten, und
 * solange der Auftrag offen ist, eine unbestimmte Leiste (die Brücke meldet nur Start und Ende — Regel G6).
 * Der Rohwert bleibt als `data-status` für Proben und den Heimrechner-Worker.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let container: HTMLDivElement | null = null;

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  container?.remove();
  container = null;
  useBlenderJobsRuntime.setState({ jobs: {} });
});

function zeichne(): HTMLDivElement {
  const Stufe2 = visInhaltsRegistry.inhaltFuer('sonnenstunden')!.Stufe2!;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<Stufe2 />));
  return container;
}

describe('blenderJobStatusWort', () => {
  it('kein Rohwert bleibt stehen', () => {
    for (const s of ['awaiting_approval', 'queued', 'running', 'done', 'error', 'cancelled', 'kein-blender-worker'] as const) {
      expect(blenderJobStatusWort(s)).not.toBe(s);
      expect(blenderJobStatusWort(s)).not.toMatch(/_|running|queued/);
    }
  });
});

describe('Sonnenstunden-Insel — Zustand in Worten, Leiste solange offen', () => {
  it('laufend: unbestimmte Leiste mit Worten, kein «Status: running»', () => {
    useBlenderJobsRuntime.getState().setzeJob('sonnenstunden', { kind: 'blender-sim', status: 'running', jobId: 'j1', gestartetUm: Date.now() });
    const c = zeichne();
    const status = c.querySelector('[data-testid="island-sonnenstunden-status"]')!;
    expect(status.getAttribute('data-status')).toBe('running');
    expect(status.textContent).not.toContain('running');
    const warten = status.querySelector('.k-warten')!;
    expect(warten).not.toBeNull();
    expect(warten.getAttribute('data-form')).toBe('leiste');
    expect(warten.getAttribute('data-art')).toBe('unbestimmt');
  });

  it('beendet ohne Rechner: Worte statt Rohwert, keine Leiste mehr', () => {
    useBlenderJobsRuntime.getState().setzeJob('sonnenstunden', { kind: 'blender-sim', status: 'kein-blender-worker', jobId: 'j1' });
    const c = zeichne();
    const status = c.querySelector('[data-testid="island-sonnenstunden-status"]')!;
    expect(status.getAttribute('data-status')).toBe('kein-blender-worker');
    expect(status.textContent).not.toContain('kein-blender-worker');
    expect(status.querySelector('.k-warten')).toBeNull();
  });
});
