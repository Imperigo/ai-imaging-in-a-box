// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { KSelect } from '../src/select';

// Gleiches Muster wie komponenten.test.tsx/overlay-schliessen.test.tsx: ohne
// dieses Flag warnt React bei jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * Regressionsschutz für den Befund vom 23.08.2026
 * (`docs/BEFUND-SELECT-SCHLIESST-SICH-SELBST.md`): der «Aktive Option in
 * Sicht halten»-Effekt in `select.tsx` rief `el.scrollIntoView({block:
 * 'nearest'})` auf der aktiven Option auf. Das scrollt JEDEN scrollbaren
 * Vorfahren mit, nicht nur die Listbox — steht der KSelect-Trigger in einem
 * scrollbaren Behälter, landet dessen `scroll`-Ereignis in `schliesseScroll`
 * (select.tsx:182ff) und schliesst das Popup mit seinem eigenen Öffnen.
 *
 * WICHTIGE EINSCHRÄNKUNG (Nachmessung 23.08.2026, im Bau-Bericht ausführlich
 * belegt): dieser Effekt-Fix ist eine ECHTE, verifizierte Reparatur seiner
 * eigenen Ursache — behebt aber NICHT allein den konkreten E2E-Fall
 * `e2e/cloud-login.spec.ts:79`/`:104`. Dort dominiert ein ZWEITER,
 * unabhängiger Mechanismus: der Browser scrollt `.kp-einstellungen`
 * NATIV beim Fokussieren jedes dort tief sitzenden Steuerelements (auch
 * eines gewöhnlichen `<input>`, nicht nur KSelect) — teils sofort (dagegen
 * hilft der zweite Fix unten, `onMouseDown` + `focus({preventScroll:true})`),
 * teils ~200–300ms VERZÖGERT und dabei nachweislich immun gegen
 * `preventScroll` (12 isolierte Chromium-Diagnosen, u. a. mit
 * Monkeypatches auf `scrollTop`/`focus`, Entfernen von
 * `aria-activedescendant`/`aria-controls`/`aria-expanded`, Abschalten von
 * `overflow-anchor`, einer Blase-Ausweichen-Prüfung (`--kp-ausweich` bleibt
 * unverändert) und einem KOMPLETT Kosmo-freien Minimal-Repro, das NICHT
 * scrollt). Dieser verzögerte Anteil liegt ausserhalb dessen, was
 * `select.tsx` allein beheben kann, ohne eine weitere Ausnahme in
 * `schliesseScroll` einzuführen (ausdrücklich nicht erwünscht) oder
 * `KosmoPanel.tsx`/`kosmo-panel.css` anzufassen (ausserhalb des
 * Dateikreises dieses Auftrags) — s. Bau-Bericht für die volle Kette.
 *
 * jsdom hat KEIN echtes Layout — offsetTop/offsetHeight/clientHeight sind
 * ohne Fixture immer 0, und `HTMLElement.prototype.scrollIntoView` ist in
 * jsdom serienmässig gar nicht implementiert (daher die frühere
 * `typeof … === 'function'`-Wache im alten Code). Test A beweist darum nur,
 * was jsdom ehrlich hergibt: der reparierte Effekt ruft `scrollIntoView`
 * NIE mehr auf (das war der Mechanismus, der Vorfahren mitzieht), und beim
 * Öffnen erreicht kein `scroll`-Ereignis einen Vorfahren oder `window`.
 *
 * Die drei `nearest`-Fälle selbst (Option oberhalb/unterhalb/schon
 * sichtbar) lassen sich in jsdom nicht am echten Pixelwert nachweisen, weil
 * es kein Layout misst — Tests B–D bauen das Layout darum GEZIELT mit
 * `Object.defineProperty` nach (offsetTop/offsetHeight/clientHeight/
 * scrollTop je Element überschrieben) und prüfen exakt die neue
 * `liste.scrollTop`-Rechnung aus select.tsx. Das ist kein echter
 * Layout-Beweis, sondern ein Beweis der RECHNUNG.
 *
 * Test E prüft den ZWEITEN Fix (mousedown → preventDefault + gezielter
 * `focus({preventScroll:true})`) — auch das nur auf JS-Ebene (dass der
 * richtige Aufruf mit der richtigen Option passiert), NICHT auf die
 * tatsächliche Browser-Scroll-Unterdrückung (die jsdom nicht simuliert).
 *
 * P-ANKER-Nachtrag (23.08.2026, `docs/URTEIL-SCHLIESS-WACHE-2026-08-23.md`,
 * W5′): die untenstehende zweite `describe`-Gruppe prüft die NEUE Wache —
 * bei Scroll/Resize wird die Popup-Lage aus dem Trigger-Rechteck neu
 * berechnet statt geschlossen; geschlossen wird nur noch, wenn der Trigger
 * nach `triggerSichtbar` (select.tsx) vollständig unsichtbar ist. jsdom
 * berechnet `requestAnimationFrame` real (kein Polyfill nötig, s.
 * `apps/kosmo-orbit/test/zeiger-messstand.test.ts`, das denselben Global
 * spied) — die rAF-Drosselung selbst ist darum ECHT geprüft. Was jsdom NICHT
 * bietet, ist echtes Layout: `getBoundingClientRect` wird darum je Test
 * gezielt mit `vi.spyOn(...).mockReturnValue(...)` überschrieben, und ohne
 * eine geklippte Vorfahren-Kette bleibt der Sichtbarkeits-Check auf den
 * Viewport-Rand reduziert (window.innerWidth/-Height). Die eigentliche
 * ENTSCHEIDUNG zwischen den beiden Sichtbarkeits-Kandidaten (Rechteck-Schnitt
 * vs. `elementFromPoint`) ist an ECHTEN Behältern (`.kp-einstellungen`,
 * `.isl-fenster`, Viewport-Clip) mit einer eigenständigen Playwright-Messung
 * belegt, nicht hier — Messprotokoll und Zahlen im Bau-Bericht dieses
 * Auftrags. Diese Tests hier beweisen die RECHNUNG/den Kontrollfluss
 * (rAF-Drosselung, Neuberechnung vs. Schliessen, Listbox-Eigenscroll-Skip),
 * nicht die geometrische Richtigkeit gegen echtes CSS-Layout — dafür ist
 * `e2e/p-anker-*.spec.ts` zuständig.
 */

