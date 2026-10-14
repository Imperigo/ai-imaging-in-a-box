// @vitest-environment jsdom
import { act, useRef } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useOverlaySchliessen } from '../src/overlay-schliessen';
import { KDialog } from '../src/overlay';
import { bestaetigen, KBestaetigung } from '../src/meldungen';

/**
 * Das EINE Haus-Gesetz fürs modale Verhalten (Schichtungs-Entscheide 20a,
 * 24a, 37a, 38b, 39a vom 21.09.2026).
 *
 * Bis zu diesem Paket konnte eine Fläche sich die HÄLFTE des Gesetzes holen:
 * `useOverlaySchliessen` kannte nur Escape/Aussenklick, `useFokusFalle` lag
 * daneben und wurde an genau zwei Stellen gerufen, und eine Fokusrückgabe
 * gab es im ganzen Repo nicht. `modal: true` ist darum EIN Wort für das
 * ganze Gesetz — Escape, Falle und Rückgabe zusammen, oder nichts.
 *
 * WAS DIESE PROBE NICHT BEWEIST (jsdom): die echte Tab-Reihenfolge des
 * Browsers. Geprüft wird der `keydown`-Vertrag der Falle.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

function esc(): void {
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
}
function tab(shift = false): void {
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: shift, bubbles: true, cancelable: true }));
}

let root: Root | null = null;
let halter: HTMLDivElement | null = null;

function auf(): void {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
}
function ab(): void {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  halter?.remove();
  halter = null;
}

afterEach(() => {
  ab();
  document.body.innerHTML = '';
});

/** Eine Minimal-Fläche, die das ganze Gesetz in einem Wort bestellt. */
function ModaleFlaeche({ onClose }: { onClose: () => void }) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  useOverlaySchliessen(boxRef, onClose, { modal: true, aussenklick: false });
  return (
    <div data-testid="probe-scrim">
      <div ref={boxRef} data-testid="probe-box">
        <button data-testid="probe-erster">erster</button>
        <button data-testid="probe-letzter">letzter</button>
      </div>
    </div>
  );
}

