// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { KCheckbox } from '../src/checkbox';
import { KSlider } from '../src/slider';
import { KTable } from '../src/table';
import { KTextarea } from '../src/textarea';
import { KTooltip } from '../src/tooltip';

// Gleiches Muster wie `komponenten.test.tsx`: ohne dieses Flag warnt React
// bei jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * P-f (Bausteine-Nachtrag) — Regressionsschutz für die fünf Bausteine, die
 * `KTooltip`/`KCheckbox`/`KSlider`/`KTextarea`/`KTable` in `aura.css`
 * ersetzen (Bedarf je Kopfkommentar der jeweiligen Datei). Muster wie
 * `komponenten.test.tsx`: `renderToStaticMarkup` für reine Struktur-Checks,
 * `createRoot`+`act`+echte DOM-Ereignisse für Interaktion.
 *
 * `pointerenter`/`pointerleave` sind in React (s. `react-dom-client
 * .development.js:27414-27415`) aus den NATIVEN, bubbelnden `pointerover`/
 * `pointerout`-Ereignissen abgeleitet — jsdom kennt zudem KEINEN
 * `PointerEvent`-Konstruktor (geprüft: `new (window as any).PointerEvent(…)`
 * wirft `TypeError: … is not a constructor`). `zeigerEreignis` unten
 * konstruiert deshalb ein `MouseEvent` (das `relatedTarget` im Init-Dict
 * kennt) mit dem gewünschten Event-NAMEN und hängt `pointerType` per
 * `Object.defineProperty` nach — React liest beide Felder generisch vom
 * nativen Event, unabhängig vom konkreten Konstruktor (selbst geprüft mit
 * einer Probe-Datei vor diesem Bau, s. Bau-Bericht).
 */
function zeigerEreignis(typ: string, pointerType: string): Event {
  const ev = new MouseEvent(typ, { bubbles: true, cancelable: true, relatedTarget: null } as MouseEventInit);
  Object.defineProperty(ev, 'pointerType', { value: pointerType });
  return ev;
}

