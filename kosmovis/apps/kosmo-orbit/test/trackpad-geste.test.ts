// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest';
import { bindeWebkitPinch, deuteRad, PINCH_RAD_EMPFINDLICHKEIT } from '../src/shell/trackpad-geste';
import { radZoomFaktor } from '../src/modules/design/navigation-geste';

/** E152: zwei Finger wischen = schieben, Pinch = zoomen, Mausrad = zoomen. */
describe('deuteRad', () => {
  it('Mausrad-Notch (ganzzahlig, wheelDelta 120) → zoomen wie bisher', () => {
    expect(deuteRad({ deltaY: 100, wheelDelta: -120 })).toEqual({ art: 'zoom', faktor: radZoomFaktor(100) });
  });
  it('Trackpad senkrecht (Bruchwert) → schieben', () => {
    expect(deuteRad({ deltaY: 4.5 })).toEqual({ art: 'schwenk', dx: 0, dy: 4.5 });
  });
  it('Trackpad senkrecht in WebKit (ganzzahlig, wheelDelta kein 120er) → schieben', () => {
    expect(deuteRad({ deltaY: 3, wheelDelta: -9 })).toEqual({ art: 'schwenk', dx: 0, dy: 3 });
  });
  it('Trackpad seitlich (deltaX) → schieben', () => {
    expect(deuteRad({ deltaX: -12, deltaY: 0 })).toEqual({ art: 'schwenk', dx: -12, dy: 0 });
  });
  it('Pinch in Chromium (ctrlKey) → zoomen, feiner als das Mausrad', () => {
    const d = deuteRad({ deltaY: -10, ctrlKey: true });
    expect(d).toEqual({ art: 'zoom', faktor: Math.exp(10 * PINCH_RAD_EMPFINDLICHKEIT) });
    expect(d.art === 'zoom' && d.faktor > 1).toBe(true);
  });
  it('Zeilenmodus (Firefox) wird in Pixel umgerechnet', () => {
    expect(deuteRad({ deltaX: 2, deltaY: 0, deltaMode: 1 })).toEqual({ art: 'schwenk', dx: 32, dy: 0 });
  });
  it('kein Ausschlag → Mausrad-Zweig mit Faktor 1 (aendert nichts)', () => {
    expect(deuteRad({ deltaY: 0 })).toEqual({ art: 'zoom', faktor: 1 });
  });
});

describe('bindeWebkitPinch', () => {
  function geste(typ: string, scale: number): Event {
    const e = new Event(typ, { cancelable: true });
    Object.assign(e, { scale, clientX: 10, clientY: 20 });
    return e;
  }
  it('meldet je Schritt den Faktor zum vorigen Schritt, verhindert das Seiten-Zoomen, und laesst sich abmelden', () => {
    const el = document.createElement('div');
    const onZoom = vi.fn();
    const ab = bindeWebkitPinch(el, onZoom);
    const s = geste('gesturestart', 1);
    el.dispatchEvent(s);
    expect(s.defaultPrevented).toBe(true);
    el.dispatchEvent(geste('gesturechange', 1.5));
    el.dispatchEvent(geste('gesturechange', 3));
    expect(onZoom.mock.calls.map((c) => [Number(c[0].toFixed(3)), c[1], c[2]])).toEqual([
      [1.5, 10, 20],
      [2, 10, 20],
    ]);
    el.dispatchEvent(geste('gestureend', 3));
    el.dispatchEvent(geste('gesturestart', 1));
    el.dispatchEvent(geste('gesturechange', 0.5));
    expect(onZoom).toHaveBeenLastCalledWith(0.5, 10, 20);
    ab();
    el.dispatchEvent(geste('gesturechange', 2));
    expect(onZoom).toHaveBeenCalledTimes(3);
  });
  it('ein ungueltiger Wert (0, NaN) wird ignoriert', () => {
    const el = document.createElement('div');
    const onZoom = vi.fn();
    bindeWebkitPinch(el, onZoom);
    el.dispatchEvent(geste('gesturestart', 1));
    el.dispatchEvent(geste('gesturechange', 0));
    el.dispatchEvent(geste('gesturechange', Number.NaN));
    expect(onZoom).not.toHaveBeenCalled();
  });
});
