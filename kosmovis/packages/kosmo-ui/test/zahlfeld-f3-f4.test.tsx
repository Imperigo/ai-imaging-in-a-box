// @vitest-environment jsdom
import { useState } from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { KNumberField } from '../src/field';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * KNumberField — F3/F4 (docs/UI-UX-2026-09-08-FEHLER-DATENVERLUST.md,
 * Auftrag Z1): dieselben vier Zusicherungen, die
 * `inspector-zahlfeld-leer-und-abgelehnt.test.tsx` am Inspector prüft, hier
 * EINMAL an der geteilten Komponente selbst, unabhängig von Inspector/Kernel
 * — ein simulierter "Kernel" (die `onCommit`-Rückgabe/der Wurf der jeweiligen
 * Test-Hülle) steht anstelle eines echten `runCommand`.
 *
 * Muster (`createRoot` + `act`, echte DOM-Events statt Testing-Library, im
 * Workspace nicht vorhanden) übernommen von `komponenten.test.tsx` und der
 * Inspector-Testdatei oben.
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

/** Fokussiert, setzt `.value` direkt (unkontrolliertes Feld) und löst Blur
 *  aus — dasselbe Muster wie `inspector-zahlfeld-leer-und-abgelehnt.test.tsx`. */
function tippenUndBlur(testid: string, wert: string): void {
  const feld = container!.querySelector(`[data-testid="${testid}"]`) as HTMLInputElement | null;
  expect(feld, `Feld «${testid}» fehlt`).not.toBeNull();
  act(() => {
    feld!.focus();
    feld!.value = wert;
    feld!.dispatchEvent(new Event('input', { bubbles: true }));
    feld!.blur();
  });
}

function feldWert(testid: string): string {
  const feld = container!.querySelector(`[data-testid="${testid}"]`) as HTMLInputElement | null;
  expect(feld, `Feld «${testid}» fehlt nach dem Blur — wurde es neu montiert?`).not.toBeNull();
  return feld!.value;
}

/** Modell-Attrappe: `onCommit` verhält sich wie `Inspector.tsx`s `set()` —
 *  akzeptierte Werte fliessen zurück ins `value`-Prop, wie ein echter
 *  Kernel-Roundtrip über Undo/Sync das täte. `akzeptiert` entscheidet je
 *  Aufruf, ob der simulierte Kernel den Wert annimmt. */
function ModellFeld({
  initial,
  akzeptiert,
  spy,
  wirft = false,
  suffix,
}: {
  initial: number;
  akzeptiert: (v: number) => boolean;
  spy?: (v: number) => void;
  wirft?: boolean;
  suffix?: string;
}) {
  const [value, setValue] = useState(initial);
  return (
    <KNumberField
      value={value}
      data-testid="zf"
      // exactOptionalPropertyTypes: `suffix` nur setzen, wenn es wirklich da
      // ist — sonst wäre `suffix: undefined` explizit im Objekt, was der
      // Compiler von einem `suffix?: string`-Prop unterscheidet.
      {...(suffix !== undefined ? { suffix } : {})}
      onCommit={(v) => {
        spy?.(v);
        if (wirft) throw new Error('vom Kernel abgelehnt');
        if (akzeptiert(v)) setValue(v);
        // sonst: bewusst KEIN State-Update — simuliert eine Ablehnung, die
        // NICHT wirft (die zweite in der Auflage genannte Spielart von F3).
      }}
    />
  );
}

describe('KNumberField — F4 (leeres Feld schreibt keine 0)', () => {
  it('Feld leeren und wegklicken lässt den Modellwert unverändert', () => {
    const spy = vi.fn();
    mount(<ModellFeld initial={5} akzeptiert={() => true} spy={spy} />);

    tippenUndBlur('zf', '');

    expect(spy, 'ein leeres Feld darf onCommit gar nicht erst rufen').not.toHaveBeenCalled();
    expect(feldWert('zf'), 'das Feld muss den Modellwert zeigen, nicht leer bleiben').toBe('5');
  });

  it('Gegenprobe — eine ECHTE 0 kommt weiterhin an (der Leerfall-Schutz darf den gültigen Fall nicht miterschlagen)', () => {
    const spy = vi.fn();
    mount(<ModellFeld initial={5} akzeptiert={() => true} spy={spy} />);

    tippenUndBlur('zf', '0');

    expect(spy).toHaveBeenCalledWith(0);
    expect(feldWert('zf'), 'wo 0 ein gültiger Modellwert ist, muss 0 auch ankommen').toBe('0');
  });
});

describe('KNumberField — F3 (ein abgelehnter Wert bleibt nicht sichtbar stehen)', () => {
  it('Ablehnung OHNE Wurf (onCommit läuft durch, ändert aber `value` nicht) — Feld fällt auf den Modellwert zurück', () => {
    const spy = vi.fn();
    mount(<ModellFeld initial={300} akzeptiert={() => false} spy={spy} />);

    tippenUndBlur('zf', '20');

    expect(spy).toHaveBeenCalledWith(20);
    expect(
      feldWert('zf'),
      'ohne Neubau bliebe hier der abgelehnte Text "20" stehen, weil `value` (300) unverändert blieb',
    ).toBe('300');
  });

  it('Ablehnung MIT Wurf (onCommit wirft) — Feld fällt trotzdem sichtbar auf den Modellwert zurück, kein unbehandelter Fehler', () => {
    const spy = vi.fn();
    mount(<ModellFeld initial={300} akzeptiert={() => true} spy={spy} wirft />);

    // Ein werfendes onCommit darf den Blur-Handler nicht mitten drin
    // abbrechen — das Remount-Ticking muss trotzdem laufen. Kein
    // `expect(...).toThrow()` nötig: die Zusicherung IST, dass hier nichts
    // unbehandelt nach aussen dringt.
    tippenUndBlur('zf', '20');

    expect(spy).toHaveBeenCalledWith(20);
    expect(feldWert('zf'), 'auch nach einem werfenden Commit muss der echte Modellwert wieder sichtbar sein').toBe(
      '300',
    );
  });

  it('Gegenprobe — ein ANGENOMMENER Wert committet normal und zeigt sich danach im Feld', () => {
    const spy = vi.fn();
    mount(<ModellFeld initial={300} akzeptiert={() => true} spy={spy} />);

    tippenUndBlur('zf', '450');

    expect(spy).toHaveBeenCalledWith(450);
    expect(feldWert('zf')).toBe('450');
  });
});

describe('KNumberField — unveränderter Wert löst keinen Commit aus', () => {
  it('derselbe Text wie der aktuelle Modellwert ruft onCommit nicht', () => {
    const spy = vi.fn();
    mount(<ModellFeld initial={7} akzeptiert={() => true} spy={spy} />);

    tippenUndBlur('zf', '7');

    expect(spy, 'ein unveränderter Wert ist kein Commit-Anlass').not.toHaveBeenCalled();
    expect(feldWert('zf')).toBe('7');
  });
});

describe('KNumberField — Einheit/Suffix optional', () => {
  it('ohne suffix-Prop wird kein Suffix-Element gerendert', () => {
    mount(<ModellFeld initial={1} akzeptiert={() => true} />);
    expect(container!.textContent).toBe('');
  });

  it('mit suffix-Prop erscheint der Text neben dem Feld', () => {
    mount(<ModellFeld initial={1} akzeptiert={() => true} suffix="mm" />);
    expect(container!.textContent).toBe('mm');
  });
});