describe('KTooltip — Ersatz für title=, muss auf Touch UND Maus funktionieren', () => {
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
  });

  it('trägt KEIN natives title-Attribut — das ist der ganze Anlass des Bausteins', () => {
    const html = renderToStaticMarkup(
      <KTooltip text="Exportieren">
        <button type="button">E</button>
      </KTooltip>,
    );
    expect(html).not.toContain('title=');
  });

  it('rendert die Blase NICHT, solange niemand hovert/tippt/fokussiert', () => {
    const html = renderToStaticMarkup(
      <KTooltip text="Exportieren">
        <button type="button">E</button>
      </KTooltip>,
    );
    expect(html).not.toContain('k-tooltip-blase');
    expect(html).not.toContain('role="tooltip"');
  });

  it('Maus: pointerenter zeigt die Blase ERST nach der Verzögerung, nicht sofort (Gegenprobe: reines Hover-CSS wäre sofort sichtbar)', () => {
    vi.useFakeTimers();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KTooltip text="Exportieren" data-testid="tip">
          <button type="button" data-testid="knopf">
            E
          </button>
        </KTooltip>,
      );
    });
    const knopf = container.querySelector('[data-testid="knopf"]') as HTMLElement;

    act(() => {
      knopf.dispatchEvent(zeigerEreignis('pointerover', 'mouse'));
    });
    expect(container.querySelector('[role="tooltip"]')).toBeNull();

    act(() => {
      vi.advanceTimersByTime(399);
    });
    expect(container.querySelector('[role="tooltip"]')).toBeNull();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(container.querySelector('[role="tooltip"]')?.textContent).toContain('Exportieren');

    vi.useRealTimers();
  });

  it('Maus: pointerleave schliesst sofort und storniert einen noch laufenden Zeitgeber', () => {
    vi.useFakeTimers();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KTooltip text="Exportieren">
          <button type="button" data-testid="knopf">
            E
          </button>
        </KTooltip>,
      );
    });
    const knopf = container.querySelector('[data-testid="knopf"]') as HTMLElement;

    act(() => {
      knopf.dispatchEvent(zeigerEreignis('pointerover', 'mouse'));
    });
    act(() => {
      knopf.dispatchEvent(zeigerEreignis('pointerout', 'mouse'));
    });
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(container.querySelector('[role="tooltip"]')).toBeNull();

    vi.useRealTimers();
  });

  it('Touch/Pen: ein pointerenter ALLEIN zeigt NICHTS — Falsifizierung des reinen Hover-Wegs auf Touch (E-8)', () => {
    vi.useFakeTimers();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KTooltip text="Exportieren">
          <button type="button" data-testid="knopf">
            E
          </button>
        </KTooltip>,
      );
    });
    const knopf = container.querySelector('[data-testid="knopf"]') as HTMLElement;

    act(() => {
      knopf.dispatchEvent(zeigerEreignis('pointerover', 'touch'));
    });
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(container.querySelector('[role="tooltip"]')).toBeNull();

    vi.useRealTimers();
  });

  it('Touch/Pen: ein Tipp (pointerdown+click) SCHALTET die Blase um, sofort, ohne Verzögerung', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KTooltip text="Exportieren">
          <button type="button" data-testid="knopf">
            E
          </button>
        </KTooltip>,
      );
    });
    const knopf = container.querySelector('[data-testid="knopf"]') as HTMLElement;

    act(() => {
      knopf.dispatchEvent(zeigerEreignis('pointerdown', 'touch'));
      knopf.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(container.querySelector('[role="tooltip"]')?.textContent).toContain('Exportieren');

    // Zweiter Tipp klappt wieder zu.
    act(() => {
      knopf.dispatchEvent(zeigerEreignis('pointerdown', 'touch'));
      knopf.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(container.querySelector('[role="tooltip"]')).toBeNull();
  });

  it('Fokus (Tastatur) zeigt sofort, Blur schliesst — kein Zeitgeber nötig', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KTooltip text="Exportieren">
          <button type="button" data-testid="knopf">
            E
          </button>
        </KTooltip>,
      );
    });
    const knopf = container.querySelector('[data-testid="knopf"]') as HTMLElement;

    act(() => {
      knopf.focus();
    });
    expect(container.querySelector('[role="tooltip"]')?.textContent).toContain('Exportieren');

    act(() => {
      knopf.blur();
    });
    expect(container.querySelector('[role="tooltip"]')).toBeNull();
  });

  it('kuerzel rendert als eigener Zusatz neben dem Text', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(
        <KTooltip text="Suchen" kuerzel="⌘K">
          <button type="button" data-testid="knopf">
            S
          </button>
        </KTooltip>,
      );
    });
    act(() => {
      (container!.querySelector('[data-testid="knopf"]') as HTMLElement).focus();
    });
    const blase = container.querySelector('.k-tooltip-blase') as HTMLElement;
    expect(blase.textContent).toContain('Suchen');
    expect(blase.querySelector('.k-tooltip-kuerzel')?.textContent).toBe('⌘K');
  });
});

describe('KCheckbox — Kontrollkästchen (Gegenstück zu KSwitch, das ausdrücklich ein Umschalter ist)', () => {
  it('rendert unmarkiert per Default, trägt k-checkbox + Grössenklasse', () => {
    const html = renderToStaticMarkup(<KCheckbox data-testid="cb" />);
    expect(html).toContain('type="checkbox"');
    expect(html).toContain('k-checkbox--md');
    expect(html).not.toContain('checked=""');
  });

  it('label rendert als eigener Text-Span, wenn gesetzt', () => {
    const html = renderToStaticMarkup(<KCheckbox label="Sichtbar" />);
    expect(html).toContain('k-checkbox-label');
    expect(html).toContain('Sichtbar');
  });

  it('ohne label KEIN k-checkbox-label-Span — Falsifizierung "Label immer da"', () => {
    const html = renderToStaticMarkup(<KCheckbox />);
    expect(html).not.toContain('k-checkbox-label');
  });

  it('size="sm" trägt k-checkbox--sm, NICHT k-checkbox--md', () => {
    const html = renderToStaticMarkup(<KCheckbox size="sm" />);
    expect(html).toContain('k-checkbox--sm');
    expect(html).not.toContain('k-checkbox--md');
  });

  it('ein echter Klick markiert das native Input (Tastatur/Screenreader/E2E bleiben nutzbar)', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() => {
      root.render(<KCheckbox data-testid="cb" />);
    });
    const input = container.querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(input.checked).toBe(false);
    act(() => {
      input.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(input.checked).toBe(true);
    act(() => root.unmount());
    container.remove();
  });

  it('unbestimmt=true setzt das DOM-Property indeterminate (JSX kennt es nicht als Attribut)', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() => {
      root.render(<KCheckbox unbestimmt data-testid="cb" />);
    });
    const input = container.querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(input.indeterminate).toBe(true);

    // Falsifizierung: unbestimmt=false (Default) lässt es aus.
    act(() => {
      root.render(<KCheckbox data-testid="cb" />);
    });
    expect(input.indeterminate).toBe(false);

    act(() => root.unmount());
    container.remove();
  });
});

