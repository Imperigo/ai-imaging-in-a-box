// @vitest-environment jsdom
import { act, useRef } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useOverlaySchliessen } from '../src/overlay-schliessen';

// Gleiches Muster wie komponenten.test.tsx: ohne dieses Flag warnt React bei
// jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * `useOverlaySchliessen` (v0.8.4 PA4, Spez §3 E3) — Regressionsschutz für
 * Esc, Aussenklick, Hover-Rückklapp-Timer, Timer-Stornierung und Cleanup.
 * Testkomponente: ein Wrapper-`<div>` (das `ref`-Ziel, enthält Trigger UND
 * Popup als Kinder — dasselbe Prinzip wie `KMenu`s `wrapRef`) plus ein
 * separates Element AUSSERHALB als Aussenklick-Ziel.
 */

function Testkomponente({ onClose, optionen }: { onClose: () => void; optionen?: Parameters<typeof useOverlaySchliessen>[2] }) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  useOverlaySchliessen(wrapRef, onClose, optionen);
  return (
    <div>
      <div data-testid="wrapper" ref={wrapRef}>
        <button type="button" data-testid="trigger">
          Trigger
        </button>
        <div data-testid="popup">Popup-Inhalt</div>
      </div>
      <button type="button" data-testid="aussen">
        Aussen
      </button>
    </div>
  );
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function montiere(onClose: () => void, optionen?: Parameters<typeof useOverlaySchliessen>[2]): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root!.render(<Testkomponente onClose={onClose} optionen={optionen} />);
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
  vi.useRealTimers();
});

describe('useOverlaySchliessen — Esc', () => {
  it('Escape (globaler keydown) ruft onClose', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++);

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(geschlossen).toBe(1);
  });

  it('esc:false unterdrückt den Escape-Schluss', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++, { esc: false });

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(geschlossen).toBe(0);
  });

  it('andere Tasten als Escape lösen nichts aus', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++);

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    });
    expect(geschlossen).toBe(0);
  });
});

describe('useOverlaySchliessen — Aussenklick', () => {
  it('mousedown ausserhalb des ref-Elements ruft onClose', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++);

    const aussen = container!.querySelector('[data-testid="aussen"]') as HTMLButtonElement;
    act(() => {
      aussen.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    expect(geschlossen).toBe(1);
  });

  it('mousedown INNERHALB des ref-Elements (Trigger oder Popup) ruft onClose NICHT', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++);

    const trigger = container!.querySelector('[data-testid="trigger"]') as HTMLButtonElement;
    const popup = container!.querySelector('[data-testid="popup"]') as HTMLDivElement;
    act(() => {
      trigger.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      popup.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    expect(geschlossen).toBe(0);
  });

  it('mousedown in einer portalten KSelect-Listbox (data-kselect-portal, ausserhalb ref) ruft onClose NICHT', () => {
    // P-F6-Nachzug (v0.9.2): die KSelect-Listbox lebt als body-Portal und
    // liegt darum IMMER ausserhalb des Overlay-`ref` — ein mousedown auf
    // eine Option darf das Overlay trotzdem nicht schliessen, sonst
    // unmountet der KSelect vor dem click und die Wahl verpufft
    // (E2E-Befund island-leer, Trace-Ziel).
    let geschlossen = 0;
    montiere(() => geschlossen++);

    const listbox = document.createElement('div');
    listbox.setAttribute('data-kselect-portal', '');
    const option = document.createElement('button');
    listbox.appendChild(option);
    document.body.appendChild(listbox);
    act(() => {
      option.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    expect(geschlossen).toBe(0);
    listbox.remove();
  });

  it('aussenklick:false unterdrückt den Aussenklick-Schluss', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++, { aussenklick: false });

    const aussen = container!.querySelector('[data-testid="aussen"]') as HTMLButtonElement;
    act(() => {
      aussen.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    });
    expect(geschlossen).toBe(0);
  });
});

describe('useOverlaySchliessen — Hover-Rückklapp-Timer', () => {
  it('pointerleave startet einen Timer, der nach hoverRueckklappMs onClose ruft', () => {
    vi.useFakeTimers();
    let geschlossen = 0;
    montiere(() => geschlossen++, { hoverRueckklappMs: 1000 });

    const wrapper = container!.querySelector('[data-testid="wrapper"]') as HTMLDivElement;
    act(() => {
      wrapper.dispatchEvent(new Event('pointerleave', { bubbles: false }));
    });
    expect(geschlossen).toBe(0);

    act(() => {
      vi.advanceTimersByTime(999);
    });
    expect(geschlossen).toBe(0);

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(geschlossen).toBe(1);
  });

  it('pointerenter VOR Ablauf storniert den Timer restlos — kein onClose-Ruf', () => {
    vi.useFakeTimers();
    let geschlossen = 0;
    montiere(() => geschlossen++, { hoverRueckklappMs: 1000 });

    const wrapper = container!.querySelector('[data-testid="wrapper"]') as HTMLDivElement;
    act(() => {
      wrapper.dispatchEvent(new Event('pointerleave', { bubbles: false }));
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });
    act(() => {
      wrapper.dispatchEvent(new Event('pointerenter', { bubbles: false }));
    });
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(geschlossen).toBe(0);
  });

  it('ohne hoverRueckklappMs löst pointerleave NICHTS aus (kein Default-Timer)', () => {
    vi.useFakeTimers();
    let geschlossen = 0;
    montiere(() => geschlossen++);

    const wrapper = container!.querySelector('[data-testid="wrapper"]') as HTMLDivElement;
    act(() => {
      wrapper.dispatchEvent(new Event('pointerleave', { bubbles: false }));
    });
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(geschlossen).toBe(0);
  });

  it('Unmount VOR Timer-Ablauf räumt den Timer auf — kein onClose-Ruf nach dem Unmount', () => {
    vi.useFakeTimers();
    let geschlossen = 0;
    montiere(() => geschlossen++, { hoverRueckklappMs: 1000 });

    const wrapper = container!.querySelector('[data-testid="wrapper"]') as HTMLDivElement;
    act(() => {
      wrapper.dispatchEvent(new Event('pointerleave', { bubbles: false }));
    });
    act(() => {
      root!.unmount();
    });
    root = null;
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(geschlossen).toBe(0);
  });
});

describe('useOverlaySchliessen — Cleanup beim Unmount', () => {
  it('nach dem Unmount lösen weder Escape noch Aussenklick noch pointerleave onClose aus', () => {
    let geschlossen = 0;
    montiere(() => geschlossen++);

    act(() => {
      root!.unmount();
    });
    root = null;

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(geschlossen).toBe(0);
  });
});
