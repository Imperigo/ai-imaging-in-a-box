// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { GespeicherteAnsichten } from '../src/modules/vis/GespeicherteAnsichten';
import { GpuStatus } from '../src/modules/vis/GpuStatus';
import { VisReportDossier } from '../src/modules/vis/VisReportDossier';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * v0.8.1 / P8 (0.7.2-Rest «Viz gespeicherte Ansichten + Review-Pins» +
 * 0.7.5-Welle-2 «Report-Dossier», Spec §6.2/§9.17) — `createRoot`+jsdom
 * (Muster `varianten-panel.test.tsx`: zustand@5s `useStore` liefert unter
 * `renderToStaticMarkup` nur den Store-Anfangszustand, hier gebraucht der
 * Test aber echte Store-Mutationen).
 */
let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  useVisRuntime.setState({ aufnahmen: {}, gespeicherteAnsichten: {}, reviewPins: {} });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

describe('GespeicherteAnsichten (Spec §6.2, B-92/B-105)', () => {
  it('zeigt alle drei Slots leer, ohne gespeicherte Aufnahme', () => {
    act(() => root.render(<GespeicherteAnsichten />));
    for (const slot of ['iso', 'nord', 'detail']) {
      expect(container.querySelector(`[data-testid="ansicht-slot-${slot}-leer"]`)?.textContent).toBe(
        'Kein Snapshot gespeichert',
      );
    }
    // Ohne jede Aufnahme ist «speichern» konsequent gesperrt (kein Vortäuschen).
    const speichern = container.querySelector('[data-testid="ansicht-slot-iso-speichern"]') as HTMLButtonElement;
    expect(speichern.disabled).toBe(true);
  });

  it('speichert die jüngste Aufnahme in einen Slot — AUTOSAVE-Badge zeigt v001', () => {
    useVisRuntime.getState().fuegeAufnahmeHinzu({ id: 'a1', dataUrl: 'data:image/png;base64,x', zeit: Date.now(), kamera: 'aktuell' });
    act(() => root.render(<GespeicherteAnsichten />));
    const speichern = container.querySelector('[data-testid="ansicht-slot-iso-speichern"]') as HTMLButtonElement;
    expect(speichern.disabled).toBe(false);
    act(() => speichern.click());
    expect(container.querySelector('[data-testid="ansicht-slot-iso-autosave"]')?.textContent).toBe('AUTOSAVE · v001');
    expect(container.querySelector('[data-testid="ansicht-slot-iso-bild"]')).not.toBeNull();
  });

  it('Review-Klick auf die Fläche legt einen Pin mit Notiz an', () => {
    useVisRuntime.getState().fuegeAufnahmeHinzu({ id: 'a1', dataUrl: 'data:image/png;base64,x', zeit: Date.now(), kamera: 'aktuell' });
    useVisRuntime.getState().speichereAnsicht('nord', 'a1');
    act(() => root.render(<GespeicherteAnsichten />));

    const reviewKnopf = container.querySelector('[data-testid="ansicht-slot-nord-review"]') as HTMLButtonElement;
    act(() => reviewKnopf.click());

    const flaeche = container.querySelector('[data-testid="ansicht-slot-nord-flaeche"]') as HTMLElement;
    const rectStub = { left: 0, top: 0, width: 200, height: 150 } as DOMRect;
    flaeche.getBoundingClientRect = () => rectStub;
    act(() => flaeche.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: 50, clientY: 30 })));

    const textfeld = container.querySelector('[data-testid="review-pin-neu-text"]') as HTMLInputElement;
    expect(textfeld).not.toBeNull();
    // React verfolgt den Vorwert über einen eigenen Property-Setter — ein
    // reines `el.value = …` + `dispatchEvent('input')` sieht darum manchmal
    // «keine Änderung»; der native Prototyp-Setter umgeht das (Standard-
    // Testmuster für kontrollierte Inputs ausserhalb von Testing-Library).
    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')!.set!;
    act(() => {
      nativeSetter.call(textfeld, 'Fenster prüfen');
      textfeld.dispatchEvent(new Event('input', { bubbles: true }));
    });
    const speichernKnopf = container.querySelector('[data-testid="review-pin-neu-speichern"]') as HTMLButtonElement;
    act(() => speichernKnopf.click());

    expect(useVisRuntime.getState().reviewPins.a1).toHaveLength(1);
    expect(useVisRuntime.getState().reviewPins.a1![0]!.text).toBe('Fenster prüfen');
    expect(container.querySelectorAll('[data-testid^="review-pin-pin-"]').length).toBeGreaterThan(0);
  });
});

