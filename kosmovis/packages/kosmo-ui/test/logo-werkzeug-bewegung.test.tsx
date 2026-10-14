// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { StationLogo } from '../src/station-logos';

/**
 * Owner-Entscheid 01.10.2026 (B16): «Marke und Kosmo bewegen sich immer leicht;
 * die Werkzeug-Logos nur, wenn sie aktiv sind oder man darüberfährt.»
 * Bis hierher standen die Werkzeug-Logos immer still.
 *
 * Rot vor gruen: vorher gibt es weder `aktiv` noch eine Trabanten-Gruppe, die
 * sich bewegen koennte.
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

describe('Werkzeug-Logos bewegen sich nur bei Aktivitaet oder Darueberfahren', () => {
  it('der Trabant ist eine eigene Gruppe, die laufen kann', () => {
    const svg = render(<StationLogo logo="draw" size={40} bewegt />);
    expect(svg.querySelector('.k-logo-trabant')).not.toBeNull();
  });

  it('in Ruhe steht er; Darueberfahren laesst ihn laufen (Regel im eigenen Stil)', () => {
    const svg = render(<StationLogo logo="draw" size={40} bewegt />);
    expect(svg.getAttribute('data-aktiv')).toBe('nein');
    const stil = svg.querySelector('style')?.textContent ?? '';
    expect(stil).toMatch(/:hover[^{]*\.k-logo-trabant/);
    expect(stil).toMatch(/\[data-aktiv="ja"\][^{]*\.k-logo-trabant/);
  });

  it('aktiv: er laeuft', () => {
    const svg = render(<StationLogo logo="draw" size={40} bewegt aktiv />);
    expect(svg.getAttribute('data-aktiv')).toBe('ja');
  });

  it('weniger Bewegung: keine Laufregel, auch nicht aktiv', () => {
    const svg = render(<StationLogo logo="draw" size={40} bewegt={false} aktiv />);
    expect(svg.querySelector('style')).toBeNull();
  });
});
