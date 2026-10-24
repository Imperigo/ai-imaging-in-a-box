// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { blasenLage, KTooltip, KTooltipPortal } from '../src/tooltip';

/**
 * R6.4 — Kurzhilfen werden in der Knotenansicht nie vom Knotenrand beschnitten.
 * Ohne Anbieter bleibt KTooltip wie bisher (Blase im Baum); mit `KTooltipPortal`
 * haengt die Blase an `document.body`, Lage aus dem Rect des Ausloesers.
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  host = document.createElement('div');
  host.style.overflow = 'hidden';
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => {
  delete (HTMLElement.prototype as unknown as Record<string, unknown>).offsetWidth;
  delete (HTMLElement.prototype as unknown as Record<string, unknown>).offsetHeight;
  act(() => root.unmount());
  host.remove();
});

function rect(r: { left: number; top: number; width: number; height: number }): DOMRect {
  return { ...r, right: r.left + r.width, bottom: r.top + r.height, x: r.left, y: r.top, toJSON: () => ({}) } as DOMRect;
}

function oeffne(): HTMLElement {
  const knopf = host.querySelector('button')!;
  act(() => {
    knopf.dispatchEvent(new FocusEvent('focusin', { bubbles: true }));
    knopf.focus();
  });
  return knopf;
}

describe('KTooltip ohne Anbieter — unveraendert', () => {
  it('die Blase steht im Baum des Ausloesers, nicht an body', () => {
    act(() => root.render(<KTooltip text="Hilfe"><button>A</button></KTooltip>));
    oeffne();
    const blase = host.querySelector('.k-tooltip-blase');
    expect(blase).not.toBeNull();
    expect(blase!.className).toContain('k-tooltip-blase--oben');
    expect(blase!.className).not.toContain('--portal');
    expect(document.body.querySelectorAll(':scope > .k-tooltip-blase').length).toBe(0);
  });
});

describe('KTooltip mit KTooltipPortal', () => {
  it('die Blase haengt an document.body, nicht im overflow-Vorfahren', () => {
    act(() => root.render(<KTooltipPortal><KTooltip text="Hilfe"><button>A</button></KTooltip></KTooltipPortal>));
    oeffne();
    expect(host.querySelector('.k-tooltip-blase')).toBeNull();
    const blase = document.body.querySelector(':scope > .k-tooltip-blase--portal') as HTMLElement | null;
    expect(blase).not.toBeNull();
    expect(blase!.getAttribute('role')).toBe('tooltip');
  });

  it('aria-describedby zeigt weiter auf den immer vorhandenen Text im Baum', () => {
    act(() => root.render(<KTooltipPortal><KTooltip text="Hilfe"><button>A</button></KTooltip></KTooltipPortal>));
    const id = host.querySelector('button')!.getAttribute('aria-describedby')!;
    expect(document.getElementById(id)?.textContent).toBe('Hilfe');
  });

  it('die Lage kommt aus dem Rect des Ausloesers und folgt dem Scroll', () => {
    act(() => root.render(<KTooltipPortal><KTooltip text="Hilfe" lage="unten"><button>A</button></KTooltip></KTooltipPortal>));
    const wrap = host.querySelector('.k-tooltip') as HTMLElement;
    let top = 100;
    wrap.getBoundingClientRect = () => rect({ left: 400, top, width: 40, height: 20 });
    Object.defineProperty(HTMLElement.prototype, 'offsetWidth', { configurable: true, get: () => 80 });
    Object.defineProperty(HTMLElement.prototype, 'offsetHeight', { configurable: true, get: () => 24 });
    oeffne();
    const blase = () => document.body.querySelector('.k-tooltip-blase--portal') as HTMLElement;
    expect(blase().style.left).toBe('380px');
    expect(blase().style.top).toBe('126px');
    top = 300;
    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    expect(blase().style.top).toBe('326px');
  });

  it('Schliessen entfernt die Blase aus body', () => {
    act(() => root.render(<KTooltipPortal><KTooltip text="Hilfe"><button>A</button></KTooltip></KTooltipPortal>));
    const knopf = oeffne();
    expect(document.body.querySelector('.k-tooltip-blase--portal')).not.toBeNull();
    act(() => {
      knopf.blur();
    });
    expect(document.body.querySelector('.k-tooltip-blase--portal')).toBeNull();
  });
});

describe('blasenLage — Umklappen und Einruecken am Fensterrand', () => {
  const fenster = { width: 1000, height: 700 };
  const blase = { width: 120, height: 30 };
  it('oben mit Platz bleibt oben, mittig', () => {
    const l = blasenLage({ left: 500, top: 300, width: 40, height: 20 }, blase, fenster, 'oben');
    expect(l.lage).toBe('oben');
    expect(l.left).toBe(460);
    expect(l.top).toBe(300 - 6 - 30);
  });
  it('oben ohne Platz klappt nach unten um', () => {
    const l = blasenLage({ left: 500, top: 10, width: 40, height: 20 }, blase, fenster, 'oben');
    expect(l.lage).toBe('unten');
    expect(l.top).toBe(36);
  });
  it('unten am Fensterboden klappt nach oben um', () => {
    const l = blasenLage({ left: 500, top: 680, width: 40, height: 20 }, blase, fenster, 'unten');
    expect(l.lage).toBe('oben');
  });
  it('am rechten Rand rueckt die Blase ein, statt hinauszulaufen', () => {
    const l = blasenLage({ left: 980, top: 300, width: 16, height: 20 }, blase, fenster, 'oben');
    expect(l.left + blase.width).toBeLessThanOrEqual(fenster.width - 8);
  });
  it('am linken Rand rueckt sie ein', () => {
    const l = blasenLage({ left: -30, top: 300, width: 16, height: 20 }, blase, fenster, 'oben');
    expect(l.left).toBe(8);
  });
  it('rechts ohne Platz klappt nach links um', () => {
    const l = blasenLage({ left: 950, top: 300, width: 30, height: 20 }, blase, fenster, 'rechts');
    expect(l.lage).toBe('links');
  });
});
