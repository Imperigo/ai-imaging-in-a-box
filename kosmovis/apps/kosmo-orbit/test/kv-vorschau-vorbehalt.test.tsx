// @vitest-environment jsdom
import { act } from 'react';
import { createRoot } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { GUETE_MARKE_HINWEIS, GUETE_MARKE_TEXT, GUETE_VORBEHALT, GueteMarke } from '../src/modules/vis/GueteMarke';
import { GUETE_TEXTE } from '../src/modules/vis/guete';

/**
 * Visbox-Ergebnis auf-20261023-346: Am Testhaus übermalte die Vorschau (ohne das Grundbild als Bildeingang) das
 * Fensterband im OG und die Bäume, die volle Güte hielt beides. Der Vorbehalt steht darum am Anfang der Kurzhilfe der
 * Marke «Vorschau» — an jedem Ort, an dem die Marke steht — und in der Kurzhilfe des Schalters. Die Marke selbst bleibt
 * das eine Wort (sie ist eine Pille ohne Umbruch im Knoten fester Höhe).
 */
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const offen: (() => void)[] = [];
afterEach(() => {
  while (offen.length) offen.pop()!();
});
function zeichne(el: React.ReactElement): HTMLDivElement {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root = createRoot(host);
  act(() => root.render(el));
  offen.push(() => {
    act(() => root.unmount());
    host.remove();
  });
  return host;
}

describe('Vorbehalt der Vorschau (346)', () => {
  it('die Kurzhilfe der Marke beginnt mit «Vorschau — Fenster und Form nicht gesichert»', () => {
    expect(GUETE_VORBEHALT).toBe('Vorschau — Fenster und Form nicht gesichert');
    expect(GUETE_MARKE_HINWEIS.startsWith(GUETE_VORBEHALT)).toBe(true);
    expect(GUETE_MARKE_HINWEIS).toContain('Fenster übermalen');
    expect(GUETE_MARKE_HINWEIS).toContain('«Güte: Voll»');
  });
  it('an jeder Form der Marke steht der Vorbehalt in der Kurzhilfe, die Pille bleibt ein Wort', () => {
    for (const form of ['bild', 'abzeichen', 'zeile'] as const) {
      const h = zeichne(<GueteMarke lauf={{ guete: 'vorschau' }} testid="m" form={form} />);
      expect(h.querySelector('[data-testid="m"]')!.textContent).toBe(GUETE_MARKE_TEXT);
      expect(h.textContent).toContain(GUETE_VORBEHALT);
    }
  });
  it('ein volles Bild trägt keinen Vorbehalt', () => {
    expect(zeichne(<GueteMarke lauf={{ guete: 'voll' }} testid="m" />).innerHTML).toBe('');
  });
  it('der Schalter sagt es vor dem Rechnen', () => {
    expect(GUETE_TEXTE.vorschau.hinweis).toContain('Fenster und Form sind darum nicht gesichert');
    expect(GUETE_TEXTE.voll.hinweis).not.toContain('nicht gesichert');
  });
});
