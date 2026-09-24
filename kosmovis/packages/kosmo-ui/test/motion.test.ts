// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { mitUebergang } from '../src/motion';

/**
 * v0.6.6 MOTION-KONZEPT-066 §4: `mitUebergang()` kapselt
 * `document.startViewTransition` mit Feature-Detection. jsdom kennt
 * `startViewTransition` nicht (Stand jsdom-Version hier) — das deckt den
 * Fallback-Pfad automatisch UND explizit ab; der Support-Pfad wird über
 * einen Mock auf `document` simuliert.
 */

afterEach(() => {
  vi.restoreAllMocks();
  // @ts-expect-error -- Test-Cleanup eines evtl. gemockten Feldes
  delete document.startViewTransition;
});

describe('mitUebergang — Fallback (kein startViewTransition ODER reduced-motion)', () => {
  it('ohne document.startViewTransition läuft wechsel() synchron direkt', () => {
    expect(typeof (document as { startViewTransition?: unknown }).startViewTransition).not.toBe('function');
    let lief = false;
    mitUebergang(() => {
      lief = true;
    });
    expect(lief).toBe(true);
  });

  it('mit prefers-reduced-motion: reduce läuft wechsel() direkt, obwohl startViewTransition existiert', () => {
    const startViewTransition = vi.fn();
    (document as unknown as { startViewTransition: typeof startViewTransition }).startViewTransition = startViewTransition;
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: query.includes('prefers-reduced-motion'),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));

    let lief = false;
    mitUebergang(() => {
      lief = true;
    });
    expect(lief).toBe(true);
    expect(startViewTransition).not.toHaveBeenCalled();
  });
});

describe('mitUebergang — Support-Pfad', () => {
  it('mit startViewTransition UND ohne reduced-motion läuft wechsel() innerhalb der View Transition', () => {
    let lief = false;
    const startViewTransition = vi.fn((callback: () => void) => {
      callback();
      return {} as unknown;
    });
    (document as unknown as { startViewTransition: typeof startViewTransition }).startViewTransition = startViewTransition;
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: false,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));

    mitUebergang(() => {
      lief = true;
    });
    expect(startViewTransition).toHaveBeenCalledTimes(1);
    expect(lief).toBe(true);
  });
});
