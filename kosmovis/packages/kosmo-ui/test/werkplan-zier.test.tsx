// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { Messrahmen, Passermarke } from '../src/components';

/**
 * D-7 «Werkplan-Zierde» (docs/design/UNTERAUFTRAG-D7-WERKPLANZIER.md,
 * Kanon E-4/E-5/E-6 in GESTALTUNGS-ENTSCHEIDE-2026-08-10.md) — Vertrag der drei
 * neuen Bausteine:
 *
 *  · E-4: Tuschelinien-Reparatur an `.k-karte` + `.k-karteikarte`-Anatomie
 *    (CSS-Wächter gegen aura.css — kein neues Token, alles aus Bestand).
 *  · E-5: `Passermarke` als Inline-SVG (nie Text-Glyph U+2316), nur die
 *    zwei sanktionierten Grössen, Farbe über `.k-passermarke`, druckfest.
 *  · E-6: die Zier-Masskette existiert AUSSCHLIESSLICH im Messrahmen und
 *    unter der Wahrheitsregel — die gerenderte Zahl ist das reale Mass der
 *    gestrichelten Rahmenlinie, die Masslinie spannt exakt diese Strecke.
 *
 * Muster `komponenten.test.tsx`: `renderToStaticMarkup` reicht — reine
 * Struktur-Checks, keine Interaktion.
 */

const auraCss = readFileSync(path.resolve(__dirname, '../src/aura.css'), 'utf8');

/** CSS-Block zu einem Selektor (Muster `token-spiegel.test.ts`). */
function block(selectorNeedle: string): string {
  const start = auraCss.indexOf(selectorNeedle);
  expect(start, `Selektor "${selectorNeedle}" fehlt in aura.css`).toBeGreaterThan(-1);
  const open = auraCss.indexOf('{', start);
  const close = auraCss.indexOf('}', open);
  return auraCss.slice(open, close + 1);
}

describe('Passermarke (E-5) — Inline-SVG, nie Text-Glyph', () => {
  it('12×12 (Listenkopf): Kreis r3.5 + Fadenkreuz, Strichstärke 1, currentColor, aria-hidden', () => {
    const html = renderToStaticMarkup(<Passermarke />);
    expect(html).toContain('class="k-passermarke"');
    expect(html).toContain('width="12"');
    expect(html).toContain('viewBox="0 0 12 12"');
    expect(html).toContain('r="3.5"');
    expect(html).toContain('stroke="currentColor"');
    expect(html).toContain('stroke-width="1"');
    expect(html).toContain('d="M6 .5V11.5M.5 6H11.5"');
    expect(html).toContain('aria-hidden="true"');
    // NIE der Text-Glyph — der Font-Fallback wäre je Gerät anders (E-5).
    expect(html).not.toContain('⌖');
    expect(html).toContain('fill="none"');
  });

  it('16×16 (Messrahmen): dieselbe Zeichnung, massstäblich mit Strichstärke 1', () => {
    const html = renderToStaticMarkup(<Passermarke size={16} />);
    expect(html).toContain('width="16"');
    expect(html).toContain('viewBox="0 0 16 16"');
    expect(html).toContain('r="5.5"');
    expect(html).toContain('d="M8 .5V15.5M.5 8H15.5"');
  });

  it('CSS-Vertrag: .k-passermarke trägt --k-ink-faint und verschwindet im Druck', () => {
    expect(block('.k-passermarke {')).toContain('color: var(--k-ink-faint)');
    const printStart = auraCss.indexOf('@media print');
    expect(printStart, '@media print-Block fehlt in aura.css').toBeGreaterThan(-1);
    const printBlock = auraCss.slice(printStart, auraCss.indexOf('}', auraCss.indexOf('display: none', printStart)) + 1);
    expect(printBlock).toContain('.k-passermarke');
    expect(printBlock).toContain('.k-masskette');
    expect(printBlock).toContain('display: none');
  });
});

