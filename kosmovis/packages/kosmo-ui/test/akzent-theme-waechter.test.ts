// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

/**
 * P-AKZENTTREU (docs/UI-2026-08-27-VERFASSUNG-NACHGEZOGEN.md §3.1, KosmoOrbit-
 * UI-Worker, 27.08.2026) — Befund: unter `data-theme='orbit'` (dem
 * Standardthema, `App.tsx:238`) ergeben die fünf Akzente NUR 1 von 5
 * verschiedenen `--k-accent`-Farben (alle fallen auf orbit's eigenen Wert
 * `#57b6c2` zurück), unter `data-theme='paper'` liefern sie korrekt 5 von 5.
 * Ursache: `[data-theme='orbit']` (aura.css, EIN Block) setzt `--k-accent`
 * bei GLEICHER Spezifität NACH den vier `[data-akzent='…']`-Blöcken — bei
 * gleicher Spezifität gewinnt in der Kaskade die später stehende Regel, ganz
 * unabhängig vom Attributnamen. `[data-theme='paper']` steht dagegen VOR den
 * Akzent-Blöcken, darum wirkt die Wahl dort schon heute.
 *
 * GEWÄHLTER MESSWEG (statt eines eigenen Spezifitäts-Nachbaus): die
 * `// @vitest-environment jsdom`-Pragma (schon von `css-var.test.ts` in
 * diesem Paket für CSS-Var-Lesen genutzt) gibt ein echtes jsdom-`document`
 * vor. Hier wird `aura.css` zusätzlich als echtes `<style>`-Blatt in dieses
 * Dokument eingehängt, statt (wie `css-var.test.ts`) Werte nur per
 * Inline-Style zu setzen — dadurch beantwortet jsdoms EIGENE CSS-Kaskaden-
 * Engine (nicht meine) `getComputedStyle`, exakt der Mechanismus, den ein
 * echter Browser für Custom Properties + Attributselektoren mit gleicher
 * Spezifität anwendet (Quellreihenfolge entscheidet). Kein Playwright/
 * Browser nötig (Auftragslage verbietet ihn ausdrücklich) — ein eigener
 * Regex-Spezifitäts-Rechner wäre nur eine zweite, weniger vertrauenswürdige
 * Implementation genau der Logik, die hier geprüft werden soll.
 */

const auraPath = path.resolve(__dirname, '../src/aura.css');
const auraCss = readFileSync(auraPath, 'utf8');

const AKZENTE = ['tusche', 'kupfer', 'signal', 'blau', 'gruen'] as const;

let styleEl: HTMLStyleElement;

beforeAll(() => {
  styleEl = document.createElement('style');
  styleEl.textContent = auraCss;
  document.head.appendChild(styleEl);
});

afterAll(() => {
  styleEl.remove();
  document.documentElement.removeAttribute('data-theme');
  document.documentElement.removeAttribute('data-akzent');
});

/** Setzt Thema + Akzent auf dem echten `<html>`-Wurzelelement des jsdom-
 * Dokuments und liest `--k-accent` per `getComputedStyle` zurück — derselbe
 * Weg wie `App.tsx` (`document.documentElement.dataset.theme/.akzent`). */
function gemessenerAccent(theme: 'paper' | 'orbit', akzent: (typeof AKZENTE)[number]): string {
  const root = document.documentElement;
  root.setAttribute('data-theme', theme);
  if (akzent === 'tusche') {
    root.removeAttribute('data-akzent'); // 'tusche' hat keinen [data-akzent]-Block (akzente.ts: farbe: null)
  } else {
    root.setAttribute('data-akzent', akzent);
  }
  return getComputedStyle(root).getPropertyValue('--k-accent').trim();
}

describe('P-AKZENTTREU: Akzentwahl muss in JEDEM Thema wirken', () => {
  it('Papier: fünf Akzente ergeben fünf verschiedene --k-accent-Werte', () => {
    const werte = AKZENTE.map((a) => gemessenerAccent('paper', a));
    expect(new Set(werte).size, `paper-Werte: ${JSON.stringify(werte)}`).toBe(5);
  });

  it('Kosmos (orbit, das Standardthema App.tsx:238): fünf Akzente ergeben fünf verschiedene --k-accent-Werte', () => {
    const werte = AKZENTE.map((a) => gemessenerAccent('orbit', a));
    expect(new Set(werte).size, `orbit-Werte: ${JSON.stringify(werte)}`).toBe(5);
  });

  it('jeder Akzent liefert unter orbit denselben Hexwert, den er unter paper NICHT hat (kupfer/signal/blau/gruen sind theme-übergreifend EINE Werte-Reihe, v0.7.3 D7)', () => {
    for (const a of ['kupfer', 'signal', 'blau', 'gruen'] as const) {
      const paperWert = gemessenerAccent('paper', a);
      const orbitWert = gemessenerAccent('orbit', a);
      expect(orbitWert, `--k-accent unter orbit für Akzent "${a}" muss dessen [data-akzent='${a}']-Wert (${paperWert}) sein, nicht orbit's Theme-Default`).toBe(
        paperWert,
      );
    }
  });

  it('Vorwahl-Akzent «tusche» behält seinen bisherigen, per-Thema unterschiedlichen Wert (paper #3e96a2, orbit #57b6c2)', () => {
    expect(gemessenerAccent('paper', 'tusche')).toBe('#3e96a2');
    expect(gemessenerAccent('orbit', 'tusche')).toBe('#57b6c2');
  });
});
