// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KMeldungen, melde, meldeFehler, setzeKosmoFragen } from '../src/meldungen';

/**
 * U16, Owner B10 (01.10.2026): «Fehler kurz + ‹Kosmo fragen› daneben.» Wer
 * eine Fehlermeldung nicht versteht, fragt Kosmo mit einem Tipp — die
 * Meldung geht dabei wörtlich mit.
 *
 * Rot vor gruen: vorher gibt es `setzeKosmoFragen` nicht.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root | null = null;
let halter: HTMLDivElement | null = null;
beforeEach(() => {
  vi.useFakeTimers();
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() => root!.render(<KMeldungen />));
});
afterEach(() => {
  act(() => vi.advanceTimersByTime(20000));
  act(() => root?.unmount());
  halter?.remove();
  setzeKosmoFragen(null);
  vi.useRealTimers();
});
const knopf = () => halter!.querySelector<HTMLButtonElement>('[data-testid="meldung-kosmo-fragen"]');

describe('Fehler mit «Kosmo fragen» (B10)', () => {
  it('ein Fehler zeigt «Kosmo fragen», wenn Kosmo da ist, und gibt die Meldung wörtlich mit', () => {
    const frage = vi.fn();
    setzeKosmoFragen(frage);
    act(() => meldeFehler(new Error('Wand zu kurz')));
    expect(knopf()?.textContent).toBe('Kosmo fragen');
    act(() => knopf()!.click());
    expect(frage).toHaveBeenCalledTimes(1);
    expect(frage.mock.calls[0]![0]).toContain('Wand zu kurz');
    expect(halter!.querySelector('[data-testid="meldung-fehler"]')).toBeNull();
  });

  it('ohne Kosmo kein Knopf — nichts, das ins Leere führt', () => {
    act(() => meldeFehler('Wand zu kurz'));
    expect(knopf()).toBeNull();
  });

  it('nur bei Fehlern, nicht bei Info oder Erfolg', () => {
    setzeKosmoFragen(() => {});
    act(() => melde('Gesichert', { ton: 'erfolg' }));
    expect(knopf()).toBeNull();
  });

  it('eine eigene Aktion der Meldung bleibt daneben bestehen', () => {
    setzeKosmoFragen(() => {});
    act(() => meldeFehler('Nicht gesichert', { label: 'Nochmals', run: () => {} }));
    expect(halter!.textContent).toContain('Nochmals');
    expect(knopf()).not.toBeNull();
  });
});
