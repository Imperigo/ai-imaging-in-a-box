// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { cssVar } from '../src/css-var';

/**
 * v0.8.8 / PA4 (`docs/V088-SPEZ.md` §2 D7/§3, Token-Brücke Vis) — Wächter für
 * den neuen `cssVar()`-Helfer: liest eine CSS-Custom-Property vom
 * Dokument-Wurzelelement (getComputedStyle), Fallback bei Fehlen/Leerwert.
 * Muster wie `Viewport3D.tsx:811` (NUR als Vorbild gelesen, dort NICHT
 * angefasst — Sanktion 6/§4).
 */

afterEach(() => {
  document.documentElement.style.cssText = '';
});

describe('cssVar', () => {
  it('liest eine gesetzte CSS-Custom-Property vom :root', () => {
    document.documentElement.style.setProperty('--k-test-farbe', '#a84b2b');
    expect(cssVar('--k-test-farbe', '#000000')).toBe('#a84b2b');
  });

  it('trimmt Weissraum um den gelesenen Wert', () => {
    document.documentElement.style.setProperty('--k-test-farbe', '  #2455a4  ');
    expect(cssVar('--k-test-farbe', '#000000')).toBe('#2455a4');
  });

  it('fällt auf den Fallback zurück, wenn die Property nicht gesetzt ist', () => {
    expect(cssVar('--k-nie-gesetzt', '#f6dfae')).toBe('#f6dfae');
  });

  it('fällt auf den Fallback zurück, wenn die Property auf einen Leerwert gesetzt ist', () => {
    document.documentElement.style.setProperty('--k-test-farbe', '');
    expect(cssVar('--k-test-farbe', '#c7c7c7')).toBe('#c7c7c7');
  });

  it('spiegelt einen Theme-/Akzent-Wechsel wider (Neusetzen vor dem nächsten Redraw genügt)', () => {
    document.documentElement.style.setProperty('--k-test-farbe', '#5c7fa8');
    expect(cssVar('--k-test-farbe', '#000000')).toBe('#5c7fa8');
    // Simuliert einen Akzent-/Theme-Wechsel: derselbe Custom-Property-Name
    // bekommt live einen neuen Wert — cssVar() liest ihn beim nächsten Aufruf
    // sofort neu (keine eigene Zwischenspeicherung).
    document.documentElement.style.setProperty('--k-test-farbe', '#a2543f');
    expect(cssVar('--k-test-farbe', '#000000')).toBe('#a2543f');
  });
});