describe('GpuStatus (Spec §6.2, C-32 — GPU-Telemetrie-Grenze)', () => {
  it('rendert ehrlich einen Prüf-Zustand, nie eine erfundene Prozentzahl', () => {
    act(() => root.render(<GpuStatus />));
    const text = container.querySelector('[data-testid="vis-gpu-status-text"]')?.textContent ?? '';
    expect(text.length).toBeGreaterThan(0);
    expect(text).not.toMatch(/\d+\s*%/); // keine erfundene Auslastungs-Prozentzahl
  });

  it('zeigt die echte GPU-Warteschlange aus vis-runtime (wartetGpu-Läufe), nicht erst nach einem Poll', () => {
    useVisRuntime.getState().setzeLauf('n1', { status: 'wartetGpu', memoKey: 'k' });
    useVisRuntime.getState().setzeLauf('n2', { status: 'wartetGpu', memoKey: 'k' });
    act(() => root.render(<GpuStatus />));
    expect(container.querySelector('[data-testid="vis-gpu-warteschlange"]')?.textContent).toContain('2 in GPU-Warteschlange');
  });
});

describe('VisReportDossier (Spec §6.2/§9.17, B-103/B-104 «Papier ist Papier»)', () => {
  it('zeigt die drei Ansichten-Kacheln + eine ehrliche Governance-Box aus echten Zählern', () => {
    useVisRuntime.getState().setzeLauf('n1', { status: 'fertig', memoKey: 'k' });
    useVisRuntime.getState().setzeLauf('n2', { status: 'fehler', memoKey: 'k' });
    act(() => root.render(<VisReportDossier onClose={() => {}} />));
    expect(container.querySelectorAll('[data-testid^="vis-report-kachel-"]')).toHaveLength(3);
    const governance = container.querySelector('[data-testid="vis-report-governance"]')?.textContent ?? '';
    expect(governance).toContain('1 fertig');
    expect(governance).toContain('1 Fehler');
  });

  it('Schliessen ruft onClose auf', () => {
    let geschlossen = false;
    act(() => root.render(<VisReportDossier onClose={() => (geschlossen = true)} />));
    const knopf = container.querySelector('[data-testid="vis-report-schliessen"]') as HTMLButtonElement;
    act(() => knopf.click());
    expect(geschlossen).toBe(true);
  });

  /**
   * P-RAND (v0.9.29, `docs/V0929-SPEZ.md` §1 «Dazu Sonde 1») — der Grund,
   * warum Sonde 1 in KosmoVis in die 300s-Zeitüberschreitung lief: dieser
   * Bogen blieb nach dem Sofort-Werkzeug «Report» offen und fing als
   * ganzflächiger Scrim jeden weiteren Zeiger ab («vis-report-dossier-scrim
   * intercepts pointer events»). Escape — das der Sondenlauf nach JEDEM
   * Werkzeug drückt — tat nichts. Seit v0.8.4 E3 ist `useOverlaySchliessen`
   * das eine Overlay-Gesetz der App; dieser Fall fehlte darin.
   */
  it('Escape schliesst den Bogen ebenfalls (Overlay-Gesetz E3)', () => {
    let geschlossen = false;
    act(() => root.render(<VisReportDossier onClose={() => (geschlossen = true)} />));
    expect(container.querySelector('[data-testid="vis-report-dossier-scrim"]')).not.toBeNull();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(geschlossen).toBe(true);
  });
});
