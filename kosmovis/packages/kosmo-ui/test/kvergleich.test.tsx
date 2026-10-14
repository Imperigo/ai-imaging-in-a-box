// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { KVergleich } from '../src/kvergleich';

/**
 * C45, Owner-Wahl «B — Regler mit Sprung» (01.10.2026): zwei Varianten
 * übereinander, eine Linie mit Griff teilt sie; dazu «A · A|B · B», ein Tipp
 * springt ganz auf eine Seite. Gleich wie der Wischregler in Visbox (Nr. 17).
 *
 * Rot vor gruen: vorher gibt es `KVergleich` nicht.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | null = null;
let halter: HTMLDivElement | null = null;
beforeEach(() => {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
});
afterEach(() => {
  act(() => root?.unmount());
  halter?.remove();
});
const zeige = () =>
  act(() =>
    root!.render(
      <KVergleich
        links={{ name: 'Variante A · Satteldach', inhalt: <div data-testid="a">A</div> }}
        rechts={{ name: 'Variante B · Flachdach', inhalt: <div data-testid="b">B</div> }}
      />,
    ),
  );
const regler = () => halter!.querySelector<HTMLElement>('[role="slider"]')!;
const anteil = () => Number(regler().getAttribute('aria-valuenow'));

describe('KVergleich (C45 B)', () => {
  it('beide Varianten liegen übereinander, der Regler steht in der Mitte und ist vorlesbar', () => {
    zeige();
    expect(halter!.querySelector('[data-testid="a"]')).not.toBeNull();
    expect(halter!.querySelector('[data-testid="b"]')).not.toBeNull();
    expect(anteil()).toBe(50);
    expect(regler().getAttribute('aria-label')).toContain('Variante A · Satteldach');
    expect(halter!.textContent).toContain('Variante B · Flachdach');
  });

  it('Pfeiltasten verschieben in 5er-Schritten, Pos1/Ende springen an den Rand', () => {
    zeige();
    act(() => regler().dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true })));
    expect(anteil()).toBe(55);
    act(() => regler().dispatchEvent(new KeyboardEvent('keydown', { key: 'Home', bubbles: true })));
    expect(anteil()).toBe(0);
    act(() => regler().dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true })));
    expect(anteil()).toBe(100);
  });

  it('der Umschalter springt ganz auf A, auf B und zurück zum Teilbild', () => {
    zeige();
    const knopf = (t: string) => [...halter!.querySelectorAll<HTMLButtonElement>('.k-vergleich-sprung button')].find((b) => b.textContent === t)!;
    act(() => knopf('A').click());
    expect(anteil()).toBe(100);
    expect(knopf('A').getAttribute('aria-pressed')).toBe('true');
    act(() => knopf('B').click());
    expect(anteil()).toBe(0);
    act(() => knopf('A | B').click());
    expect(anteil()).toBe(50);
  });

  it('die rechte Variante wird von links bis zum Regler verdeckt (clip-path)', () => {
    zeige();
    const b = halter!.querySelector<HTMLElement>('.k-vergleich-rechts')!;
    expect(b.style.clipPath).toBe('inset(0 0 0 50%)');
  });
});