/** Ersetzt `getBoundingClientRect` eines Elements durch einen festen,
 * beobachtbaren Rückgabewert (jsdom liefert ohne echtes Layout sonst immer
 * ein Nullrechteck). */
function fakeRect(
  el: HTMLElement,
  rect: { top: number; bottom: number; left: number; right: number },
): void {
  const width = rect.right - rect.left;
  const height = rect.bottom - rect.top;
  vi.spyOn(el, 'getBoundingClientRect').mockReturnValue({
    ...rect,
    width,
    height,
    x: rect.left,
    y: rect.top,
    toJSON: () => ({}),
  } as DOMRect);
}

async function naechsterFrame(): Promise<void> {
  await act(async () => {
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => resolve());
    });
  });
}

function fakeLayout(
  el: HTMLElement,
  werte: Partial<Record<'offsetTop' | 'offsetHeight' | 'clientHeight', number>>,
): void {
  for (const [schluessel, wert] of Object.entries(werte)) {
    Object.defineProperty(el, schluessel, { value: wert, configurable: true });
  }
}

/** Ersetzt `scrollTop` durch eine echte, beobachtbare Fake-Property (jsdom
 * ignoriert Zuweisungen sonst stillschweigend, weil es nicht wirklich
 * scrollt). Gibt den aktuellen Wert UND die Anzahl der Zuweisungen zurück —
 * «nichts bewegt sich» heisst: der Setter wird nicht einmal aufgerufen. */
function fakeScrollTop(el: HTMLElement, start = 0): { wert: () => number; anzahlSetzen: () => number } {
  let wert = start;
  let anzahl = 0;
  Object.defineProperty(el, 'scrollTop', {
    configurable: true,
    get: () => wert,
    set: (v: number) => {
      wert = v;
      anzahl += 1;
    },
  });
  return { wert: () => wert, anzahlSetzen: () => anzahl };
}

