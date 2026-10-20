import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * Fehler-Nachgang 20.10.2026 (Owner am Mac: «Textfelder mit Farbumrandung»). Der Fokusring des Hauses
 * (`packages/kosmo-ui/src/aura.css`, `:focus-visible`: Umriss mit Abstand plus Innenring als
 * `box-shadow … !important`) zeichnet AUSSERHALB des Feldes; der Knotenkoerper schneidet ab
 * (`.vis-node-koerper { overflow: hidden }`), und von dem Ring blieben die runden Ecken oben und unten
 * am Stil-Text des Prompt-Knotens stehen. Im Knotenkoerper traegt ein Feld den Fokus darum in seinem
 * eigenen Rand. Geprueft an den Regeln selbst (die gemessene Probe am Bild steht in
 * `e2e/kv-fehler.spec.ts`).
 */
const HIER = path.dirname(fileURLToPath(import.meta.url));
const VIS = readFileSync(path.resolve(HIER, '../src/modules/vis/vis-visual.css'), 'utf8');
const AURA = readFileSync(path.resolve(HIER, '../../../packages/kosmo-ui/src/aura.css'), 'utf8');

function block(css: string, kopf: string): string {
  const start = css.indexOf(`\n${kopf} {`);
  expect(start, `Regel «${kopf}» fehlt`).toBeGreaterThanOrEqual(0);
  const auf = css.indexOf('{', start);
  return css.slice(auf + 1, css.indexOf('}', auf));
}

describe('kv-fehler — kein abgeschnittener Fokusring in Knotenkoerpern', () => {
  it('der Ring des Hauses steht unveraendert und zeichnet ausserhalb (Anlass)', () => {
    const ring = block(AURA, ':focus-visible');
    expect(ring).toMatch(/outline-offset:\s*var\(--k-fokusring-versatz\)/);
    expect(ring).toMatch(/box-shadow:[^;]*!important/);
    expect(block(VIS, '.vis-node-koerper')).toContain('overflow: hidden;');
  });

  it('Eingaben, Auswahlen und Textfelder im Koerper: kein Umriss, kein Ring, Akzent im eigenen Rand', () => {
    const kopf = [
      '.vis-node-koerper input:focus-visible,',
      '.vis-node-koerper select:focus-visible,',
      '.vis-node-koerper textarea:focus-visible',
    ].join('\n');
    const r = block(VIS, kopf);
    expect(r).toContain('outline: none;');
    // `!important` noetig, weil der Ring es traegt; die hoehere Spezifitaet (0,2,1 gegen 0,1,0) gewinnt.
    expect(r).toContain('box-shadow: none !important;');
    expect(r).toContain('border-color: var(--k-accent);');
  });

  it('Kaestchen und Schiene behalten einen Umriss, aber ohne Abstand nach aussen', () => {
    const kopf = [
      ".vis-node-koerper input[type='checkbox']:focus-visible,",
      ".vis-node-koerper input[type='radio']:focus-visible,",
      ".vis-node-koerper input[type='range']:focus-visible",
    ].join('\n');
    const r = block(VIS, kopf);
    expect(r).toContain('outline: var(--k-fokusring-breite) solid var(--k-fokusring-aussen);');
    expect(r).toContain('outline-offset: 0;');
  });

  it('das Textfeld des Prompt-Knotens hat einen Rand, der den Fokus tragen kann', () => {
    const feld = block(VIS, '.vis-node-feld');
    expect(feld).toMatch(/border:\s*1px solid/);
  });
});
