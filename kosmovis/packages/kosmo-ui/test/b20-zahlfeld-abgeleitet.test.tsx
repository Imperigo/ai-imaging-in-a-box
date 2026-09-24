// @vitest-environment jsdom
import { useState } from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { KNumberField } from '../src/field';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * B20 — `abgeleitet`: das Zahlenfeld darf die Eingabe des ANGEZEIGTEN Werts
 * nicht mehr stumm schlucken, WO der angezeigte Wert abgeleitet ist.
 *
 * DER ANLASS, gemessen und nicht vermutet (73-BEFUNDE-OHNE-BESITZER.md §18/§20):
 * das Laufrichtungsfeld einer Decke zeigt die AUFGELOESTE Achse — bei 6 × 4 m
 * sagt die Hausregel «der Balken nimmt den kuerzeren Weg» 90°. Ein
 * unabhaengiger Pruefer tippte genau diese 90 ein, `v !== value` war falsch,
 * es geschah nichts — und er hielt die ganze Faehigkeit fuer kaputt. Sie wirkt:
 * 0° gegen 90° bewegt an einer Brettstapeldecke rund 10 % der Bildpunkte.
 *
 * DIE ENTSCHEIDUNG, und warum nicht «immer committen»: gemessen kostete
 * «immer committen» die bestehende Zusicherung in `zahlfeld-f3-f4.test.tsx`
 * («ein unveraenderter Wert ist kein Commit-Anlass») — die ist fuer die 47
 * Felder richtig, die ein Modellfeld 1:1 zeigen. Darum traegt das MERKMAL das
 * Feld, das den abgeleiteten Wert zeigt, und der Default bleibt unveraendert.
 *
 * WARUM «BERUEHRT» UND NICHT «VERLASSEN»: ein `abgeleitet`-Feld, das bei JEDEM
 * Verlassen schriebe, machte aus dem blossen Durchtabben einen stillen
 * Schreibvorgang samt Undo-Schritt (Muster 9). Gezaehlt wird darum die
 * Eingabe, nicht der Fokuswechsel — ueber einen NATIVEN `input`-Lauscher.
 * GEMESSEN, NICHT VERMUTET (Sonde, 17.09.2026): tippt man denselben Text, den
 * das Feld schon zeigt, sieht ein nativer Lauscher das Ereignis (1×), Reacts
 * `onChange` sieht es NICHT (0×) — Reacts Wert-Merker unterdrueckt es. Ein
 * `onChange` waere hier also genau im gesuchten Fall blind gewesen.
 */

let root: Root | null = null;
let container: HTMLDivElement | null = null;

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
  vi.restoreAllMocks();
});

function mount(el: React.ReactElement): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(el);
  });
}

function feld(testid: string): HTMLInputElement {
  const el = container!.querySelector(`[data-testid="${testid}"]`) as HTMLInputElement | null;
  expect(el, `Feld «${testid}» fehlt`).not.toBeNull();
  return el!;
}

/** Tippen + wegklicken — dasselbe Muster wie `zahlfeld-f3-f4.test.tsx`. */
function tippenUndBlur(testid: string, wert: string): void {
  const el = feld(testid);
  act(() => {
    el.focus();
    el.value = wert;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.blur();
  });
}

/** NUR hineinklicken und wieder heraus — kein Tastendruck, kein input-Ereignis. */
function nurDurchgehen(testid: string): void {
  const el = feld(testid);
  act(() => {
    el.focus();
    el.blur();
  });
}

/**
 * Modell-Attrappe mit HAUSREGEL: `spann` ist der ausdrueckliche Override, der
 * anfangs fehlt; angezeigt wird die abgeleitete Achse. Genau die Lage der
 * Decke aus dem Befund — nur ohne Kern, damit die Probe die Komponente misst
 * und nicht den Kern.
 */
function DeckenFeld({
  hausregel,
  abgeleitet,
  spy,
  wirft = false,
}: {
  hausregel: number;
  abgeleitet?: boolean;
  spy?: (v: number) => void;
  wirft?: boolean;
}) {
  const [spann, setSpann] = useState<number | undefined>(undefined);
  const gezeigt = spann ?? hausregel;
  return (
    <KNumberField
      value={gezeigt}
      data-testid="lauf"
      {...(abgeleitet === true ? { abgeleitet: true } : {})}
      onCommit={(v) => {
        spy?.(v);
        if (wirft) throw new Error('vom Kernel abgelehnt');
        setSpann(v);
      }}
    />
  );
}

