// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { useClaudeAnschluss } from '../../kosmo-orbit/src/state/claude-anschluss';
import { VisboxClaude } from '../src/kopf';

/**
 * E131/E134 (A0155): Die Pille «N offen» pulst, solange ein Vorschlag offen liegt, und hört auf, sobald alle
 * entschieden sind. Bei reduzierter Bewegung steht ein stiller Ring. jsdom wertet `@media` nicht aus; die berechnete
 * Animation misst der Lauf im echten Browser (Meldung A0155), hier steht die Regel selbst unter Probe.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

type Vorschlag = ReturnType<typeof useClaudeAnschluss.getState>['vorschlaege'][number];
const vorschlag = (kennung: string): Vorschlag => ({ kennung, commandId: 'vis.nodeSetzen', params: {}, zusammenfassung: 'Probe' });
const pille = () => document.querySelector<HTMLElement>('[data-testid="claude-karten-zaehler"]');
const setze = (vorschlaege: Vorschlag[]) => act(() => useClaudeAnschluss.setState({ vorschlaege }));

let root: Root | null = null;
let halter: HTMLDivElement | null = null;

beforeEach(() => {
  useClaudeAnschluss.setState({ verbunden: true, vorschlaege: [], internet: false, zuletztAktiv: null });
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() => root!.render(<VisboxClaude />));
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  halter?.remove();
  halter = null;
  useClaudeAnschluss.setState({ verbunden: false, vorschlaege: [] });
});

describe('A0155 · Puls an der Pille «N offen»', () => {
  it('N = 0: keine Pille, kein Merkmal', () => {
    expect(pille()).toBeNull();
    expect(document.querySelector('[data-puls]')).toBeNull();
  });

  it('N ≥ 1: die Pille trägt das Merkmal, auch wenn N wächst', () => {
    setze([vorschlag('a')]);
    expect(pille()?.dataset['puls']).toBe('an');
    setze([vorschlag('a'), vorschlag('b')]);
    expect(pille()?.dataset['puls']).toBe('an');
    expect(pille()?.textContent).toContain('2 offen');
  });

  it('zugeklappt und aufgeklappt: der Puls bleibt, solange etwas offen liegt', () => {
    setze([vorschlag('a')]);
    const vorher = pille()!.getAttribute('aria-expanded');
    act(() => pille()!.click());
    expect(pille()!.getAttribute('aria-expanded')).not.toBe(vorher);
    expect(pille()?.dataset['puls']).toBe('an');
  });

  it('alle entschieden: der Puls hört auf, ein neuer Vorschlag startet ihn wieder', () => {
    setze([vorschlag('a')]);
    setze([]);
    expect(document.querySelector('[data-puls]')).toBeNull();
    setze([vorschlag('b')]);
    expect(pille()?.dataset['puls']).toBe('an');
  });

  it('nach einer Trennung trägt die neu gezeichnete Pille das Merkmal wieder', () => {
    setze([vorschlag('a')]);
    act(() => useClaudeAnschluss.setState({ verbunden: false }));
    act(() => useClaudeAnschluss.setState({ verbunden: true }));
    expect(pille()?.dataset['puls']).toBe('an');
  });

  it('kein Band: der Vorschlag erzeugt ausser der Pille kein neues Merkmal', () => {
    setze([vorschlag('a')]);
    expect(document.querySelectorAll('[data-puls]')).toHaveLength(1);
  });

  describe('Regeln in visbox.css', () => {
    const css = readFileSync(resolve(__dirname, '../src/visbox.css'), 'utf-8');
    const auswahl = ".claude-anschluss .claude-anschluss-zaehler[data-puls='an']";

    it('der Puls ändert die Grösse nicht', () => {
      const bloecke = css.match(/@keyframes visbox-pille-puls \{[\s\S]*?\n\}/);
      expect(bloecke?.[0]).toBeTruthy();
      expect(bloecke?.[0]).not.toMatch(/transform|scale/);
      expect(css).toContain(`${auswahl} {\n  border-color: var(--k-accent);\n  animation: visbox-pille-puls`);
    });

    it('reduzierte Bewegung und Bewegungs-Schalter: keine Animation, stiller Ring', () => {
      const reduziert = css.slice(css.indexOf('@media (prefers-reduced-motion: reduce) {', css.indexOf('visbox-pille-puls')));
      expect(reduziert).toContain(auswahl);
      expect(reduziert).toMatch(/animation: none;\s+box-shadow: 0 0 0 1px var\(--k-accent\);/);
      expect(css).toContain(`:root[data-bewegung='aus'] ${auswahl}`);
      expect(css).toContain(`:root[data-bewegung='ruhig'] ${auswahl}`);
    });
  });
});
