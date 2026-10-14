// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { TexturStufe2 } from '../src/modules/vis/island/inhalte/textur';
import { texturMaterialOptionen } from '../src/modules/vis/textur-material';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// jsdom kennt `URL.createObjectURL`/`revokeObjectURL` NICHT (bekannte Lücke,
// s. `node-canvas-render-done.test.tsx`) — hier mit ZAEHLER statt einer
// festen Zeichenkette, weil eine Probe unten zwei AUFEINANDERFOLGENDE
// Aufrufe auf Verschiedenheit prueft; ein fester Stub liesse sie falsch
// gruen aussehen, egal ob der Code wirklich zwei URLs vergibt.
if (!('createObjectURL' in URL)) {
  let zaehler = 0;
  Object.assign(URL, {
    createObjectURL: () => `blob:stub-${zaehler++}`,
    revokeObjectURL: () => undefined,
  });
}

/**
 * Abnahmezeile 6 — «Textur-Knopf» (P16, `docs/V016-SPEZ.md` Zeile 246).
 *
 * Rendert über `createRoot`/`act`/`dispatchEvent` (Muster
 * `w2-belichtung-ueberlebt.test.tsx`/`a10-uebernahme-oberflaeche.test.tsx`,
 * kein `@testing-library/react` in diesem Workspace).
 *
 * Was geprüft wird: OHNE Klick zeigt die Fläche ehrlich «noch keine
 * Bildkarten» (Regel 5, `UI-REGELN.md`) und KEIN Bild — sonst wäre ein
 * gezeigtes Bild kein Beleg für den Knopf, sondern ein Zufallstreffer. Nach
 * dem Klick liegen ZWEI Bilder da (Farbe, Rauheit) mit `blob:`-Quelle und
 * einem Lade-Link je Karte.
 */

let container: HTMLDivElement | null = null;
let root: Root | null = null;

function zeichne(): HTMLDivElement {
  if (root) act(() => root!.unmount());
  if (container) container.remove();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<TexturStufe2 />));
  return container;
}

function finde(c: HTMLDivElement, testid: string): HTMLElement | null {
  return c.querySelector(`[data-testid="${testid}"]`);
}

afterEach(() => {
  if (root) { act(() => root!.unmount()); root = null; }
  if (container) { container.remove(); container = null; }
});

describe('Textur-Knopf — Auswahlfeld', () => {
  it('bietet genau die Materialien mit echtem Rezept an (`texturMaterialOptionen()`)', () => {
    const c = zeichne();
    const liste = finde(c, 'island-textur-material') as HTMLSelectElement;
    expect(liste).not.toBeNull();
    const erwartet = texturMaterialOptionen().map((m) => m.key);
    expect([...liste.options].map((o) => o.value)).toEqual(erwartet);
  });

  it('vor jedem Klick: ehrlich «noch keine Bildkarten», kein Bild im DOM (Gegenprobe zuerst)', () => {
    const c = zeichne();
    expect(finde(c, 'island-textur-leer')).not.toBeNull();
    expect(finde(c, 'island-textur-vorschau')).toBeNull();
    expect(c.querySelectorAll('img').length).toBe(0);
  });
});

describe('Textur-Knopf — «Bildkarten erzeugen»', () => {
  it('zeigt danach zwei Bilder (Farbe, Rauheit) mit `blob:`-Quelle und je einem Lade-Link', () => {
    const c = zeichne();
    act(() => {
      finde(c, 'island-textur-erzeugen')!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(finde(c, 'island-textur-leer')).toBeNull();
    const farbe = finde(c, 'island-textur-farbe') as HTMLImageElement;
    const rauheit = finde(c, 'island-textur-rauheit') as HTMLImageElement;
    expect(farbe.src.startsWith('blob:'), farbe.src).toBe(true);
    expect(rauheit.src.startsWith('blob:'), rauheit.src).toBe(true);
    expect(farbe.src).not.toBe(rauheit.src);
    expect((finde(c, 'island-textur-farbe-laden') as HTMLAnchorElement).download).toMatch(/farbe\.png$/);
    expect((finde(c, 'island-textur-rauheit-laden') as HTMLAnchorElement).download).toMatch(/rauheit\.png$/);
  });

  it('der Hinweis nennt das gerechnete Rezept — nicht fest eingetippt, sondern das der Wahl', () => {
    const c = zeichne();
    const liste = finde(c, 'island-textur-material') as HTMLSelectElement;
    const holzOption = texturMaterialOptionen().find((m) => m.sia === 'holz');
    expect(holzOption, 'Testvoraussetzung: es gibt ein Holz-Material im Katalog').toBeDefined();
    act(() => {
      liste.value = holzOption!.key;
      liste.dispatchEvent(new Event('change', { bubbles: true }));
    });
    act(() => {
      finde(c, 'island-textur-erzeugen')!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(finde(c, 'island-textur-hinweis')!.textContent).toContain('holz');
  });

  it('der Hinweis zeigt keine liegengebliebenen Markdown-Backticks im Fliesstext (Gegenpruefung Mangel 3, Zeile ~151)', () => {
    const c = zeichne();
    act(() => {
      finde(c, 'island-textur-erzeugen')!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    // Woertliche Backticks wie „`derive/textur.ts`" wirken im UI-Fliesstext
    // wie ein stehengebliebener Code-Verweis aus Markdown — kein Verstoss
    // gegen die fuenf UI-Regeln selbst, aber vor Freigabe zu bereinigen.
    expect(finde(c, 'island-textur-hinweis')!.textContent).not.toContain('`');
  });

  it('ein zweiter Klick raeumt die vorige `blob:`-URL ab (kein Leck) und ersetzt sie', () => {
    const c = zeichne();
    const revoked: string[] = [];
    const echtRevoke = URL.revokeObjectURL.bind(URL);
    URL.revokeObjectURL = (u: string) => { revoked.push(u); echtRevoke(u); };
    try {
      act(() => finde(c, 'island-textur-erzeugen')!.dispatchEvent(new MouseEvent('click', { bubbles: true })));
      const ersteFarbe = (finde(c, 'island-textur-farbe') as HTMLImageElement).src;
      act(() => finde(c, 'island-textur-erzeugen')!.dispatchEvent(new MouseEvent('click', { bubbles: true })));
      const zweiteFarbe = (finde(c, 'island-textur-farbe') as HTMLImageElement).src;
      expect(zweiteFarbe).not.toBe(ersteFarbe);
      expect(revoked).toContain(ersteFarbe);
    } finally {
      URL.revokeObjectURL = echtRevoke;
    }
  });
});