describe('KSlider — natives type="range", nur Spur/Griff gestylt', () => {
  it('rendert ein input type="range" mit k-slider + Grössenklasse', () => {
    const html = renderToStaticMarkup(<KSlider min={0} max={10} defaultValue={3} data-testid="sl" />);
    expect(html).toContain('type="range"');
    expect(html).toContain('k-slider--md');
    expect(html).toContain('data-testid="sl"');
  });

  it('size="sm" trägt k-slider--sm, NICHT k-slider--md — Falsifizierung fester Default-Klasse', () => {
    const html = renderToStaticMarkup(<KSlider size="sm" />);
    expect(html).toContain('k-slider--sm');
    expect(html).not.toContain('k-slider--md');
  });

  it('onChange feuert bei echter Wertänderung mit dem neuen Wert', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);
    const root = createRoot(container);
    let letzterWert = '';
    act(() => {
      root.render(
        <KSlider min={0} max={10} defaultValue={2} onChange={(e) => (letzterWert = e.target.value)} data-testid="sl" />,
      );
    });
    const input = container.querySelector('input[type="range"]') as HTMLInputElement;
    // `input.value = '7'` allein setzt NICHT den React-Wert-Tracker zurück
    // (der native Setter umgeht den React-Patch, s. `apps/kosmo-orbit/test/
    // berechnungsliste-panel-spiegel.test.tsx` `setzeControlledInputValue`)
    // — ohne den Umweg über den ECHTEN Prototyp-Setter bliebe `onChange` aus.
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    act(() => {
      setter.call(input, '7');
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    expect(letzterWert).toBe('7');
    act(() => root.unmount());
    container.remove();
  });
});

describe('KTextarea — Blaupause KInput, mehrzeilig', () => {
  it('rendert ein <textarea>, KEIN <input> — Falsifizierung des falschen Tags', () => {
    const html = renderToStaticMarkup(<KTextarea data-testid="ta" />);
    expect(html).toContain('<textarea');
    expect(html).not.toContain('<input');
  });

  it('mono=true trägt k-textarea--mono, Default lässt es aus', () => {
    const mono = renderToStaticMarkup(<KTextarea mono data-testid="ta" />);
    expect(mono).toContain('k-textarea--mono');
    const ohne = renderToStaticMarkup(<KTextarea data-testid="ta" />);
    expect(ohne).not.toContain('k-textarea--mono');
  });

  it('rows/placeholder/value werden durchgereicht wie bei jedem nativen textarea', () => {
    const html = renderToStaticMarkup(<KTextarea rows={5} placeholder="Notiz…" defaultValue="Text" />);
    expect(html).toContain('rows="5"');
    expect(html).toContain('placeholder="Notiz…"');
    expect(html).toContain('Text');
  });
});

describe('KTable — reiner Klassen-Wrapper um <table>', () => {
  it('rendert eine <table> mit k-table, Kinder (thead/tbody) bleiben native Elemente', () => {
    const html = renderToStaticMarkup(
      <KTable data-testid="t">
        <thead>
          <tr>
            <th>Spalte</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Wert</td>
          </tr>
        </tbody>
      </KTable>,
    );
    expect(html).toContain('<table');
    expect(html).toContain('class="k-table"');
    expect(html).toContain('<thead');
    expect(html).toContain('<tbody');
    expect(html).toContain('Spalte');
    expect(html).toContain('Wert');
  });

  it('dicht=true trägt k-table--dicht ZUSAETZLICH zu k-table, Default lässt es aus', () => {
    const dicht = renderToStaticMarkup(<KTable dicht />);
    expect(dicht).toContain('class="k-table k-table--dicht"');
    const ohne = renderToStaticMarkup(<KTable />);
    expect(ohne).not.toContain('k-table--dicht');
  });
});

