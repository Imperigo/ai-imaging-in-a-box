// @vitest-environment jsdom
import { act, useState } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { useRollfokus, type UseRollfokusOptionen } from '../src/rollfokus';

// Gleiches Muster wie overlay-schliessen.test.tsx: ohne dieses Flag warnt
// React bei jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * `useRollfokus` (P-g / Tastatur-Rückgrat) — Regressionsschutz für die
 * EINE-`tabIndex=0`-Garantie, Pfeiltasten-Wandern (beide Ausrichtungen),
 * Home/End, `umlaufend`, dynamisch wechselnde Gruppengrösse und den
 * SSR-Fall (`renderToStaticMarkup`, kein DOM nötig).
 *
 * Testkomponente: eine Reihe von Buttons, jeder trägt `tabIndexFuer(i)` und
 * ruft `onKeyDown` mit seinem eigenen Index.
 */

function Gruppe({ anzahl, optionen }: { anzahl: number; optionen?: UseRollfokusOptionen }) {
  const rf = useRollfokus(anzahl, optionen);
  return (
    <div data-testid="gruppe">
      {Array.from({ length: anzahl }, (_, i) => (
        <button
          key={i}
          type="button"
          data-testid={`glied-${i}`}
          tabIndex={rf.tabIndexFuer(i)}
          onKeyDown={(e) => rf.onKeyDown(e, i)}
        >
          Glied {i}
        </button>
      ))}
    </div>
  );
}

/** Deckt den dynamischen Fall ab: eine Elternkomponente, deren `anzahl` sich
 *  per Knopfdruck ändert (Filter/bedingtes Rendern). */
function GruppeMitSchrumpfung() {
  const [anzahl, setAnzahl] = useState(4);
  return (
    <div>
      <button type="button" data-testid="schrumpfe" onClick={() => setAnzahl(2)}>
        Schrumpfen
      </button>
      <Gruppe anzahl={anzahl} />
    </div>
  );
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function montiere(anzahl: number, optionen?: UseRollfokusOptionen): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<Gruppe anzahl={anzahl} {...(optionen !== undefined ? { optionen } : {})} />);
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

/** Prüft die EINE-`tabIndex=0`-Garantie: genau ein Glied trägt `tabIndex=0`,
 *  gibt dessen Index zurück. Wirft, wenn 0 oder ≥2 Glieder `0` tragen — der
 *  falsifizierbare Fehlerfall dieses Bausteins. */
function pruefeGenauEinenAktiven(anzahl: number): number {
  const nullTraeger: number[] = [];
  for (let i = 0; i < anzahl; i++) {
    const el = container!.querySelector(`[data-testid="glied-${i}"]`) as HTMLButtonElement;
    if (el.tabIndex === 0) nullTraeger.push(i);
    else expect(el.tabIndex).toBe(-1);
  }
  expect(nullTraeger.length).toBe(1);
  return nullTraeger[0]!;
}

function pfeil(el: Element, key: string, shiftKey = false): void {
  act(() => {
    el.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, shiftKey }));
  });
}

describe('useRollfokus — Struktur (SSR, kein DOM)', () => {
  it('renderToStaticMarkup: genau ein Glied trägt tabIndex=0 (initial Index 0)', () => {
    const html = renderToStaticMarkup(<Gruppe anzahl={5} />);
    const nullTreffer = [...html.matchAll(/tabindex="0"/g)];
    const minusEinsTreffer = [...html.matchAll(/tabindex="-1"/g)];
    expect(nullTreffer.length).toBe(1);
    expect(minusEinsTreffer.length).toBe(4);
  });

  it('anfangsIndex verschiebt, welches Glied initial tabIndex=0 trägt', () => {
    const html = renderToStaticMarkup(<Gruppe anzahl={5} optionen={{ anfangsIndex: 2 }} />);
    // Glied 2 ist der dritte Button im Markup — grob geprüft über die
    // Reihenfolge der tabindex-Attribute selbst (SSR hat kein DOM zum Abfragen).
    const attribute = [...html.matchAll(/tabindex="(-?\d)"/g)].map((m) => m[1]);
    expect(attribute).toEqual(['-1', '-1', '0', '-1', '-1']);
  });
});

