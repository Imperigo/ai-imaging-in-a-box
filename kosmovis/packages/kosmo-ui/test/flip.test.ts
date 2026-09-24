// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { flipFirst, flipPlay, reduzierteBewegungAktiv } from '../src/flip';

/**
 * v0.7.2 W2-C — FLIP-Utility (`docs/V072-VISUELLES-UPDATE-SPEZ.md` §4).
 * jsdom liefert `getBoundingClientRect()` immer als Nullen — die Tests
 * überschreiben sie gezielt je Element (Standard-Muster für FLIP-Tests ohne
 * echtes Layout).
 */

function mitRect(el: HTMLElement, rect: { left: number; top: number; width: number; height: number }): void {
  el.getBoundingClientRect = () =>
    ({ ...rect, right: rect.left + rect.width, bottom: rect.top + rect.height, x: rect.left, y: rect.top, toJSON: () => rect }) as DOMRect;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('reduzierteBewegungAktiv', () => {
  it('liest prefers-reduced-motion über matchMedia', () => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: query.includes('prefers-reduced-motion'),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));
    expect(reduzierteBewegungAktiv()).toBe(true);
  });

  it('ohne matchMedia (SSR/Test-Umgebung) gilt "nicht reduziert"', () => {
    vi.stubGlobal('matchMedia', undefined);
    expect(reduzierteBewegungAktiv()).toBe(false);
  });
});

describe('flipFirst', () => {
  it('friert die vier Kernwerte aus getBoundingClientRect ein', () => {
    const el = document.createElement('div');
    mitRect(el, { left: 10, top: 20, width: 30, height: 40 });
    expect(flipFirst(el)).toEqual({ left: 10, top: 20, width: 30, height: 40 });
  });
});

describe('flipPlay', () => {
  it('reduced-motion: setzt KEIN Transform (Element springt direkt an die neue Position)', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true, media: '', addEventListener: () => {}, removeEventListener: () => {} }));
    const el = document.createElement('div');
    mitRect(el, { left: 0, top: 0, width: 50, height: 50 });
    flipPlay(el, { left: 100, top: 100, width: 50, height: 50 });
    expect(el.style.transform).toBe('');
  });

  it('bei realer Verschiebung: setzt sofort den inversen Transform (vor dem nächsten Frame)', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: false, media: '', addEventListener: () => {}, removeEventListener: () => {} }));
    const el = document.createElement('div');
    mitRect(el, { left: 100, top: 0, width: 50, height: 50 });
    flipPlay(el, { left: 0, top: 0, width: 50, height: 50 });
    // Inverser Transform: alte Position (0) minus neue Position (100) = -100.
    expect(el.style.transform).toContain('translate(-100px, 0px)');
    expect(el.style.transition).toBe('none');
  });

  it('ohne messbare Verschiebung/Skalierung: rührt kein Transform an (kein No-op-Sprung)', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: false, media: '', addEventListener: () => {}, removeEventListener: () => {} }));
    const el = document.createElement('div');
    mitRect(el, { left: 10, top: 10, width: 50, height: 50 });
    flipPlay(el, { left: 10, top: 10, width: 50, height: 50 });
    expect(el.style.transform).toBe('');
  });
});
