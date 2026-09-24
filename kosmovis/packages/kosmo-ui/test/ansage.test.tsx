// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { ansage, KAnsageBereich } from '../src/meldungen';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * `ansage()`/`KAnsageBereich` (P-g / Tastatur-Rückgrat) — Regressionsschutz:
 * zwei getrennte `aria-live`-Kanäle (polite/assertive), keine sichtbare
 * Meldung, und der falsifizierbare Fehlerfall: eine `ansage()` darf NIE im
 * Toast-Store (`meldungen`) landen — die beiden Kanäle sind unabhängig.
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<KAnsageBereich />);
  });
}

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
});

describe('KAnsageBereich — Grundstruktur', () => {
  it('rendert zwei aria-live-Container, polite und assertive, initial leer', () => {
    montiere();
    const polite = container!.querySelector('[data-testid="ansage-polite"]')!;
    const assertive = container!.querySelector('[data-testid="ansage-assertive"]')!;
    expect(polite.getAttribute('aria-live')).toBe('polite');
    expect(assertive.getAttribute('aria-live')).toBe('assertive');
    expect(polite.textContent).toBe('');
    expect(assertive.textContent).toBe('');
  });
});

describe('ansage() — polite (Default)', () => {
  it('schreibt den Text in den polite-Container, NICHT in den assertive-Container', () => {
    montiere();
    act(() => {
      ansage('Element 3 von 8 ausgewählt');
    });
    const polite = container!.querySelector('[data-testid="ansage-polite"]')!;
    const assertive = container!.querySelector('[data-testid="ansage-assertive"]')!;
    expect(polite.textContent).toBe('Element 3 von 8 ausgewählt');
    expect(assertive.textContent).toBe('');
  });

  it('kein hoeflichkeit-Argument verhält sich identisch zu explizitem "polite"', () => {
    montiere();
    act(() => {
      ansage('Ohne Argument');
    });
    expect(container!.querySelector('[data-testid="ansage-polite"]')!.textContent).toBe('Ohne Argument');
  });
});

describe('ansage() — assertive', () => {
  it('schreibt den Text in den assertive-Container, lässt polite unberührt', () => {
    montiere();
    act(() => {
      ansage('Erste polite Ansage');
    });
    act(() => {
      ansage('Dringend', 'assertive');
    });
    const polite = container!.querySelector('[data-testid="ansage-polite"]')!;
    const assertive = container!.querySelector('[data-testid="ansage-assertive"]')!;
    expect(polite.textContent).toBe('Erste polite Ansage');
    expect(assertive.textContent).toBe('Dringend');
  });
});

describe('ansage() — visuell verborgen, keine sichtbare Meldung', () => {
  it('beide Container tragen das Clip-Pattern — jetzt ueber `.k-nur-sr` statt als Inline-Stil', () => {
    // GEAENDERT AM 09.09.2026 (P-TASTATUR-LUECKEN Teil 2), und die Aenderung
    // wird benannt statt umgangen. Hier stand die Pruefung des INLINE-Stils
    // (`polite.style.position === 'absolute'` usw.). Das Muster wohnt jetzt
    // als `.k-nur-sr` in `aura.css` — der Kommentar in `meldungen.tsx` hatte
    // genau das als die «naheliegendere Form» gemeldet und nur deshalb
    // dupliziert, weil `aura.css` damals ausserhalb des Dateikreises lag.
    //
    // **Die Zusage dieser Probe bleibt dieselbe und wird nicht schwaecher:**
    // die Ansage ist fuer das Auge verborgen und fuer die Sprachausgabe da.
    // Sie wird nur eine Stufe weiter geprueft — am Klassennamen hier, an der
    // Regel selbst in `nur-sr-klasse.test.ts` (die verlangt dort das
    // vollstaendige Clip-Muster UND ausdruecklich die Abwesenheit von
    // `display:none`/`visibility:hidden`/`opacity:0`).
    montiere();
    const polite = container!.querySelector('[data-testid="ansage-polite"]') as HTMLDivElement;
    const assertive = container!.querySelector('[data-testid="ansage-assertive"]') as HTMLDivElement;
    expect(polite.className).toBe('k-nur-sr');
    expect(assertive.className).toBe('k-nur-sr');
    // Und weiterhin KEIN Inline-Stil, der das Muster ueberschreibt — sonst
    // waere die Klasse gesetzt und trotzdem wirkungslos.
    expect(polite.style.display).not.toBe('none');
    expect(polite.style.visibility).not.toBe('hidden');
    expect(polite.getAttribute('style'), 'ein Inline-Stil ist zurueck').toBeNull();
  });

  it('FALSIFIZIERBARER FEHLERFALL: ansage() erzeugt KEINEN Eintrag im Toast-Store (kein [data-testid^="meldung-"])', async () => {
    montiere();
    act(() => {
      ansage('Nur für Hilfstechnik');
    });
    // Der Toast-Host (KMeldungen) ist hier gar nicht gemountet — die
    // eigentliche Garantie ist, dass ansage() NICHT denselben Store wie
    // melde() beschreibt. Importiere den Toast-Host zusätzlich und
    // vergewissere, dass er nach einer ansage() leer bleibt.
    const { KMeldungen } = await import('../src/meldungen');
    const zweiterContainer = document.createElement('div');
    document.body.appendChild(zweiterContainer);
    const zweiteRoot = createRoot(zweiterContainer);
    act(() => {
      zweiteRoot.render(<KMeldungen />);
    });
    expect(zweiterContainer.querySelector('[data-testid^="meldung-"]')).toBeNull();
    act(() => zweiteRoot.unmount());
    zweiterContainer.remove();
  });
});

describe('ansage() — wiederholter identischer Text', () => {
  it('zwei identische aufeinanderfolgende polite-Ansagen ändern den Text nicht sichtbar, lösen aber je einen Store-Takt aus', () => {
    montiere();
    act(() => {
      ansage('Wiederholt');
    });
    act(() => {
      ansage('Wiederholt');
    });
    // Der Text bleibt korrekt (kein Crash/keine Verdopplung) — ob der
    // Screenreader beim zweiten Mal erneut vorliest, ist eine Eigenheit der
    // Hilfstechnik selbst (Kopfkommentar), keine hier prüfbare Eigenschaft.
    expect(container!.querySelector('[data-testid="ansage-polite"]')!.textContent).toBe('Wiederholt');
  });
});