function druecke(ziel: HTMLElement, key: string): void {
  act(() => {
    ziel.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
  });
}

const SCROLL_INTO_VIEW_DESC = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'scrollIntoView');

let root: Root | null = null;
let host: HTMLElement | null = null;

function montiere(knoten: Parameters<Root['render']>[0], hostElement?: HTMLElement): HTMLElement {
  host = hostElement ?? document.createElement('div');
  if (!host.isConnected) document.body.appendChild(host);
  root = createRoot(host);
  act(() => {
    root!.render(knoten);
  });
  return host;
}

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (host) {
    host.remove();
    host = null;
  }
  if (SCROLL_INTO_VIEW_DESC) {
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', SCROLL_INTO_VIEW_DESC);
  } else {
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).scrollIntoView;
  }
  vi.restoreAllMocks();
});

describe('KSelect: der Öffnen-Scroll schliesst sich nicht mehr selbst (Befund 23.08.2026)', () => {
  it('Öffnen ruft nie scrollIntoView auf und löst kein scroll-Ereignis auf Vorfahr oder window aus', () => {
    const scrollIntoViewSpion = vi.fn();
    // jsdom implementiert scrollIntoView normalerweise gar nicht — hier
    // GEZIELT gesetzt, damit ein Aufruf überhaupt beobachtbar wäre. Bliebe
    // die alte `scrollIntoView`-Zeile stehen, würde dieser Spion feuern.
    HTMLElement.prototype.scrollIntoView = scrollIntoViewSpion;

    const vorfahr = document.createElement('div');
    vorfahr.className = 'kp-einstellungen'; // Nachbau des echten Panel-Behälters.
    document.body.appendChild(vorfahr);
    const vorfahrScrollEvents: Event[] = [];
    vorfahr.addEventListener('scroll', (e) => vorfahrScrollEvents.push(e));
    const windowScrollEvents: Event[] = [];
    const windowListener = (e: Event) => windowScrollEvents.push(e);
    window.addEventListener('scroll', windowListener, { capture: true });

    try {
      montiere(
        <KSelect data-testid="modell-select" value="a" onChange={() => {}}>
          <option value="a">Alpha</option>
          <option value="b">Beta</option>
          <option value="c">Gamma</option>
        </KSelect>,
        vorfahr,
      );

      const trigger = vorfahr.querySelector('[data-testid="modell-select"]') as HTMLButtonElement;
      expect(trigger).not.toBeNull();
      act(() => {
        trigger.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      });

      // Popup ist wirklich offen — sonst wäre "kein Scroll" ein Fehlalarm.
      expect(document.querySelector('[data-testid="modell-select-popup"]')).not.toBeNull();
      expect(scrollIntoViewSpion).not.toHaveBeenCalled();
      expect(vorfahrScrollEvents).toEqual([]);
      expect(windowScrollEvents).toEqual([]);
    } finally {
      window.removeEventListener('scroll', windowListener, { capture: true } as EventListenerOptions);
    }
  });

  it('Nachbau der Rechnung — Option UNTERHALB des sichtbaren Bereichs holt die Listbox nach unten', () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
        <option value="c">C</option>
        <option value="d">D</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));

    const liste = document.querySelector('[data-testid="s-popup"]') as HTMLElement;
    const optionen = [0, 1, 2, 3].map(
      (i) => document.querySelector(`[data-testid="s-popup"] [data-index="${i}"]`) as HTMLElement,
    );
    fakeLayout(liste, { clientHeight: 100 });
    const scroll = fakeScrollTop(liste, 0);
    optionen.forEach((el, i) => fakeLayout(el, { offsetTop: i * 40, offsetHeight: 40 }));

    // aktivIndex startet bei 0 (Wert 'a'). Zwei ArrowDown → Index 2:
    // elOben=80, elUnten=120 > sichtUnten(0+100=100) → muss auf 20 scrollen.
    druecke(trigger, 'ArrowDown');
    druecke(trigger, 'ArrowDown');
    expect(scroll.wert()).toBe(20);

    // Ein weiterer ArrowDown → Index 3: elOben=120, elUnten=160 >
    // sichtUnten(20+100=120) → muss auf 60 scrollen.
    druecke(trigger, 'ArrowDown');
    expect(scroll.wert()).toBe(60);
  });

  it('Nachbau der Rechnung — Option OBERHALB des sichtbaren Bereichs holt die Listbox nach oben', () => {
    montiere(
      <KSelect data-testid="s" value="f" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
        <option value="c">C</option>
        <option value="d">D</option>
        <option value="e">E</option>
        <option value="f">F</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    // Öffnet mit aktivIndex=5 (Wert 'f').
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));

    const liste = document.querySelector('[data-testid="s-popup"]') as HTMLElement;
    const optionen = [0, 1, 2, 3, 4, 5].map(
      (i) => document.querySelector(`[data-testid="s-popup"] [data-index="${i}"]`) as HTMLElement,
    );
    fakeLayout(liste, { clientHeight: 100 });
    // Simuliert: die Liste steht bereits weit unten gescrollt (Index 5 war sichtbar).
    const scroll = fakeScrollTop(liste, 200);
    optionen.forEach((el, i) => fakeLayout(el, { offsetTop: i * 40, offsetHeight: 40 }));

    // ArrowUp → Index 4: elOben=160 < sichtOben(200) → JA, nach oben holen.
    druecke(trigger, 'ArrowUp');
    expect(scroll.wert()).toBe(160);

    // ArrowUp → Index 3: elOben=120 < sichtOben(160) → weiter nach oben.
    druecke(trigger, 'ArrowUp');
    expect(scroll.wert()).toBe(120);
  });

  it('Nachbau der Rechnung — Option bereits sichtbar: scrollTop wird NICHT einmal angefasst (Bedeutung von "nearest")', () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
        <option value="c">C</option>
        <option value="d">D</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));

    const liste = document.querySelector('[data-testid="s-popup"]') as HTMLElement;
    const optionen = [0, 1, 2, 3].map(
      (i) => document.querySelector(`[data-testid="s-popup"] [data-index="${i}"]`) as HTMLElement,
    );
    // Grosszügige Höhe (200) — alle vier Optionen (0..160) passen vollständig hinein.
    fakeLayout(liste, { clientHeight: 200 });
    const scroll = fakeScrollTop(liste, 0);
    optionen.forEach((el, i) => fakeLayout(el, { offsetTop: i * 40, offsetHeight: 40 }));

    druecke(trigger, 'ArrowDown');
    druecke(trigger, 'ArrowDown');
    druecke(trigger, 'ArrowDown');

    // Kein einziger Aufruf des Setters — nicht nur "Wert am Ende gleich",
    // sondern es wurde nie versucht, etwas zu bewegen.
    expect(scroll.anzahlSetzen()).toBe(0);
    expect(scroll.wert()).toBe(0);
  });

  it('mousedown auf dem Trigger: preventDefault + gezielter focus({preventScroll:true}) (zweiter Fix, JS-Ebene)', () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    const focusSpion = vi.spyOn(trigger, 'focus');

    let defaultVerhindert = false;
    // WICHTIG: React (17+) hängt seinen Handler NICHT am Element selbst,
    // sondern delegiert am Root-Container — in der Bubble-Phase feuert der
    // darum SPÄTER als ein Listener direkt am Ziel. Auf `document` lauschen
    // (bubbelt zuletzt dorthin), damit dieser Check WIRKLICH NACH select.tsx
    // läuft, statt eine falsche Reihenfolge vorzutäuschen.
    document.addEventListener('mousedown', (e) => {
      defaultVerhindert = e.defaultPrevented;
    });

    act(() => {
      trigger.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    });

    expect(defaultVerhindert).toBe(true);
    expect(focusSpion).toHaveBeenCalledWith({ preventScroll: true });
  });
});

