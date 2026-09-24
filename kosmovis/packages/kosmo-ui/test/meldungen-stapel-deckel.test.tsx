// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KMeldungen, melde } from '../src/meldungen';

// Gleiches Muster wie `overlay-schliessen.test.tsx`/`p2-glass-optik.test.tsx`:
// ohne dieses Flag warnt React bei jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * P-TOASTDECKEL — «die Meldung deckt den Knopf zu, der sie ausgelöst hat»
 * (`docs/UI-2026-08-27-B72-MELDUNG-UEBER-FENSTER.md` §3a). Gemessen im
 * Browser, unveränderter TKB, «Ausführen» mehrmals gedrückt: der Host wächst
 * je Toast um genau +67,2 px nach oben (`bottom:160px` bleibt fix,
 * `aura.css:3096`), Unterkante bleibt bei 740. Ab dem DRITTEN gleichzeitig
 * stehenden Toast erreicht der Stapel die Ausführen-Knöpfe, die ihn selbst
 * ausgelöst haben — 3,6 px ist derselbe invariante Versatz, der in §2a für
 * die Plakat-Popup-Knöpfe an allen drei Fenstergrössen gemessen wurde: eine
 * Konstante der Stapelgeometrie, kein Zufall einer Fenstergrösse.
 *
 * Ursache liegt in der STAPELGEOMETRIE (wie viele volle Karten gleichzeitig
 * übereinander gerendert werden), nicht im einzelnen Toast — darum begrenzt
 * der Fix die Zahl gleichzeitig voll gerenderter Karten, statt Text, Ton
 * oder Lebensdauer eines einzelnen Toasts anzufassen.
 *
 * Gegenprobe ist Pflicht (Auftrag): bei 1 und bei 2 Toasts ändert sich
 * nichts — weder Kartenzahl noch Markup. Die ersten beiden Fälle unten sind
 * genau diese Gegenprobe und müssen VOR und NACH dem Fix identisch grün
 * bleiben.
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<KMeldungen />);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  // Alle offenen Toasts ausklingen lassen — `meldungen`-Array ist ein
  // Modul-Singleton (kein Store-Reset exportiert), der nächste Testfall
  // muss darum mit geleertem Zustand starten.
  act(() => {
    vi.advanceTimersByTime(9000);
  });
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
  vi.useRealTimers();
});

describe('KMeldungen — Stapeldeckel (P-TOASTDECKEL)', () => {
  it('Gegenprobe 1 Toast: eine Karte, kein Stapel-Hinweis', () => {
    montiere();
    act(() => {
      melde('Standpunkt «Eingang»: Augenhoehe 1.3 m liegt ausserhalb der plausiblen Spanne 1.5-2.0 m.', {
        ton: 'fehler',
      });
    });
    const karten = container!.querySelectorAll('.k-meldung-karte');
    expect(karten.length).toBe(1);
    expect(container!.querySelector('[data-testid="meldung-stapel-hinweis"]')).toBeNull();
  });

  it('Gegenprobe 2 Toasts: zwei Karten, kein Stapel-Hinweis', () => {
    montiere();
    act(() => {
      melde('Fehler A', { ton: 'fehler' });
      melde('Fehler B', { ton: 'fehler' });
    });
    const karten = container!.querySelectorAll('.k-meldung-karte');
    expect(karten.length).toBe(2);
    expect(container!.querySelector('[data-testid="meldung-stapel-hinweis"]')).toBeNull();
  });

  it('ab 3 Toasts: höchstens 2 volle Karten, Rest als kompakter Stapel-Hinweis', () => {
    montiere();
    act(() => {
      melde('Fehler A', { ton: 'fehler' });
      melde('Fehler B', { ton: 'fehler' });
      melde('Fehler C', { ton: 'fehler' });
    });
    const karten = container!.querySelectorAll('.k-meldung-karte');
    expect(karten.length).toBeLessThanOrEqual(2);
    const hinweis = container!.querySelector('[data-testid="meldung-stapel-hinweis"]');
    expect(hinweis).not.toBeNull();
    expect(hinweis!.textContent).toMatch(/1/);
  });

  it('4 Toasts (Kanalgrenze aus meldungen.tsx): weiterhin höchstens 2 volle Karten', () => {
    montiere();
    act(() => {
      melde('Fehler A', { ton: 'fehler' });
      melde('Fehler B', { ton: 'fehler' });
      melde('Fehler C', { ton: 'fehler' });
      melde('Fehler D', { ton: 'fehler' });
    });
    const karten = container!.querySelectorAll('.k-meldung-karte');
    expect(karten.length).toBeLessThanOrEqual(2);
    const hinweis = container!.querySelector('[data-testid="meldung-stapel-hinweis"]');
    expect(hinweis).not.toBeNull();
    expect(hinweis!.textContent).toMatch(/2/);
  });

  it('bei >2 Toasts bleiben die NEUESTEN sichtbar (die dem Auslöser am nächsten stehen)', () => {
    montiere();
    act(() => {
      melde('Fehler A', { ton: 'fehler' });
      melde('Fehler B', { ton: 'fehler' });
      melde('Fehler C', { ton: 'fehler' });
    });
    const texte = Array.from(container!.querySelectorAll('.k-meldung-text')).map((el) => el.textContent);
    expect(texte).toEqual(['Fehler B', 'Fehler C']);
  });
});