describe('useRollfokus — Pfeiltasten waagrecht (Default)', () => {
  it('ArrowRight wandert um eins vor, ArrowLeft um eins zurück', () => {
    montiere(4);
    expect(pruefeGenauEinenAktiven(4)).toBe(0);

    const glied0 = container!.querySelector('[data-testid="glied-0"]')!;
    pfeil(glied0, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(4)).toBe(1);

    const glied1 = container!.querySelector('[data-testid="glied-1"]')!;
    pfeil(glied1, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(4)).toBe(2);

    const glied2 = container!.querySelector('[data-testid="glied-2"]')!;
    pfeil(glied2, 'ArrowLeft');
    expect(pruefeGenauEinenAktiven(4)).toBe(1);
  });

  it('ArrowUp/ArrowDown lösen in waagrechter Ausrichtung NICHTS aus', () => {
    montiere(3);
    const glied0 = container!.querySelector('[data-testid="glied-0"]')!;
    pfeil(glied0, 'ArrowDown');
    expect(pruefeGenauEinenAktiven(3)).toBe(0);
    pfeil(glied0, 'ArrowUp');
    expect(pruefeGenauEinenAktiven(3)).toBe(0);
  });

  it('ohne umlaufend bleibt ArrowRight am letzten Glied stehen', () => {
    montiere(3);
    const glied0 = container!.querySelector('[data-testid="glied-0"]')!;
    pfeil(glied0, 'ArrowRight');
    pfeil(container!.querySelector('[data-testid="glied-1"]')!, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(3)).toBe(2);
    pfeil(container!.querySelector('[data-testid="glied-2"]')!, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(3)).toBe(2); // bleibt stehen, kein Umlauf
  });

  it('umlaufend: true lässt ArrowRight am letzten Glied zum ersten springen', () => {
    montiere(3, { umlaufend: true });
    const glied0 = container!.querySelector('[data-testid="glied-0"]')!;
    pfeil(glied0, 'ArrowRight');
    pfeil(container!.querySelector('[data-testid="glied-1"]')!, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(3)).toBe(2);
    pfeil(container!.querySelector('[data-testid="glied-2"]')!, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(3)).toBe(0); // Umlauf zurück zum ersten

    // Und rückwärts vom ersten zum letzten:
    pfeil(container!.querySelector('[data-testid="glied-0"]')!, 'ArrowLeft');
    expect(pruefeGenauEinenAktiven(3)).toBe(2);
  });

  it('Home springt zum ersten, End zum letzten Glied', () => {
    montiere(5);
    pfeil(container!.querySelector('[data-testid="glied-0"]')!, 'ArrowRight');
    pfeil(container!.querySelector('[data-testid="glied-1"]')!, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(5)).toBe(2);

    pfeil(container!.querySelector('[data-testid="glied-2"]')!, 'End');
    expect(pruefeGenauEinenAktiven(5)).toBe(4);

    pfeil(container!.querySelector('[data-testid="glied-4"]')!, 'Home');
    expect(pruefeGenauEinenAktiven(5)).toBe(0);
  });

  it('andere Tasten (Enter, Tab, Escape) lösen keine Bewegung aus', () => {
    montiere(3);
    const glied0 = container!.querySelector('[data-testid="glied-0"]')!;
    pfeil(glied0, 'Enter');
    pfeil(glied0, 'Tab');
    pfeil(glied0, 'Escape');
    expect(pruefeGenauEinenAktiven(3)).toBe(0);
  });
});

describe('useRollfokus — Pfeiltasten senkrecht', () => {
  it('ArrowDown/ArrowUp bewegen, ArrowRight/ArrowLeft lösen NICHTS aus', () => {
    montiere(3, { ausrichtung: 'senkrecht' });
    const glied0 = container!.querySelector('[data-testid="glied-0"]')!;
    pfeil(glied0, 'ArrowRight');
    expect(pruefeGenauEinenAktiven(3)).toBe(0);

    pfeil(glied0, 'ArrowDown');
    expect(pruefeGenauEinenAktiven(3)).toBe(1);

    pfeil(container!.querySelector('[data-testid="glied-1"]')!, 'ArrowUp');
    expect(pruefeGenauEinenAktiven(3)).toBe(0);
  });
});

describe('useRollfokus — dynamisch wechselnde Anzahl', () => {
  it('eine schrumpfende Gruppe hält die EINE-tabIndex=0-Garantie, auch wenn der aktive Index wegfällt', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(<GruppeMitSchrumpfung />);
    });

    // Zum letzten Glied (Index 3) wandern, dann auf 2 Glieder schrumpfen.
    pfeil(container!.querySelector('[data-testid="glied-0"]')!, 'End');
    expect(pruefeGenauEinenAktiven(4)).toBe(3);

    const schrumpfe = container!.querySelector('[data-testid="schrumpfe"]') as HTMLButtonElement;
    act(() => {
      schrumpfe.click();
    });

    // aktiverIndex war 3, anzahl ist jetzt 2 (Indizes 0/1) — der Hook klemmt
    // auf den letzten gültigen Index, NIE ausserhalb des Bereichs.
    expect(pruefeGenauEinenAktiven(2)).toBe(1);
  });
});

describe('useRollfokus — falsifizierbarer Fehlerfall', () => {
  it('nach JEDEM simulierten Tastendruck bleibt es bei GENAU EINEM tabIndex=0 (nie zwei, nie null)', () => {
    montiere(6, { umlaufend: true });
    const tasten = ['ArrowRight', 'ArrowRight', 'End', 'ArrowLeft', 'Home', 'ArrowRight', 'ArrowLeft', 'ArrowLeft'];
    for (const taste of tasten) {
      const aktuellerIndex = pruefeGenauEinenAktiven(6);
      const el = container!.querySelector(`[data-testid="glied-${aktuellerIndex}"]`)!;
      pfeil(el, taste);
      // Die eigentliche Prüfung: würde die Implementierung je zwei Glieder
      // gleichzeitig auf tabIndex=0 setzen (oder keines), wirft dies HIER,
      // nicht erst am Testende — jeder einzelne Schritt ist ein Fehlerfall
      // für sich.
      pruefeGenauEinenAktiven(6);
    }
  });
});