describe('B20 — `abgeleitet`: der angezeigte Wert laesst sich ausdruecklich setzen', () => {
  it('DER BEFUND: die angezeigte Zahl noch einmal eintippen committet — der Override wird fest gesetzt', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} abgeleitet spy={spy} />);

    expect(feld('lauf').value, 'das Feld zeigt die aufgeloeste Achse der Hausregel').toBe('90');
    tippenUndBlur('lauf', '90');

    expect(spy, 'die Eingabe des angezeigten Werts ist eine Bestellung, kein Nichts').toHaveBeenCalledWith(90);
    expect(spy).toHaveBeenCalledTimes(1);
    expect(feld('lauf').value, 'danach steht weiterhin der echte Modellwert im Feld').toBe('90');
  });

  it('GEGENPROBE — dasselbe Feld OHNE das Merkmal schluckt weiter: ein gewoehnliches Feld schreibt nicht bei jedem Verlassen', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} spy={spy} />);

    tippenUndBlur('lauf', '90');

    expect(spy, 'ohne `abgeleitet` bleibt der unveraenderte Wert kein Commit-Anlass').not.toHaveBeenCalled();
  });

  it('GEGENPROBE ZUR GEGENPROBE — nur durchgehen, ohne zu tippen, schreibt AUCH mit dem Merkmal nichts', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} abgeleitet spy={spy} />);

    nurDurchgehen('lauf');

    expect(spy, 'ein blosser Fokuswechsel ist keine Eingabe — sonst waere jedes Durchtabben ein Undo-Schritt').not.toHaveBeenCalled();
  });

  it('GEGENPROBE — eine ANDERE Zahl committet mit dem Merkmal genau EINMAL, nicht zweimal', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} abgeleitet spy={spy} />);

    tippenUndBlur('lauf', '45');

    expect(spy).toHaveBeenCalledTimes(1);
    expect(spy).toHaveBeenCalledWith(45);
    expect(feld('lauf').value).toBe('45');
  });

  it('F4 BLEIBT — ein geleertes Feld schreibt auch mit dem Merkmal keine 0', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} abgeleitet spy={spy} />);

    tippenUndBlur('lauf', '');

    expect(spy, 'der Leerfall ist keine Eingabe — das Merkmal darf F4 nicht aufweichen').not.toHaveBeenCalled();
    expect(feld('lauf').value, 'das Feld muss danach den Modellwert zeigen, nicht leer bleiben').toBe('90');
  });

  it('F3 BLEIBT — ein werfender Commit auf dem unveraenderten Wert laesst nichts stehen und dringt nicht nach aussen', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} abgeleitet spy={spy} wirft />);

    tippenUndBlur('lauf', '90');

    expect(spy).toHaveBeenCalledWith(90);
    expect(feld('lauf').value, 'auch nach einem werfenden Commit steht der echte Modellwert im Feld').toBe('90');
  });

  it('ZWEIMAL HINTEREINANDER — das Merkmal bleibt nach dem ersten Commit wirksam (der Beruehrt-Merker wird zurueckgesetzt)', () => {
    const spy = vi.fn();
    mount(<DeckenFeld hausregel={90} abgeleitet spy={spy} />);

    tippenUndBlur('lauf', '90');
    expect(spy).toHaveBeenCalledTimes(1);

    // Nach dem ersten Commit steht der Override auf 90; erneut 90 tippen ist
    // wieder eine ausdrueckliche Bestellung und muss wieder durchgehen.
    tippenUndBlur('lauf', '90');
    expect(spy, 'der Merker darf nicht haengenbleiben — sonst wirkte das Merkmal nur einmal').toHaveBeenCalledTimes(2);

    // Und die Gegenprobe zur Gegenprobe: durchgehen ohne Tippen bleibt auch
    // JETZT folgenlos, der Merker ist also wirklich zurueckgesetzt und nicht
    // dauerhaft auf «beruehrt» stehengeblieben.
    nurDurchgehen('lauf');
    expect(spy).toHaveBeenCalledTimes(2);
  });
});