describe('KSelect: P-ANKER — Scroll berechnet die Popup-Lage neu statt zu schliessen (Urteil 23.08.2026)', () => {
  it('Scroll bei sichtbarem Trigger: kein synchrones Schliessen, nach EINEM rAF steht die neue Lage', async () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    fakeRect(trigger, { top: 100, bottom: 130, left: 20, right: 220 });
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));

    const popupVorScroll = document.querySelector('[data-testid="s-popup"]') as HTMLElement;
    expect(popupVorScroll).not.toBeNull();
    expect(popupVorScroll.style.top).toBe('132px'); // trigger.bottom(130) + 2

    // Der Trigger "wandert" — genau das simuliert einen scrollbaren Vorfahren,
    // der beim Scroll seine Kinder verschiebt, ohne dass der Trigger dabei
    // den sichtbaren Bereich verlässt.
    fakeRect(trigger, { top: 40, bottom: 70, left: 20, right: 220 });

    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    // Synchron direkt nach dem Ereignis darf NICHTS geschehen sein — das ist
    // der Kern des Urteils: keine Zustandssetzung ohne rAF-Drosselung.
    expect(document.querySelector('[data-testid="s-popup"]')).not.toBeNull();
    expect((document.querySelector('[data-testid="s-popup"]') as HTMLElement).style.top).toBe('132px');

    await naechsterFrame();

    const popupNachScroll = document.querySelector('[data-testid="s-popup"]');
    expect(popupNachScroll).not.toBeNull(); // weiterhin offen — der Trigger ist sichtbar
    expect((popupNachScroll as HTMLElement).style.top).toBe('72px'); // neuer trigger.bottom(70) + 2
  });

  it('Trigger vollständig ausserhalb des Viewports: Popup schliesst nach dem Frame (Abnahme 4)', async () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    fakeRect(trigger, { top: 100, bottom: 130, left: 20, right: 220 });
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(document.querySelector('[data-testid="s-popup"]')).not.toBeNull();

    // Trigger komplett aus dem Viewport gescrollt (negative Koordinaten) —
    // "der Trigger verlässt den Clip" (Urteil, Abnahme 4).
    fakeRect(trigger, { top: -200, bottom: -170, left: 20, right: 220 });
    act(() => {
      window.dispatchEvent(new Event('scroll'));
    });
    await naechsterFrame();

    expect(document.querySelector('[data-testid="s-popup"]')).toBeNull();
  });

  it('rAF-Drosselung: zwei scroll-Ereignisse vor dem nächsten Frame melden nur EINEN rAF an', async () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    fakeRect(trigger, { top: 100, bottom: 130, left: 20, right: 220 });
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));

    const rafSpion = vi.spyOn(window, 'requestAnimationFrame');
    act(() => {
      window.dispatchEvent(new Event('scroll'));
      window.dispatchEvent(new Event('scroll'));
      window.dispatchEvent(new Event('resize'));
    });
    // Drei Ereignisse, aber nur EIN angemeldeter Frame — das ist die
    // rAF-Drosselung (Urteil-Preis 3: kein Layout-Thrash je Ereignis).
    expect(rafSpion).toHaveBeenCalledTimes(1);

    await naechsterFrame();
    rafSpion.mockRestore();
  });

  it('Scroll INNERHALB der Listbox meldet keinen rAF an (unverändert seit dem alten Code)', () => {
    montiere(
      <KSelect data-testid="s" value="a" onChange={() => {}}>
        <option value="a">A</option>
        <option value="b">B</option>
      </KSelect>,
    );
    const trigger = host!.querySelector('[data-testid="s"]') as HTMLButtonElement;
    fakeRect(trigger, { top: 100, bottom: 130, left: 20, right: 220 });
    act(() => trigger.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    const popup = document.querySelector('[data-testid="s-popup"]') as HTMLElement;

    const rafSpion = vi.spyOn(window, 'requestAnimationFrame');
    act(() => {
      popup.dispatchEvent(new Event('scroll', { bubbles: true }));
    });
    expect(rafSpion).not.toHaveBeenCalled();
    rafSpion.mockRestore();
  });
});
