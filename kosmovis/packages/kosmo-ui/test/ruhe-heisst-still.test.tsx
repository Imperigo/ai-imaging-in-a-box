// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeAll, describe, expect, it } from 'vitest';
import { KosmoOrbitMarke } from '../src/kosmoorbit-marke';
import { StationLogo } from '../src/station-logos';

/**
 * Owner-Abstimmung mit Visbox, G1 (01.10.2026): «Bewegung nur, wenn etwas
 * passiert. In Ruhe steht alles still.» Ersetzt B16 («Marke und Kosmo immer
 * animiert») und den Wunsch vom 30.09. («animiere immer überall das Logo»).
 *
 * Rot vor gruen: vorher lief der Trabant der Marke in jedem Browser, der
 * Bahnen kennt, und der ruhige Kosmo atmete dauernd.
 */

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
beforeAll(() => {
  // Ein Browser, der Bahnen kennt und keine «weniger Bewegung» verlangt —
  // genau der Fall, in dem die Marke bisher dauernd lief.
  (globalThis as unknown as { CSS: { supports: () => boolean } }).CSS = { supports: () => true };
  window.matchMedia = ((q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
});

describe('Ruhe heisst still (G1)', () => {
  it('die Marke steht in Ruhe still: kein Umlauf, keine Regel', () => {
    const svg = render(<KosmoOrbitMarke />);
    expect(svg.getAttribute('data-bewegt')).toBe('nein');
    expect(svg.querySelector('style')).toBeNull();
  });

  it('die Marke laeuft, wenn etwas passiert (`aktiv`)', () => {
    const svg = render(<KosmoOrbitMarke aktiv />);
    expect(svg.getAttribute('data-bewegt')).toBe('ja');
    expect(svg.querySelector('style')?.textContent).toContain('k-marke-umlauf');
  });

  it('«weniger Bewegung» gewinnt auch gegen `aktiv`', () => {
    const svg = render(<KosmoOrbitMarke aktiv bewegt={false} />);
    expect(svg.getAttribute('data-bewegt')).toBe('nein');
  });

  it('StationLogo «orbit» reicht `aktiv` an die Marke weiter', () => {
    expect(render(<StationLogo logo="orbit" />).getAttribute('data-bewegt')).toBe('nein');
    act(() => root?.unmount());
    halter?.remove();
    expect(render(<StationLogo logo="orbit" aktiv />).getAttribute('data-bewegt')).toBe('ja');
  });

  it('der ruhige Kosmo atmet nicht; denkend bewegt er sich', () => {
    const ruhig = render(<StationLogo logo="kosmo" bewegt />);
    expect(ruhig.querySelector<SVGCircleElement>('[data-kosmo-kern]')!.style.animation).toBe('');
    act(() => root?.unmount());
    halter?.remove();
    const denkt = render(<StationLogo logo="kosmo" bewegt kosmoZustand="denkt" />);
    expect(denkt.querySelector<SVGCircleElement>('[data-kosmo-kern]')!.style.animation).toContain('k-kosmo-atem');
  });
});
