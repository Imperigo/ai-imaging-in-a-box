// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { StationLogo } from '../src/station-logos';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | null = null;
let halter: HTMLDivElement | null = null;
function render(el: React.ReactElement): SVGSVGElement {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() => root!.render(el));
  return halter.querySelector('svg')!;
}
afterEach(() => {
  act(() => root?.unmount());
  halter?.remove();
});

function kern(svg: SVGSVGElement): SVGCircleElement {
  return svg.querySelector('[data-kosmo-kern]')!;
}
function wellen(svg: SVGSVGElement): SVGGElement | null {
  return svg.querySelector('[data-kosmo-wellen]');
}
function skala(el: Element | null): number {
  const m = /scale\(([\d.]+)\)/.exec((el as SVGElement | null)?.style.transform ?? '');
  return m ? Number(m[1]) : NaN;
}

describe('Kosmo-Logo folgt dem Pegel der Stimme (U2)', () => {
  it('lauter Pegel macht Scheibe und Wellen groesser als leiser', () => {
    const leise = render(<StationLogo logo="kosmo" bewegt kosmoZustand="spricht" pegel={0.1} />);
    const kLeise = skala(kern(leise));
    const wLeise = skala(wellen(leise));
    act(() => root?.unmount());
    halter?.remove();
    const laut = render(<StationLogo logo="kosmo" bewegt kosmoZustand="spricht" pegel={0.9} />);
    expect(skala(kern(laut))).toBeGreaterThan(kLeise);
    expect(skala(wellen(laut))).toBeGreaterThan(wLeise);
    // Mit Pegel schlaegt die Scheibe nicht zusaetzlich im festen Takt.
    expect(kern(laut).style.animation).toBe('');
  });

  it('ohne Pegel bleibt die feste Silben-Animation', () => {
    const svg = render(<StationLogo logo="kosmo" bewegt kosmoZustand="spricht" />);
    expect(kern(svg).style.animation).toContain('k-kosmo-silbe');
    expect(wellen(svg)?.style.transform ?? '').toBe('');
  });

  it('Pegel wird auf 0…1 begrenzt', () => {
    const svg = render(<StationLogo logo="kosmo" bewegt kosmoZustand="spricht" pegel={7} />);
    expect(skala(kern(svg))).toBeLessThanOrEqual(1.25);
  });

  it('«weniger Bewegung»: kein Mitschwingen', () => {
    const svg = render(<StationLogo logo="kosmo" bewegt={false} kosmoZustand="spricht" pegel={0.9} />);
    expect(kern(svg).style.transform).toBe('');
    expect(wellen(svg)).toBeNull();
  });

  it('nur im Zustand «spricht»', () => {
    const svg = render(<StationLogo logo="kosmo" bewegt kosmoZustand="hoert" pegel={0.9} />);
    expect(kern(svg).style.transform).toBe('');
  });
});
