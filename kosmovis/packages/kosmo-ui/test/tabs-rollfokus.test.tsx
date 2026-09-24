// @vitest-environment jsdom
import { act, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { KTabs, type KTabItem } from '../src/tabs';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * **P-TASTATUR-LUECKEN — die Reiterleiste kostete einen Tab-Stopp je Reiter.**
 *
 * Der Befund aus der Bestandsaufnahme: `useRollfokus` ist gebaut, und der
 * Rollout-Kommentar dort nennt `KTabs` als ERSTEN Ort — benutzt hat ihn
 * `KTabs` trotzdem nicht. Eine Leiste mit fuenf Reitern kostete fuenf
 * Tabulator-Anschlaege, und die Pfeiltasten taten nichts.
 *
 * Jeder Fall hier hat seinen Gegenfall: es reicht nicht zu zeigen, DASS ein
 * `tabIndex=0` existiert — es muss GENAU EINER sein, sonst waere der alte
 * Zustand (jeder Reiter ein Stopp) ebenfalls gruen.
 */

const ITEMS: readonly KTabItem[] = [
  { id: 'a', label: 'Eins', testid: 'tab-a' },
  { id: 'b', label: 'Zwei', testid: 'tab-b' },
  { id: 'c', label: 'Drei', testid: 'tab-c' },
];

function Leiste({ start = 'a' }: { start?: string }) {
  const [aktiv, setAktiv] = useState(start);
  return <KTabs items={ITEMS} aktiv={aktiv} onChange={setAktiv} data-testid="leiste" />;
}

let root: Root | null = null;
let wirt: HTMLDivElement | null = null;

function baue(el: React.ReactElement): HTMLDivElement {
  wirt = document.createElement('div');
  document.body.appendChild(wirt);
  root = createRoot(wirt);
  act(() => root!.render(el));
  return wirt;
}

afterEach(() => {
  if (root) act(() => root!.unmount());
  wirt?.remove();
  root = null;
  wirt = null;
});

function knoepfe(w: HTMLElement): HTMLButtonElement[] {
  return Array.from(w.querySelectorAll('[role="tab"]')) as HTMLButtonElement[];
}

function pfeil(el: HTMLElement, key: string): void {
  act(() => {
    el.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
  });
}

describe('KTabs — Rollfokus statt eines Tab-Stopps je Reiter', () => {
  it('GENAU EIN Reiter ist tabulierbar — der Kern des Befunds', () => {
    const w = baue(<Leiste />);
    const nullen = knoepfe(w).filter((b) => b.tabIndex === 0);
    expect(nullen, 'mehr oder weniger als ein Tab-Stopp').toHaveLength(1);
    expect(nullen[0]!.getAttribute('data-testid')).toBe('tab-a');
  });

  it('der Tab-Stopp sitzt beim AUSGEWAEHLTEN Reiter, nicht stur beim ersten', () => {
    // Gegenfall zum vorigen: eine Fassung, die einfach immer Index 0 mit
    // tabIndex 0 versaehe, waere oben gruen und hier rot.
    const w = baue(<Leiste start="c" />);
    const nullen = knoepfe(w).filter((b) => b.tabIndex === 0);
    expect(nullen).toHaveLength(1);
    expect(nullen[0]!.getAttribute('data-testid')).toBe('tab-c');
  });

  it('Pfeil rechts bewegt den FOKUS zum naechsten Reiter', () => {
    const w = baue(<Leiste />);
    const [a, b] = knoepfe(w);
    act(() => a!.focus());
    pfeil(a!, 'ArrowRight');
    expect(document.activeElement).toBe(b);
    expect(b!.tabIndex).toBe(0);
    expect(a!.tabIndex).toBe(-1);
  });

  it('Pfeil waehlt NICHT aus — manuelle Aktivierung, und das ist Absicht', () => {
    // Ein Reiterwechsel tauscht ganze Inhalte aus. Wer mit dem Pfeil an
    // Reitern vorbeiwandert, soll nicht jeden davon laden.
    const w = baue(<Leiste />);
    const [a, b] = knoepfe(w);
    act(() => a!.focus());
    pfeil(a!, 'ArrowRight');
    expect(document.activeElement).toBe(b);
    expect(a!.getAttribute('aria-selected'), 'der Pfeil hat ausgewaehlt').toBe('true');
    expect(b!.getAttribute('aria-selected')).toBe('false');
  });

  it('Enter/Leertaste auf dem bepfeilten Reiter waehlt ihn dann wirklich aus', () => {
    // Der Gegenbeweis zum vorigen Fall: waere die Auswahl gar nicht ueber
    // die Tastatur erreichbar, waere «manuelle Aktivierung» nur ein Name
    // fuer «geht nicht».
    const w = baue(<Leiste />);
    const [a, b] = knoepfe(w);
    act(() => a!.focus());
    pfeil(a!, 'ArrowRight');
    act(() => b!.click());
    expect(b!.getAttribute('aria-selected')).toBe('true');
    expect(a!.getAttribute('aria-selected')).toBe('false');
  });

  it('Pfeil links am Anfang laeuft um — Home und End springen an die Enden', () => {
    const w = baue(<Leiste />);
    const [a, b, c] = knoepfe(w);
    act(() => a!.focus());
    pfeil(a!, 'ArrowLeft');
    expect(document.activeElement, 'umlaufend greift nicht').toBe(c);
    pfeil(c!, 'Home');
    expect(document.activeElement).toBe(a);
    pfeil(a!, 'End');
    expect(document.activeElement).toBe(c);
    expect(b!.tabIndex).toBe(-1);
  });

  it('ein Klick nimmt den Tab-Stopp mit — sonst zeigte er danach woandershin', () => {
    const w = baue(<Leiste />);
    const [, b] = knoepfe(w);
    act(() => b!.click());
    const nullen = knoepfe(w).filter((k) => k.tabIndex === 0);
    expect(nullen).toHaveLength(1);
    expect(nullen[0]!.getAttribute('data-testid')).toBe('tab-b');
  });

  it('beim ersten Rendern wird KEIN Fokus gesetzt — sonst reisst die Leiste ihn an sich', () => {
    // Ein Effekt, der beim Mounten `focus()` ruft, holt den Fokus aus dem
    // Feld, in dem gerade jemand tippt. Genau dagegen steht das Merkzeichen
    // `tasteWarZuletzt` in der Komponente.
    const feld = document.createElement('input');
    document.body.appendChild(feld);
    feld.focus();
    expect(document.activeElement).toBe(feld);
    baue(<Leiste />);
    expect(document.activeElement, 'die Leiste hat den Fokus an sich gerissen').toBe(feld);
    feld.remove();
  });
});
