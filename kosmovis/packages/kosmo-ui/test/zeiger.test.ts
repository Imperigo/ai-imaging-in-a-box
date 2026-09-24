import { describe, expect, it } from 'vitest';
import { istTouchArtig } from '../src/zeiger';

/**
 * D-8 (E-8 B, `docs/design/GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`) — der zentrale
 * Zeiger-Helfer: `pointerType !== 'mouse'` gilt als Touch-artig, Events OHNE
 * Auskunft gelten als Maus (Ehrlichkeits-Klausel, s. `src/zeiger.ts`).
 */
describe('istTouchArtig (D-8, E-8 B)', () => {
  it('touch und pen sind Touch-artig', () => {
    expect(istTouchArtig({ pointerType: 'touch' })).toBe(true);
    expect(istTouchArtig({ pointerType: 'pen' })).toBe(true);
  });

  it('mouse ist es nicht', () => {
    expect(istTouchArtig({ pointerType: 'mouse' })).toBe(false);
  });

  it('Events ohne pointerType-Auskunft zählen als Maus (jsdom-MouseEvents, ältere Engines)', () => {
    expect(istTouchArtig({})).toBe(false);
    expect(istTouchArtig({ pointerType: undefined })).toBe(false);
    expect(istTouchArtig({ pointerType: '' })).toBe(false);
  });

  it('ein unbekannter künftiger Zeigertyp fällt auf die Touch-Seite (E-8-Wortlaut: alles ausser mouse)', () => {
    expect(istTouchArtig({ pointerType: 'zukunft' })).toBe(true);
  });
});
