// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import { bestaetigen, KBestaetigung, KMeldungen, melde } from '../src/meldungen';

// Gleiches Muster wie `komponenten.test.tsx`: ohne dieses Flag warnt React
// bei jedem `act()` in dieser jsdom-Umgebung.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * v0.8.0B / P2 (Spez §3) — KSelect/KDialog/KMenu/Meldungen: Glass-/
 * Flächenstufen-Optik, Verhalten (testids/aria/Fokusfalle/ESC) unverändert.
 * Muster wie `popup-layout.test.tsx`: aura.css-Textproben für die reine
 * CSS-Deklarationsebene + DOM-Proben für den unveränderten Verhaltens-
 * Vertrag.
 */

const auraCss = readFileSync(path.resolve(__dirname, '../src/aura.css'), 'utf8');

describe('aura.css: Glass-Fallback-Ketten (Papier bleibt deckend, Orbit bekommt Glass)', () => {
  it('.k-menu / .k-dialog-box nutzen --k-glass-fill mit --k-raised-Fallback', () => {
    expect(auraCss).toMatch(/\.k-menu\s*{[^}]*background:\s*var\(--k-glass-fill,\s*var\(--k-raised\)\)/);
    expect(auraCss).toMatch(/\.k-dialog-box\s*{[^}]*background:\s*var\(--k-glass-fill,\s*var\(--k-raised\)\)/);
  });

  it('.k-select steht auf --k-sunken (Fallback --k-field), radius-md', () => {
    expect(auraCss).toMatch(/\.k-select\s*{[^}]*background-color:\s*var\(--k-sunken,\s*var\(--k-field\)\)/);
    expect(auraCss).toMatch(/\.k-select\s*{[^}]*border-radius:\s*var\(--k-radius-md\)/);
  });

  it('.k-meldung-karte + .k-dialog-box tragen Glow-/Glass-Fallbacks statt roher Hex-Werte', () => {
    expect(auraCss).toMatch(/\.k-meldung-karte\s*{[^}]*background:\s*var\(--k-glass-fill,\s*var\(--k-raised\)\)/);
  });
});

describe('aura.css: Approval-Klassensatz (Spez §3 B-46/B-99) — reine Klassen, keine Datei-Kopplung', () => {
  it('enthält .k-approval + Risiko-Pill + Meta-Grid + Aktionen-Zeile', () => {
    expect(auraCss).toContain('.k-approval {');
    expect(auraCss).toContain('.k-approval-risiko');
    expect(auraCss).toContain('.k-approval-meta');
    expect(auraCss).toContain('.k-approval-aktionen');
  });

  it('Risiko-Pill nutzt eine vom Konsumenten gesetzte --_risiko-Variable mit Warn-Fallback', () => {
    expect(auraCss).toMatch(/\.k-approval-risiko\s*{[^}]*color:\s*var\(--_risiko,\s*var\(--k-warning\)\)/);
  });
});

describe('KMeldungen: testids/aria-live bleiben, Optik wandert in CSS-Klassen', () => {
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

  it('rendert data-testid="meldung-{ton}" + aria-live="polite", keine Inline-Farbwerte mehr', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      melde('Alles gespeichert', { ton: 'erfolg' });
    });
    act(() => {
      root!.render(<KMeldungen />);
    });

    const host = container.querySelector('[aria-live="polite"]') as HTMLElement;
    expect(host).not.toBeNull();
    expect(host.className).toContain('k-meldungen-host');

    const karte = container.querySelector('[data-testid="meldung-erfolg"]') as HTMLElement;
    expect(karte).not.toBeNull();
    expect(karte.className).toContain('k-meldung-karte');
    expect(karte.getAttribute('style')).not.toMatch(/background:\s*#/i);
  });
});

describe('KBestaetigung: testids/role/Esc-Vertrag bleiben, Box nutzt Glass-Karten-Rezept', () => {
  // E-K5 (`docs/V0812-SPEZ.md`, Sanktion 4, 21.07.2026, Bauagenten-Fund):
  // `KBestaetigung` portalt seit E-K5 nach `document.body` (derselbe Weg wie
  // `Einstellungen.tsx` — sonst bleibt der Dialog im `#root`-Stacking-
  // Context gefangen und ein aufrufendes Panel mit höherem `z-index` legt
  // sich klickbar darüber, s. `meldungen.tsx`s Kopfkommentar an
  // `KBestaetigung`). `renderToStaticMarkup` (reines SSR, kein echtes DOM)
  // rendert `createPortal`-Inhalte NICHT — hier darum dasselbe
  // `createRoot`+`document.body`-Muster wie der `KMeldungen`-Test oben.
  let container: HTMLDivElement | null = null;
  let root: Root | null = null;

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

  it('rendert role=dialog + bestaetigung-ja/-nein, Box trägt k-dialog-box statt k-karte', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      void bestaetigen({ titel: 'Wirklich löschen?', bestaetigen: 'Löschen', gefaehrlich: true });
    });
    act(() => {
      root!.render(<KBestaetigung />);
    });

    // Portal nach `document.body` — die Bestätigung lebt darum NICHT im
    // `container`, sondern direkt an `document.body`.
    const dialog = document.body.querySelector('[data-testid="bestaetigung"]') as HTMLElement;
    expect(dialog).not.toBeNull();
    expect(dialog.getAttribute('role')).toBe('dialog');
    expect(dialog.querySelector('[data-testid="bestaetigung-ja"]')).not.toBeNull();
    expect(dialog.querySelector('[data-testid="bestaetigung-nein"]')).not.toBeNull();
    expect(dialog.className).toContain('k-dialog-scrim');
    const box = dialog.querySelector('.k-dialog-box') as HTMLElement;
    expect(box).not.toBeNull();
    expect(box.className).toContain('k-bestaetigung-box');
  });
});
