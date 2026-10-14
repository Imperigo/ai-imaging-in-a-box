// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KZahl } from '../src/kzahl';

/**
 * U19, Owner C7 (01.10.2026): «Zahlen zählen kurz hoch», mit G6: nur echte
 * Werte. Ändert sich eine Zahl, läuft sie in 320 ms zum neuen Wert; beim
 * ersten Anzeigen steht sie sofort da, und mit «weniger Bewegung» springt
 * sie. Vorgelesen wird immer nur der echte Endwert, nie ein Zwischenwert.
 *
 * Rot vor gruen: vorher gibt es `KZahl` nicht.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | null = null;
let halter: HTMLDivElement | null = null;
let reduziert = false;
beforeEach(() => {
  vi.useFakeTimers();
  reduziert = false;
  window.matchMedia = ((q: string) => ({ matches: reduziert, media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
  vi.stubGlobal('requestAnimationFrame', (f: FrameRequestCallback) => setTimeout(() => f(performance.now()), 16) as unknown as number);
  vi.stubGlobal('cancelAnimationFrame', (id: number) => clearTimeout(id));
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
});
afterEach(() => {
  act(() => root?.unmount());
  halter?.remove();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
const zeige = (el: React.ReactElement) => act(() => root!.render(el));
const sichtbar = () => halter!.querySelector('[data-kzahl-anzeige]')!.textContent;
const vorgelesen = () => halter!.querySelector('[data-kzahl-wert]')!.textContent;

describe('KZahl — Zahlen zählen kurz hoch (C7)', () => {
  it('beim ersten Anzeigen steht der Wert sofort da', () => {
    zeige(<KZahl wert={120} />);
    expect(sichtbar()).toBe('120');
    expect(vorgelesen()).toBe('120');
  });

  it('ein neuer Wert läuft hoch und endet genau auf dem Ziel', () => {
    zeige(<KZahl wert={100} />);
    zeige(<KZahl wert={200} />);
    act(() => void vi.advanceTimersByTime(160));
    const mitte = Number(sichtbar());
    expect(mitte).toBeGreaterThan(100);
    expect(mitte).toBeLessThan(200);
    // Vorgelesen wird nie ein Zwischenwert.
    expect(vorgelesen()).toBe('200');
    act(() => void vi.advanceTimersByTime(400));
    expect(sichtbar()).toBe('200');
  });

  it('mit «weniger Bewegung» springt der Wert', () => {
    reduziert = true;
    zeige(<KZahl wert={100} />);
    zeige(<KZahl wert={200} />);
    expect(sichtbar()).toBe('200');
  });

  it('formatiert mit der übergebenen Funktion, auch die Zwischenwerte', () => {
    const fmt = (n: number) => `${n.toFixed(1)} m²`;
    zeige(<KZahl wert={10} format={fmt} />);
    expect(sichtbar()).toBe('10.0 m²');
    zeige(<KZahl wert={20} format={fmt} />);
    act(() => void vi.advanceTimersByTime(600));
    expect(sichtbar()).toBe('20.0 m²');
    expect(vorgelesen()).toBe('20.0 m²');
  });
});