describe('Messrahmen-Masskette (E-6) — die Wahrheitsregel', () => {
  it('height=220: die Zahl ist das reale Mass der Rahmenlinie (220 − 2·10 = 200 px), die Masslinie spannt exakt diese Strecke', () => {
    const html = renderToStaticMarkup(<Messrahmen height={220} caption="leer" />);
    // Der gezeichnete Rahmen liegt bei inset 10 …
    expect(html).toContain('inset:10px');
    // … die Beschriftung behauptet exakt das daraus messbare Mass …
    expect(html).toContain(`${220 - 2 * 10} px`);
    // … und die Masslinie läuft von Rahmen-Oberkante zu Rahmen-Unterkante.
    expect(html).toContain('M8 10V210');
    // Ton: --k-ink-faint über .k-masskette, Beschriftung in .k-label-Stimme.
    expect(html).toContain('k-masskette');
    expect(html).toContain('k-label k-masskette');
  });

  it('height=180 (zweite Stichprobe): 160 px — die Zahl folgt der Grösse, kein fixer Platzhalter', () => {
    const html = renderToStaticMarkup(<Messrahmen height={180} caption="leer" />);
    expect(html).toContain('160 px');
    expect(html).toContain('M8 10V170');
    expect(html).not.toContain('200 px');
  });

  it('nicht-numerische Höhe ("100%"): KEINE Masskette — eine geschätzte Zahl wäre erfunden, erfundene Masse sind verboten', () => {
    const html = renderToStaticMarkup(<Messrahmen height="100%" caption="leer" />);
    expect(html).not.toContain('k-masskette');
    expect(html).not.toContain('k-passermarke');
  });

  it('Klein-Instanzen (< 160px, z. B. Vorschau-Kacheln): keine Zierde — Mass-Regel statt Zier-Wiederholung', () => {
    const html = renderToStaticMarkup(<Messrahmen height={120} caption="Vorschau" />);
    expect(html).not.toContain('k-masskette');
    expect(html).not.toContain('k-passermarke');
  });

  it('max-2-Regel (E-5): der Messrahmen trägt genau EINE Passermarke (16×16) — der zweite diagonale Platz bleibt frei', () => {
    const html = renderToStaticMarkup(<Messrahmen height={220} caption="leer" />);
    const marken = html.match(/data-testid="k-passermarke"/g) ?? [];
    expect(marken.length).toBe(1);
    expect(html).toContain('width="16"');
  });
});

describe('Karteikarte (E-4) — CSS-Anatomie in aura.css, alles aus Bestands-Tokens', () => {
  it('Tuschelinien-Reparatur: .k-karte::before liegt 45°-rotiert auf der Schnittkante (17×2px, --k-technik)', () => {
    const b = block('.k-karte::before');
    expect(b).toContain('width: 17px');
    expect(b).toContain('height: 2px');
    expect(b).toContain('transform: rotate(45deg)');
    expect(b).toContain('background: var(--k-technik)');
    expect(b).toContain('pointer-events: none');
    // Träger braucht position: relative (Kollisionsregel: ::after gehört
    // dem Akzent-Eckpunkt — darum ::before).
    expect(block('.k-karte {')).toContain('position: relative');
  });

  it('.k-karteikarte: 32px-Nummernspalte (--k-s7) + Inhalt', () => {
    expect(block('.k-karteikarte {')).toContain('grid-template-columns: var(--k-s7) minmax(0, 1fr)');
    const nr = block('.k-karteikarte-nr');
    expect(nr).toContain('font-family: var(--k-font-mono)');
    expect(nr).toContain('color: var(--k-ink-faint)');
    expect(nr).toContain('border-right: 1px solid var(--k-line)');
  });

  it('Titel bleibt gemischt geschrieben (kein uppercase — VERSAL gilt Labels, nicht Inhalt); Unterzeile in UI-Schrift', () => {
    const titel = block('.k-karteikarte-titel');
    expect(titel).not.toContain('uppercase');
    expect(titel).toContain('font-size: var(--k-t-sm)');
    const unterzeile = block('.k-karteikarte-unterzeile');
    expect(unterzeile).toContain('font-family: var(--k-font-ui)');
    expect(unterzeile).toContain('color: var(--k-ink-soft)');
  });

  it('Auswahl = 1.5px---k-ink-Rahmen, nie .k-akzent-eckpunkt (::after/Clip-Kollision)', () => {
    const b = block('.k-karteikarte--gewaehlt');
    expect(b).toContain('border: 1.5px solid var(--k-ink)');
    expect(b).not.toContain('akzent-eckpunkt');
  });
});