describe('useOverlaySchliessen — `modal: true` bringt das GANZE Gesetz, nicht die Hälfte', () => {
  it('Escape schliesst', () => {
    const onClose = vi.fn();
    auf();
    act(() => root!.render(<ModaleFlaeche onClose={onClose} />));
    act(() => esc());
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('die Fokusfalle kommt mit — Tab von aussen zieht den Fokus in die Fläche', () => {
    const aussen = document.createElement('button');
    document.body.appendChild(aussen);
    auf();
    act(() => root!.render(<ModaleFlaeche onClose={() => {}} />));
    aussen.focus();
    act(() => tab());
    expect(document.activeElement).toBe(document.querySelector('[data-testid="probe-erster"]'));
  });

  it('die Fokusrückgabe kommt mit — nach dem Abbau steht der Fokus wieder auf dem Öffner', () => {
    const oeffner = document.createElement('button');
    document.body.appendChild(oeffner);
    oeffner.focus();
    auf();
    act(() => root!.render(<ModaleFlaeche onClose={() => {}} />));
    (document.querySelector('[data-testid="probe-letzter"]') as HTMLElement).focus();
    ab();
    expect(document.activeElement).toBe(oeffner);
  });

  it('die Rückgabe stiehlt NICHT, wenn der Mensch inzwischen bewusst etwas anderes fokussiert hat', () => {
    const oeffner = document.createElement('button');
    const anderes = document.createElement('button');
    document.body.append(oeffner, anderes);
    oeffner.focus();
    auf();
    act(() => root!.render(<ModaleFlaeche onClose={() => {}} />));
    anderes.focus();
    ab();
    expect(document.activeElement).toBe(anderes);
  });
});

describe('Entscheid 24a — Escape schliesst die OBERSTE modale Fläche, nicht alle auf einmal', () => {
  function Gestapelt({ aussenZu, innenZu }: { aussenZu: () => void; innenZu: () => void }) {
    const aussenRef = useRef<HTMLDivElement | null>(null);
    const innenRef = useRef<HTMLDivElement | null>(null);
    useOverlaySchliessen(aussenRef, aussenZu, { modal: true, aussenklick: false });
    useOverlaySchliessen(innenRef, innenZu, { modal: true, aussenklick: false });
    return (
      <div ref={aussenRef} data-testid="stapel-aussen">
        <button>aussen</button>
        <div ref={innenRef} data-testid="stapel-innen">
          <button>innen</button>
        </div>
      </div>
    );
  }

  it('bei zwei gestapelten modalen Flächen antwortet nur die innere auf Escape', () => {
    const aussenZu = vi.fn();
    const innenZu = vi.fn();
    auf();
    act(() => root!.render(<Gestapelt aussenZu={aussenZu} innenZu={innenZu} />));
    act(() => esc());
    expect(innenZu).toHaveBeenCalledTimes(1);
    expect(aussenZu).not.toHaveBeenCalled();
  });
});

describe('KDialog — das Haus-Gesetz statt eigener Handler', () => {
  it('gibt den Fokus nach dem Schliessen an den Öffner zurück', () => {
    const oeffner = document.createElement('button');
    document.body.appendChild(oeffner);
    oeffner.focus();
    auf();
    act(() =>
      root!.render(
        <KDialog titel="Probe" onClose={() => {}}>
          <button data-testid="kdialog-inhalt">Inhalt</button>
        </KDialog>,
      ),
    );
    (document.querySelector('[data-testid="kdialog-inhalt"]') as HTMLElement).focus();
    ab();
    expect(document.activeElement).toBe(oeffner);
  });
});

describe('KBestaetigung — der «Esc-Vertrag», den bisher niemand gefahren ist', () => {
  it('Escape (globaler keydown, Fokus NICHT im Dialog) bricht die Bestätigung ab', () => {
    auf();
    act(() => {
      void bestaetigen({ titel: 'Wirklich löschen?', gefaehrlich: true });
    });
    act(() => root!.render(<KBestaetigung />));
    expect(document.body.querySelector('[data-testid="bestaetigung"]')).not.toBeNull();
    act(() => esc());
    expect(document.body.querySelector('[data-testid="bestaetigung"]')).toBeNull();
  });
});

/** Ein nicht-modales Fenster mit Aussenklick, daneben ein «Rückgängig» und ein gewöhnlicher Knopf. */
function FensterMitUndo({ onClose }: { onClose: () => void }) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  useOverlaySchliessen(boxRef, onClose, { aussenklick: true });
  return (
    <div>
      <div ref={boxRef} data-testid="probe-fenster">Fenster</div>
      <button data-testid="probe-undo" data-aussenklick-frei="">
        <span data-testid="probe-undo-zeichen">↶</span>
      </button>
      <button data-testid="probe-anderswo">anderswo</button>
    </div>
  );
}

function mausAuf(testid: string): void {
  const el = document.querySelector(`[data-testid="${testid}"]`)!;
  el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
}

describe('U25 Phase 6 (Welle D4) — ein Klick auf «Rückgängig» ist kein Aussenklick', () => {
  it('ein Knopf mit `data-aussenklick-frei` (auch sein Inneres) schliesst das Fenster nicht', () => {
    const onClose = vi.fn();
    auf();
    act(() => root!.render(<FensterMitUndo onClose={onClose} />));
    act(() => mausAuf('probe-undo'));
    act(() => mausAuf('probe-undo-zeichen'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('Gegenprobe: ein gewöhnlicher Knopf daneben schliesst es weiterhin', () => {
    const onClose = vi.fn();
    auf();
    act(() => root!.render(<FensterMitUndo onClose={onClose} />));
    act(() => mausAuf('probe-anderswo'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
